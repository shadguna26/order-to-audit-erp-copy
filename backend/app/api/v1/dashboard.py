from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.api.deps import get_current_user, require_roles
from app.models.auth import User, UserRole
from app.services.dashboard_service import get_owner_dashboard_metrics

router = APIRouter(prefix="/dashboard", tags=["Owner Dashboard"])

@router.get("/owner", response_model=Dict[str, Any])
def owner_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OWNER, UserRole.ADMIN]))
):
    """
    NON-NEGOTIABLE OWNER DASHBOARD:
    Returns today's orders, live stock levels, variance alerts, cost per packet, and outstanding dues.
    """
    return get_owner_dashboard_metrics(db)
