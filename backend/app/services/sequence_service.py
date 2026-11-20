from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

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
    target_date: date = None
) -> str:
    """
    NON-NEGOTIABLE RULE 3:
    Invoice numbers follow financial year, e.g. TN/2026-27/0001.
    Also used for PO/2026-27/0001, PR/2026-27/0001, SO/2026-27/0001, etc.
    """
    fy = get_current_financial_year(target_date)
    prefix_fy = f"{prefix}/{fy}/"

    # Count how many records exist for this prefix and financial year
    count = db.query(func.count(model_class.id)).filter(
        no_column.like(f"{prefix_fy}%")
    ).scalar() or 0

    next_seq = count + 1
    return f"{prefix_fy}{next_seq:04d}"
