from flask_restx import Namespace, Resource, fields
from flask import request
from ..controllers.auth_controller import register_user, login_user, reset_password, verify_otp_and_create_user, resend_otp, forget_password, verify_password_reset_otp

auth_ns = Namespace("auth", description="Authentication operations")

register_model = auth_ns.model("Register", {
    "name": fields.String(required=True),
    "email": fields.String(required=True),
    "password": fields.String(required=True)
})

login_model = auth_ns.model("Login", {
    "email": fields.String(required=True),
    "password": fields.String(required=True)
})

otp_verify_model = auth_ns.model("VerifyOTP", {
    "email": fields.String(required=True),
    "otp": fields.String(required=True)
})

otp_resend_model = auth_ns.model("ResendOTP", {
    "email": fields.String(required=True)
})
reset_password_model = auth_ns.model("ResetPassword", {
    "email": fields.String(required=True),
    "otp": fields.String(required=True),
    "new_password": fields.String(required=True)
})

@auth_ns.route("/register")
class Register(Resource):
    @auth_ns.expect(register_model)
    def post(self):
        data = request.json
        return register_user(data)


@auth_ns.route("/verify-otp")
class VerifyOTP(Resource):
    @auth_ns.expect(otp_verify_model)
    def post(self):
        data = request.json
        return verify_otp_and_create_user(data)


@auth_ns.route("/resend-otp")
class ResendOTP(Resource):
    @auth_ns.expect(otp_resend_model)
    def post(self):
        data = request.json
        return resend_otp(data)


@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        data = request.json
        return login_user(data)
    
@auth_ns.route("/forgot-password")
class ForgotPassword(Resource):
    @auth_ns.expect(otp_resend_model)
    def post(self):
        data = request.json
        return forget_password(data)
    
@auth_ns.route("/verify-reset-otp")
class VerifyResetOTP(Resource):
    @auth_ns.expect(otp_verify_model)
    def post(self):
        data = request.json
        return verify_password_reset_otp(data)

@auth_ns.route("/reset-password")
class ResetPassword(Resource):
    @auth_ns.expect(reset_password_model)
    def post(self):
        data = request.json
        return reset_password(data)