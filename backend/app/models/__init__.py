# Import all models here so Alembic and Base.metadata see them together
from app.models.auth import User, UserRole, OTPRequest, RefreshToken
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
from app.models.production import (
    ProductionRun,
    ProductionRunItem,
    ProductionOverhead
)
from app.models.sales import (
    OrderStatus,
    Order,
    OrderItem,
    Dispatch
)
from app.models.billing import (
    PurchaseStatus,
    Purchase,
    PurchaseItem,
    InvoiceStatus,
    Invoice,
    InvoiceItem,
    CreditNote,
    Payment
)
from app.models.audit import AuditLog

__all__ = [
    "User",
    "UserRole",
    "MaterialType",
    "BaseUnitType",
    "RawMaterial",
    "Product",
    "BOM",
    "BOMItem",
    "Customer",
    "PriceList",
    "Supplier",
    "StockItemType",
    "StockLocationType",
    "StockDirection",
    "StockDocType",
    "StockLedger",
    "ProductionRun",
    "ProductionRunItem",
    "ProductionOverhead",
    "OrderStatus",
    "Order",
    "OrderItem",
    "Dispatch",
    "PurchaseStatus",
    "Purchase",
    "PurchaseItem",
    "InvoiceStatus",
    "Invoice",
    "InvoiceItem",
    "CreditNote",
    "Payment",
    "AuditLog"
]
