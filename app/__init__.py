from flask import Flask
from .config import Config
from .extensions import db, jwt, api , migrate
from flask_cors import CORS
from jwt.exceptions import ExpiredSignatureError
from flask import jsonify


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["PROPAGATE_EXCEPTIONS"] = True

    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    api.init_app(app)



    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {"message": "Token has expired",
                "error": "token_expired"}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {"message": "Invalid token",
                "error": "invalid_token"}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {"message": "Authorization token is missing",
                "error": "authorization_required"}, 401

    @app.errorhandler(ExpiredSignatureError)
    def handle_expired_jwt(e):
        return jsonify({
            "message": "Token has expired",
            "error": "token_expired"
        }), 401

    from .models.user import User
    from .models.cv import CV

    from .routes.auth_namespace import auth_ns
    from .routes.cv_namespace import cv_ns

    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(cv_ns, path="/cv")

    return app
