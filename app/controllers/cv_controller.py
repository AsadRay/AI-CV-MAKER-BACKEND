from flask_jwt_extended import get_jwt_identity
from ..models.cv import CV
from ..extensions import db
import uuid

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