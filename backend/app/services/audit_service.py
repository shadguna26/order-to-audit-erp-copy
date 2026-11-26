from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.auth import User
from app.models.business import Business

def log_audit_event(
    db: Session,
    user_id: int,
    table_name: str,
    record_id: int,
    action: str,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    business_id: Optional[int] = None,
) -> AuditLog:
    """
    NON-NEGOTIABLE RULE 4:
    Every edit to an invoice or production run writes to an audit_log (user, time, old/new values).
    """
    resolved_biz_id = business_id
    if resolved_biz_id is None and user_id is not None:
        u = db.query(User.business_id).filter(User.id == user_id).first()
        if u:
            resolved_biz_id = u[0]
    if resolved_biz_id is None:
        resolved_biz_id = db.query(Business.id).order_by(Business.id.asc()).scalar() or 1

    log_entry = AuditLog(
        business_id=resolved_biz_id,
        table_name=table_name,
        record_id=record_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        user_id=user_id
    )
    db.add(log_entry)
    db.flush()
    return log_entry
