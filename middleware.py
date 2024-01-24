from fastapi import Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import SessionLocal
from auth import authenticate_user
import logging
from typing import Annotated, List
from jose import jwt, JWTError
from datetime import datetime
from models import LogRecord
from auth import SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)


async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()

    # Get current user
    current_user = await get_current_user_from_request(request)

    response = await call_next(request)
    end_time = datetime.utcnow()

    log_data = {
        "user": current_user.get('username', 'unknown') if current_user else 'unknown',
        # Add current user name to log data
        "method": request.method,
        "url": request.url.path,
        "status_code": response.status_code,
        "timestamp": start_time,
        "duration": (end_time - start_time).total_seconds(),
    }

    # Log to console
    logger.info(log_data)

    # Log to database
    db = SessionLocal()
    try:
        log_to_db(db, log_data)
    finally:
        db.close()

    return response


async def get_current_user_from_request(request: Request):
    # Extract token from request headers
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    # Validate token and decode user information
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            return None  # Return None if user validation fails
        return {'username': username, 'id': user_id}
    except JWTError:
        return None


def log_to_db(db: Session, log_data: dict):
    db_log_record = LogRecord(**log_data)
    db.add(db_log_record)
    db.commit()
    db.refresh(db_log_record)


