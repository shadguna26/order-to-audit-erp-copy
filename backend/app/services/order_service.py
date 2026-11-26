from datetime import datetime, timezone
import math
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.master import Product, Customer, PriceList, BOM
from app.models.stock import StockItemType, StockLocationType
from app.models.sales import Order, OrderItem, OrderStatus
from app.services.ledger_service import get_item_stock_balance
from app.services.sequence_service import generate_document_sequence
from app.services.gst_service import calculate_gst_breakdown

def check_order_stock_coverage(db: Session, product_id: int, requested_packets: int, business_id: int = 1) -> Dict[str, Any]:
    """
    NON-NEGOTIABLE BUSINESS LOGIC:
    Order stock check: show whether finished-goods stock covers each order line.
    On shortage, say e.g. 'Only 88 packets in stock. Short by 32.'
    and offer: dispatch available now + backorder, or suggest number of batches to produce.
    """
    avail_balance = get_item_stock_balance(
        db=db,
        item_type=StockItemType.FINISHED_GOODS,
        item_id=product_id,
        location_type=StockLocationType.FINISHED,
        business_id=business_id,
    )
    avail_packets = int(avail_balance)

    has_shortage = requested_packets > avail_packets
    shortage_packets = max(0, requested_packets - avail_packets)

    product = db.query(Product).filter(Product.id == product_id, Product.business_id == business_id).first()
    bom = db.query(BOM).filter(BOM.product_id == product_id, BOM.business_id == business_id).first()

    suggested_batches = 0
    shortage_message = None

    if has_shortage:
        shortage_message = f"Only {avail_packets} packets in stock. Short by {shortage_packets}."
        if bom and bom.expected_yield_packets > 0:
            suggested_batches = math.ceil(shortage_packets / bom.expected_yield_packets)

    return {
        "product_id": product_id,
        "product_name": product.name if product else "",
        "requested_packets": requested_packets,
        "available_packets": avail_packets,
        "has_shortage": has_shortage,
        "shortage_packets": shortage_packets,
        "shortage_message": shortage_message,
        "suggested_batches_to_produce": suggested_batches,
        "can_dispatch_available": avail_packets > 0
    }

def create_customer_order(
    db: Session,
    customer_id: int,
    salesman_id: int,
    items: List[Dict[str, Any]],
    notes: str = None,
    business_id: int = 1,
) -> Order:
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.business_id == business_id).first()
    if not customer:
        raise ValueError("Customer not found")

    business = db.query(Business).filter(Business.id == business_id).first()

    order_no = generate_document_sequence(
        db,
        model_class=Order,
        no_column=Order.order_no,
        prefix="SO",
        business_id=business_id,
    )

    order = Order(
        business_id=business_id,
        order_no=order_no,
        customer_id=customer_id,
        salesman_id=salesman_id,
        status=OrderStatus.SUBMITTED,
        notes=notes
    )
    db.add(order)
    db.flush()

    for item_data in items:
        p_id = item_data["product_id"]
        qty_pkts = int(item_data["quantity_packets"])

        product = db.query(Product).filter(Product.id == p_id, Product.business_id == business_id).first()
        if not product:
            raise ValueError(f"Product {p_id} not found")

        # Resolve effective-dated price from price_list or product default
        now_utc = datetime.now(timezone.utc)
        price_entry = (
            db.query(PriceList)
            .filter(
                PriceList.business_id == business_id,
                PriceList.product_id == p_id,
                PriceList.customer_type == customer.customer_type,
                PriceList.effective_from <= now_utc,
            )
            .order_by(PriceList.effective_from.desc(), PriceList.id.desc())
            .first()
        )

        unit_price = item_data.get("unit_price_paise")
        if unit_price is None:
            unit_price = price_entry.price_paise if price_entry else (product.selling_price_paise or 5000)

        subtotal_paise = qty_pkts * unit_price
        gst = calculate_gst_breakdown(
            subtotal_paise=subtotal_paise,
            gst_rate_pct=product.gst_rate_pct,
            customer_state_code=customer.state_code,
            customer_state=customer.state,
            company_state_code=business.state_code if business else None,
            company_state=business.state if business else None,
        )

        order_item = OrderItem(
            order_id=order.id,
            product_id=p_id,
            quantity_packets=qty_pkts,
            unit_price_paise=unit_price,
            tax_rate_pct=product.gst_rate_pct,
            subtotal_paise=subtotal_paise,
            cgst_paise=gst["cgst_paise"],
            sgst_paise=gst["sgst_paise"],
            igst_paise=gst["igst_paise"],
            total_paise=gst["total_paise"]
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)
    return order
