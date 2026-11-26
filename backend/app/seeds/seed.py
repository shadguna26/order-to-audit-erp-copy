import os
import sys
from decimal import Decimal
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.business import Business, BusinessType
from app.models.auth import User, UserRole
from app.models.master import (
    MaterialType,
    BaseUnitType,
    RawMaterial,
    Product,
    BOM,
    BOMItem,
    Customer,
    PriceList,
    Supplier
)
from app.models.stock import (
    StockItemType,
    StockLocationType,
    StockDirection,
    StockDocType,
    StockLedger
)
def seed_database(db: Session):
    print("=== Starting Seed: Sri Lakshmi Snacks (Tiruchirappalli) ===")

    # Ensure tables exist on the current database bind
    bind_engine = db.get_bind()
    Base.metadata.create_all(bind=bind_engine)

    # 0. BUSINESS #1 (Sri Lakshmi Snacks)
    biz = db.query(Business).filter(Business.id == 1).first()
    if not biz:
        biz = Business(
            id=1,
            name="Sri Lakshmi Snacks",
            business_type=BusinessType.MANUFACTURER,
            gstin="33AAAAA0000A1Z5",
            state="Tamil Nadu",
            state_code="33",
            address="Plot 42, SIDCO Industrial Estate, Thuvakudi, Tiruchirappalli",
            pincode="620015",
            phone="+91-431-2501234",
            email="accounts@srilakshmisnacks.in",
            invoice_prefix="TN",
            variance_tolerance_pct=Decimal("3.00"),
            is_active=True,
        )
        db.add(biz)
        db.flush()

    # 1. USERS & ROLES (Mobile + OTP, one dummy user per role + second salesman for benchmark)
    # Non-negotiable: salesman, admin, production, accountant (read-only), owner
    users_data = [
        ("owner", "+919000000001", "P. Shanmugam (Owner)", UserRole.OWNER),
        ("admin", "+919000000002", "K. Ramanathan (Factory Admin)", UserRole.ADMIN),
        ("salesman_a", "+919000000003", "S. Murugan (Salesman TN - Tiruchi & Madurai)", UserRole.SALESMAN),
        ("salesman_b", "+919000000004", "M. Venkatesh (Salesman Outstation)", UserRole.SALESMAN),
        ("production", "+919000000005", "T. Palanivel (Production Incharge)", UserRole.PRODUCTION),
        ("accountant", "+919000000006", "G. Sundaram (Auditor & Accountant)", UserRole.ACCOUNTANT),
    ]

    users_map = {}
    for key, mobile, full_name, role in users_data:
        existing = db.query(User).filter(User.mobile == mobile).first()
        if not existing:
            user = User(
                mobile=mobile,
                full_name=full_name,
                role=role,
                is_active=True
            )
            db.add(user)
            db.flush()
            users_map[key] = user
            print(f"Created User: {mobile} [{role.value}]")
        else:
            users_map[key] = existing

    admin_user = users_map["admin"]

    # 2. RAW MATERIALS & PACKAGING
    # Benchmark:
    # flour (kg -> base g)
    # oil (L -> base ml)
    # spice mix (kg -> base g)
    # 200g pouch (piece)
    # carton (piece, holds 20 packets)
    materials_data = [
        ("RM-FLOUR", "Raw Rice Flour / Arisi Maavu", MaterialType.RAW, BaseUnitType.G, Decimal("50000.0")), # 50 kg reorder
        ("RM-OIL", "Refined Sunflower Oil", MaterialType.RAW, BaseUnitType.ML, Decimal("20000.0")),         # 20 L reorder
        ("RM-SPICE", "Salt & Chilli Spice Blend", MaterialType.RAW, BaseUnitType.G, Decimal("5000.0")),    # 5 kg reorder
        ("PKG-POUCH-200G", "Printed Laminated Pouch 200g", MaterialType.PACKAGING, BaseUnitType.PIECE, Decimal("200.0")),
        ("PKG-CARTON-20", "Corrugated Carton (20 pkts)", MaterialType.PACKAGING, BaseUnitType.PIECE, Decimal("20.0")),
    ]

    materials_map = {}
    for code, name, mat_type, base_unit, reorder in materials_data:
        rm = db.query(RawMaterial).filter(RawMaterial.code == code).first()
        if not rm:
            rm = RawMaterial(
                code=code,
                name=name,
                type=mat_type,
                base_unit=base_unit,
                reorder_level_base=reorder
            )
            db.add(rm)
            db.flush()
            print(f"Created Material: {code} ({base_unit.value})")
        materials_map[code] = rm

    # 3. PRODUCTS
    # Benchmark: Murukku 200 g (Selling price Rs 50 + 5% GST)
    products_data = [
        ("FG-MRK-200G", "Kai Murukku 200g", "21069099", Decimal("5.00"), Decimal("200.00"), BaseUnitType.PIECE),
        ("FG-MIX-200G", "Madras Mixture 200g", "21069099", Decimal("5.00"), Decimal("200.00"), BaseUnitType.PIECE),
    ]

    products_map = {}
    for code, name, hsn, gst_rate, pack_size, base_unit in products_data:
        prod = db.query(Product).filter(Product.code == code).first()
        if not prod:
            prod = Product(
                code=code,
                name=name,
                hsn_code=hsn,
                gst_rate_pct=gst_rate,
                pack_size_g=pack_size,
                base_unit=base_unit
            )
            db.add(prod)
            db.flush()
            print(f"Created Product: {code}")
        products_map[code] = prod

    # 4. PRICE LIST
    # Rs 50 selling price = 5000 paise for Retailers, Rs 45 = 4500 paise for Distributors
    murukku = products_map["FG-MRK-200G"]
    prices = [
        (murukku.id, "retailer", 5000),      # Rs 50.00
        (murukku.id, "distributor", 4500),   # Rs 45.00
    ]
    for prod_id, cust_type, price_paise in prices:
        pl = db.query(PriceList).filter(PriceList.product_id == prod_id, PriceList.customer_type == cust_type).first()
        if not pl:
            pl = PriceList(product_id=prod_id, customer_type=cust_type, price_paise=price_paise)
            db.add(pl)

    # 5. BILL OF MATERIALS (BOM)
    # Benchmark:
    # 1 batch = 200 packets:
    # flour 40 kg (40,000 g), oil 10 L (10,000 ml), salt+spice mix 1.2 kg (1,200 g),
    # 200 g pouch 200 pcs, carton 10 pcs (each carton holds 20 packets)
    bom = db.query(BOM).filter(BOM.product_id == murukku.id).first()
    if not bom:
        bom = BOM(
            product_id=murukku.id,
            name="Standard Batch - Kai Murukku 200g (200 pkts)",
            batch_size_packets=200,
            expected_yield_packets=200,
            tolerance_pct=Decimal("3.00")
        )
        db.add(bom)
        db.flush()

        bom_items_data = [
            (materials_map["RM-FLOUR"].id, Decimal("40000.0"), BaseUnitType.G),     # 40 kg
            (materials_map["RM-OIL"].id, Decimal("10000.0"), BaseUnitType.ML),       # 10 L
            (materials_map["RM-SPICE"].id, Decimal("1200.0"), BaseUnitType.G),       # 1.2 kg
            (materials_map["PKG-POUCH-200G"].id, Decimal("200.0"), BaseUnitType.PIECE), # 200 pouches
            (materials_map["PKG-CARTON-20"].id, Decimal("10.0"), BaseUnitType.PIECE),   # 10 cartons
        ]
        for mat_id, std_qty, b_unit in bom_items_data:
            item = BOMItem(
                bom_id=bom.id,
                raw_material_id=mat_id,
                standard_qty_base=std_qty,
                base_unit=b_unit
            )
            db.add(item)
        print("Created BOM for Kai Murukku 200g")

    # 6. SUPPLIERS
    suppliers_data = [
        ("Annapoorna Agro Mills", "33AAACA1234A1Z1", "Tamil Nadu", "33", "+91 94432 22001", "Gandhi Market, Tiruchirappalli, TN"),
        ("Cauvery Packaging Ltd", "33AAACC5678B1Z2", "Tamil Nadu", "33", "+91 94432 22002", "Thuvakudi Industrial Estate, Tiruchirappalli, TN"),
    ]
    for s_name, s_gstin, s_state, s_code, s_phone, s_addr in suppliers_data:
        sup = db.query(Supplier).filter(Supplier.name == s_name).first()
        if not sup:
            sup = Supplier(
                name=s_name,
                gstin=s_gstin,
                state=s_state,
                state_code=s_code,
                phone=s_phone,
                address=s_addr
            )
            db.add(sup)

    # 7. CUSTOMERS
    # Benchmark:
    # Retailer A (Tamil Nadu, CGST+SGST)
    # Distributor B (Karnataka, IGST)
    customers_data = [
        ("Retailer A (Sri Balaji Provision Stores)", "33AAAAA1111A1Z1", "Tamil Nadu", "33", "Main Bazaar, Thillai Nagar, Tiruchirappalli", "+91 98424 55001", "retailer", 5000000),
        ("Distributor B (Cauvery Sweets & Snacks)", "29BBBBB2222B1Z2", "Karnataka", "29", "Avenue Road, Bengaluru, Karnataka", "+91 98450 66002", "distributor", 10000000),
        ("Retailer C (Murugan Maligai)", "33CCCC3333C1Z3", "Tamil Nadu", "33", "Madurai Road, Dindigul, Tamil Nadu", "+91 98421 77003", "retailer", 3000000),
    ]
    for c_name, c_gstin, c_state, c_code, c_addr, c_phone, c_type, credit_limit in customers_data:
        cust = db.query(Customer).filter(Customer.name == c_name).first()
        if not cust:
            cust = Customer(
                name=c_name,
                gstin=c_gstin,
                state=c_state,
                state_code=c_code,
                address=c_addr,
                phone=c_phone,
                customer_type=c_type,
                credit_limit_paise=credit_limit
            )
            db.add(cust)

    # 8. BENCHMARK OPENING STOCK IN STOCK LEDGER (Append-Only source of truth)
    # Rates: flour Rs 42 (opening), oil Rs 140/L, spice mix Rs 200/kg, pouch Rs 2.50, carton Rs 15
    # Opening stock:
    # flour 100 kg (100,000 g) @ Rs 42/kg = 4.2 paise/g
    # oil 30 L (30,000 ml) @ Rs 140/L = 14 paise/ml
    # spice mix 5 kg (5,000 g) @ Rs 200/kg = 20 paise/g
    # pouches 500 pcs @ Rs 2.50 = 250 paise/piece
    # cartons 30 pcs @ Rs 15 = 1500 paise/piece
    # finished Murukku 200 g = 50 packets @ cost Rs 35 = 3500 paise/packet
    opening_ledger_exists = db.query(StockLedger).filter(StockLedger.source_doc_type == StockDocType.OPENING_BALANCE).first()
    if not opening_ledger_exists:
        opening_entries = [
            (StockItemType.RAW_MATERIAL, materials_map["RM-FLOUR"].id, StockLocationType.RAW, Decimal("100000.0"), BaseUnitType.G, Decimal("4.2000")), # Rs 42/kg = 4.2 paise/g
            (StockItemType.RAW_MATERIAL, materials_map["RM-OIL"].id, StockLocationType.RAW, Decimal("30000.0"), BaseUnitType.ML, Decimal("14.0000")),   # Rs 140/L = 14 paise/ml
            (StockItemType.RAW_MATERIAL, materials_map["RM-SPICE"].id, StockLocationType.RAW, Decimal("5000.0"), BaseUnitType.G, Decimal("20.0000")),   # Rs 200/kg = 20 paise/g
            (StockItemType.RAW_MATERIAL, materials_map["PKG-POUCH-200G"].id, StockLocationType.PACKAGING, Decimal("500.0"), BaseUnitType.PIECE, Decimal("250.0000")), # Rs 2.50 = 250 paise
            (StockItemType.RAW_MATERIAL, materials_map["PKG-CARTON-20"].id, StockLocationType.PACKAGING, Decimal("30.0"), BaseUnitType.PIECE, Decimal("1500.0000")),  # Rs 15 = 1500 paise
            (StockItemType.FINISHED_GOODS, murukku.id, StockLocationType.FINISHED, Decimal("50.0"), BaseUnitType.PIECE, Decimal("3500.0000")), # 50 packets opening
        ]

        for item_type, item_id, loc_type, qty, unit, cost in opening_entries:
            ledger_row = StockLedger(
                item_type=item_type,
                item_id=item_id,
                location_type=loc_type,
                direction=StockDirection.IN,
                qty_base=qty,
                base_unit=unit,
                unit_cost_paise=cost,
                source_doc_type=StockDocType.OPENING_BALANCE,
                source_doc_id=0,
                batch_no="OPENING-2026",
                created_by=admin_user.id
            )
            db.add(ledger_row)
        print("Created Benchmark Opening Stock in append-only stock_ledger")

    db.commit()
    print("=== Database Seed Complete ===")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
