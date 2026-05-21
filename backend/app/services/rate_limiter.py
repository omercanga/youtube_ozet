import os
import logging
from datetime import date
from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models import RateLimit

logger = logging.getLogger(__name__)

FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "5"))


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_and_increment(ip: str, db: Session) -> tuple[bool, int, int]:
    """Check rate limit and increment counter. Returns (allowed, new_count, limit)."""
    today = date.today()

    record = db.query(RateLimit).filter(
        RateLimit.ip_address == ip,
        RateLimit.date == today,
    ).first()

    if record is None:
        try:
            record = RateLimit(ip_address=ip, date=today, count=1)
            db.add(record)
            db.commit()
            return True, 1, FREE_DAILY_LIMIT
        except IntegrityError:
            db.rollback()
            record = db.query(RateLimit).filter(
                RateLimit.ip_address == ip,
                RateLimit.date == today,
            ).first()

    if record.count >= FREE_DAILY_LIMIT:
        return False, record.count, FREE_DAILY_LIMIT

    record.count += 1
    db.commit()
    return True, record.count, FREE_DAILY_LIMIT


def get_status(ip: str, db: Session) -> dict:
    """Return current usage status for an IP without incrementing."""
    today = date.today()
    record = db.query(RateLimit).filter(
        RateLimit.ip_address == ip,
        RateLimit.date == today,
    ).first()

    used = record.count if record else 0
    return {
        "ip": ip,
        "used": used,
        "limit": FREE_DAILY_LIMIT,
        "remaining": max(0, FREE_DAILY_LIMIT - used),
        "date": today.isoformat(),
    }
