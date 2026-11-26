from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.business import DocumentSequence


def get_current_financial_year(target_date: date = None) -> str:
    """
    Calculates Indian Financial Year string: e.g. 2026-11-20 -> '2026-27'
    Financial year starts on April 1 and ends on March 31.
    """
    if target_date is None:
        target_date = date.today()

    year = target_date.year
    if target_date.month >= 4:
        next_yy = str((year + 1) % 100).zfill(2)
        return f"{year}-{next_yy}"
    else:
        prev_year = year - 1
        curr_yy = str(year % 100).zfill(2)
        return f"{prev_year}-{curr_yy}"


def generate_document_sequence(
    db: Session,
    model_class,
    no_column,
    prefix: str,
    target_date: date = None,
    business_id: int = 1,
) -> str:
    """
    Allocate per-business, per-FY document numbers under a row lock
    (e.g. TN/2026-27/0001). Works on both PostgreSQL (SELECT ... FOR UPDATE)
    and SQLite.
    """
    fy = get_current_financial_year(target_date)
    prefix_fy = f"{prefix}/{fy}/"
    doc_type = getattr(model_class, "__tablename__", str(model_class))

    seq_row = (
        db.query(DocumentSequence)
        .filter(
            DocumentSequence.business_id == business_id,
            DocumentSequence.doc_type == doc_type,
            DocumentSequence.prefix == prefix,
            DocumentSequence.fy == fy,
        )
        .with_for_update()
        .first()
    )

    if seq_row is None:
        # Bootstrap from existing rows in this business for this prefix+FY
        biz_col = getattr(model_class, "business_id", None)
        q = db.query(func.count(model_class.id)).filter(no_column.like(f"{prefix_fy}%"))
        if biz_col is not None:
            q = q.filter(biz_col == business_id)
        existing_count = q.scalar() or 0
        seq_row = DocumentSequence(
            business_id=business_id,
            doc_type=doc_type,
            prefix=prefix,
            fy=fy,
            last_seq=existing_count + 1,
        )
        db.add(seq_row)
        db.flush()
        next_seq = seq_row.last_seq
    else:
        seq_row.last_seq += 1
        db.flush()
        next_seq = seq_row.last_seq

    return f"{prefix_fy}{next_seq:04d}"
