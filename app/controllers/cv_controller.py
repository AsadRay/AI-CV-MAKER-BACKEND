from itertools import count
from flask_jwt_extended import get_jwt_identity
from flask import request

from app.models.user import User
from ..models.cv import CV
from ..extensions import db
import uuid
from datetime import datetime, timedelta
from .auth_controller import r
from flask_jwt_extended import verify_jwt_in_request as _verify_jwt


DAILY_MESSAGE_LIMIT = 500
GUEST_MESSAGE_LIMIT = 100

def create_cv(data):
    user_id = get_jwt_identity()

    copy_previous_data = data.get('copy_previous_data', False)  

    copied_data = {}
    if copy_previous_data:
        existing_cv = CV.query.filter(
            CV.user_id == user_id,
            CV.cv_data != None
        ).order_by(CV.created_at.desc()).first()
        copied_data = existing_cv.cv_data if existing_cv else {}

    cv = CV(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=data.get('title'),
        template_name=data.get('template_name'),
        cv_data=copied_data
    )

    db.session.add(cv)
    db.session.commit()

    return {
        "message": "CV created successfully",
        "cv": {
            "id": str(cv.id),
            "title": cv.title,
            "template_name": cv.template_name,
            "created_at": cv.created_at.isoformat()
        },
        "data_prefilled": bool(copied_data)
    }, 201


def get_user_cvs():
    """Get all CVs for the authenticated user"""
    user_id = get_jwt_identity()
    cvs = CV.query.filter_by(user_id=user_id).all()
    
    return {
        "cvs": [
            {
                "id": str(cv.id),  # Convert UUID to string
                "title": cv.title,
                "template_name": cv.template_name,
                "created_at": cv.created_at.isoformat(),
                "updated_at": cv.updated_at.isoformat() if cv.updated_at else None
            }
            for cv in cvs
        ]
    }, 200


def get_single_cv(cv_id):
    """Get a single CV by ID"""
    user_id = get_jwt_identity()
    cv = CV.query.filter_by(id=cv_id, user_id=user_id).first()
    
    if not cv:
        return {"message": "CV not found"}, 404
    
    return {
        "id": str(cv.id),  # Convert UUID to string
        "title": cv.title,
        "template_name": cv.template_name,
        "cv_data": cv.cv_data if cv.cv_data else {},
        "created_at": cv.created_at.isoformat(),
        "updated_at": cv.updated_at.isoformat() if cv.updated_at else None
    }, 200
def get_client_ip():
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    
    return request.remote_addr

def check_and_increment_message_limit(user_id):
    user = User.query.get(user_id)
    today = datetime.utcnow().date()

    if user.message_reset_date != today:
        user.message_count = 0
        user.message_reset_date = today
        db.session.commit()

    if user.message_count >= DAILY_MESSAGE_LIMIT:
        return False

    db.session.query(User).filter_by(id=user_id).update(
        {"message_count": User.message_count + 1}
    )
    db.session.commit()
    return True


# def limit_message_length(user_message):
#     if len(user_message) > 500:
#         return user_message[:500]
#     return user_message


def limit_message_length(user_message):
    return len(user_message) <= 500


def check_and_increment_guest_limit():

    ip = get_client_ip()
    print(f"Client IP: {ip}")  # Debugging statement

    key = f"guest_limit:{ip}:{datetime.utcnow().date()}"
    count = r.get(key)

    if count and int(count) >= GUEST_MESSAGE_LIMIT:
        return False

    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, 86400)
    pipe.execute()

    return True

def verify_jwt_in_request(optional=False):
    try:
        _verify_jwt(optional=optional)
    except Exception:
        pass