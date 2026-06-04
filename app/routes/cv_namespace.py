# app/routes/cv_namespace.py

from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from ..controllers.cv_controller import (
    create_cv,
    get_user_cvs,
    get_single_cv,
    check_and_increment_message_limit,
    limit_message_length,
    check_and_increment_guest_limit,
    verify_jwt_in_request

)
from ..services.ai_service import generate_structured_cv
from ..models.cv import CV
from ..extensions import db
import traceback


cv_ns = Namespace("cv", description="CV operations")

create_model = cv_ns.model("CreateCV", {
    "title": fields.String(required=True, description="CV title"),
    "template_name": fields.String(required=True, description="Template name (e.g., 'modern-minimal')")
})

update_model = cv_ns.model("UpdateCV", {
    "title": fields.String(description="CV title"),
    "template_name": fields.String(description="Template name"),
    "cv_data": fields.Raw(description="CV Data object")
})

chat_model = cv_ns.model("ChatMessage", {
    "message": fields.String(required=True, description="User message to update CV")
})


@cv_ns.route("/")
class CVList(Resource):
    """CV collection endpoint"""

    @jwt_required()
    def get(self):
        """Get all CVs for the authenticated user"""
        try:
            return get_user_cvs()
        except Exception as e:
            return {"message": f"Error fetching CVs: {str(e)}"}, 500

    @jwt_required()
    @cv_ns.expect(create_model)
    def post(self):
        """Create a new CV"""
        try:
            data = request.json
            return create_cv(data)
        except Exception as e:
            return {"message": f"Error creating CV: {str(e)}"}, 500


@cv_ns.route("/<string:cv_id>")
class SingleCV(Resource):
    """Single CV endpoint"""

    @jwt_required()
    def get(self, cv_id):
        """Get CV data for frontend rendering"""
        try:
            user_id = get_jwt_identity()
            cv = CV.query.filter_by(id=cv_id, user_id=user_id).first()

            if not cv:
                return {"message": "CV not found"}, 404
            
        

            return {
                "id": str(cv.id),  # Convert UUID to string
                "title": cv.title,
                "template_name": cv.template_name,
                "cv_data": cv.cv_data if cv.cv_data else {
                    "personal_info": {
                        "name": "",
                        "email": "",
                        "phone": "",
                        "location": "",
                        "position": "",
                        "summary": ""
                    },
                    "experience": [],
                    "education": [],
                    "skills": [],
                    "projects": [],
                    "research_and_publications": [],
                    "certifications": [],
                },
                "created_at": cv.created_at.isoformat(),  # Convert datetime to string
                "updated_at": cv.updated_at.isoformat() if cv.updated_at else None
            }, 200
            
        except Exception as e:
            return {"message": f"Error fetching CV: {str(e)}"}, 500
    
    @jwt_required()
    def delete(self, cv_id):
        try:
            user_id = get_jwt_identity()
            cv = CV.query.filter_by(id=cv_id, user_id=user_id).first()

            if not cv:
                return {"message": "CV not found"}, 404

            db.session.delete(cv)
            db.session.commit()

            return {"message": "CV deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            return {"message": f"Error deleting CV: {str(e)}"}, 500
    
    @jwt_required()
    @cv_ns.expect(update_model)
    def put(self, cv_id):
        """Update CV title or template"""
        try:
            user_id = get_jwt_identity()
            cv = CV.query.filter_by(id=cv_id, user_id=user_id).first()

            if not cv:
                return {"message": "CV not found"}, 404

            data = request.json
            
            if 'title' in data:
                cv.title = data['title']
            
            if 'template_name' in data:
                cv.template_name = data['template_name']
            
            if 'cv_data' in data:
                cv.cv_data = data['cv_data']
            
            db.session.commit()

            return {
                "message": "CV updated successfully",
                "cv": {
                    "id": str(cv.id),  # Convert UUID to string
                    "title": cv.title,
                    "template_name": cv.template_name,
                    "created_at": cv.created_at.isoformat(),  # Convert datetime to string
                    "updated_at": cv.updated_at.isoformat() if cv.updated_at else None
                }
            }, 200
        except Exception as e:
            db.session.rollback()
            return {"message": f"Error updating CV: {str(e)}"}, 500


@cv_ns.route("/chat")
class CVChat(Resource):
    """CV chat endpoint for AI-powered updates"""

    @cv_ns.expect(chat_model)
    def post(self):
        """Update CV data through conversational AI — works for guests and logged-in users"""
        try:
            # Try JWT — don't fail if missing
            user_id = None
            try:
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
            except Exception:
                pass

            data = request.json
            user_message = data.get("message", "").strip()

            if not user_message:
                return {"message": "Message cannot be empty"}, 400

            if not limit_message_length(user_message):
                return {"message": "Message exceeds maximum allowed length"}, 400

            # Rate limiting
            if user_id:
                if not check_and_increment_message_limit(user_id):
                    return {"message": "Message limit reached for today. Please try again tomorrow."}, 429
            else:
                
                if not check_and_increment_guest_limit():
                    return {"message": "Guest message limit reached. Please register to continue."}, 429

            # Get existing CV data
            if user_id:
                cv_id = data.get("cv_id")
                cv = CV.query.filter_by(id=cv_id, user_id=user_id).first() if cv_id else None
                existing_data = cv.cv_data if cv and cv.cv_data else get_empty_cv()
            else:
                cv = None
                # Guest sends cv_data in request body — lives only in frontend
                existing_data = data.get("cv_data") or get_empty_cv()

            # Generate AI response
            ai_response = generate_structured_cv(user_message, existing_data)

            if not ai_response:
                return {"message": "AI request failed"}, 500

            if not isinstance(ai_response, dict) or "cv_data" not in ai_response:
                return {
                    "message": "AI returned invalid response structure",
                    "hint": "Please try rephrasing your message"
                }, 500

            # Save to DB only if logged in
            if user_id and cv:
                cv.cv_data = ai_response.get("cv_data", existing_data)
                db.session.commit()

            return {
                "message": "CV updated successfully",
                "cv_data": ai_response.get("cv_data"),
                "ai_response": ai_response.get("ai_message", ""),
                "next_question": ai_response.get("next_question", ""),
                "progress_percentage": ai_response.get("progress_percentage", 0),
                "current_section": ai_response.get("current_section", "personal_info"),
                "all_complete": ai_response.get("all_complete", False),
                "is_guest": user_id is None
            }, 200

        except Exception as e:
            db.session.rollback()
            print(f"Error in CV chat: {str(e)}")
            print(traceback.format_exc())
            return {"message": f"Error updating CV: {str(e)}"}, 500


def get_empty_cv():
    return {
        "personal_info": {
            "name": "", "email": "", "phone": "",
            "location": "", "position": "", "summary": ""
        },
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "research_and_publications": [],
        "certifications": [],
    }