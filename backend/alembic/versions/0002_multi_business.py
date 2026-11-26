"""Add businesses table, document_sequences, and business_id multi-tenancy across all tables.

Revision ID: 0002_multi_business
Revises: 30f6e1a249ed
Create Date: 2026-11-26 15:15:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_multi_business"
down_revision = "30f6e1a249ed"
branch_labels = None
depends_on = None

BUSINESS_OWNED_TABLES = [
    "users",
    "raw_materials",
    "products",
    "bom",
    "customers",
    "price_list",
    "suppliers",
    "orders",
    "dispatches",
    "purchases",
    "invoices",
    "credit_notes",
    "payments",
    "production_runs",
    "production_overheads",
    "stock_ledger",
    "audit_log",
]


def upgrade() -> None:
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("business_type", sa.Enum("manufacturer", "trader", name="businesstype"), nullable=False, server_default="manufacturer"),
        sa.Column("gstin", sa.String(length=15), nullable=True),
        sa.Column("state", sa.String(length=50), nullable=False, server_default="Tamil Nadu"),
        sa.Column("state_code", sa.String(length=2), nullable=False, server_default="33"),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("pincode", sa.String(length=10), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("invoice_prefix", sa.String(length=10), nullable=False, server_default="TN"),
        sa.Column("variance_tolerance_pct", sa.Numeric(5, 2), nullable=False, server_default="3.00"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "document_sequences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False, index=True),
        sa.Column("doc_type", sa.String(length=30), nullable=False),
        sa.Column("prefix", sa.String(length=15), nullable=False),
        sa.Column("fy", sa.String(length=10), nullable=False),
        sa.Column("last_seq", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("business_id", "doc_type", "prefix", "fy", name="uq_doc_seq_biz_type_prefix_fy"),
    )

    # Seed Business #1 from existing factory settings
    op.execute(
        """
        INSERT INTO businesses (id, name, business_type, gstin, state, state_code, address, pincode, phone, email, invoice_prefix, variance_tolerance_pct, is_active)
        VALUES (1, 'Sri Lakshmi Snacks', 'manufacturer', '33AAAAA0000A1Z5', 'Tamil Nadu', '33',
                'Plot 42, SIDCO Industrial Estate, Thuvakudi, Tiruchirappalli', '620015',
                '+91-431-2501234', 'accounts@srilakshmisnacks.in', 'TN', 3.00, true)
        """
    )

    # Add business_id to every business-owned table, backfill 1, then enforce NOT NULL + FK + index
    for tbl in BUSINESS_OWNED_TABLES:
        op.add_column(tbl, sa.Column("business_id", sa.Integer(), nullable=True))
        op.execute(f"UPDATE {tbl} SET business_id = 1 WHERE business_id IS NULL")
        op.alter_column(tbl, "business_id", nullable=False)
        op.create_foreign_key(f"fk_{tbl}_business_id", tbl, "businesses", ["business_id"], ["id"])
        op.create_index(f"ix_{tbl}_business_id", tbl, ["business_id"])

    # Customer shop fields
    op.add_column("customers", sa.Column("area", sa.String(length=100), nullable=True))
    op.add_column("customers", sa.Column("status", sa.String(length=20), nullable=False, server_default="active"))


def downgrade() -> None:
    op.drop_column("customers", "status")
    op.drop_column("customers", "area")

    for tbl in reversed(BUSINESS_OWNED_TABLES):
        op.drop_index(f"ix_{tbl}_business_id", table_name=tbl)
        op.drop_constraint(f"fk_{tbl}_business_id", tbl, type_="foreignkey")
        op.drop_column(tbl, "business_id")

    op.drop_table("document_sequences")
    op.drop_table("businesses")
