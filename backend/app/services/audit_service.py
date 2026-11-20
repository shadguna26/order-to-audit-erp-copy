from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

def log_audit_event(
    db: Session,
    user_id: int,
    table_name: str,
    record_id: int,
    action: str,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    NON-NEGOTIABLE RULE 4:
    Every edit to an invoice or production run writes to an audit_log (user, time, old/new values).
    """
    log_entry = AuditLog(
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
