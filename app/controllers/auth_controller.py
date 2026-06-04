import os
import secrets
import json
import resend
import redis
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from ..models.user import User
from ..extensions import db
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from app.config import Config


r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)



def generate_otp(otp_length=6):
    return str(secrets.randbelow(10**otp_length)).zfill(otp_length)

def send_otp_email(to_email, otp):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; background-color:#f4f4f4; font-family: Arial, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        
                        <!-- Header -->
                        <tr>
                            <td style="background-color:#4F46E5; padding: 32px; text-align:center;">
                                <h1 style="color:#ffffff; margin:0; font-size:24px;">CV Builder</h1>
                            </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px 32px;">
                                <h2 style="color:#111827; margin:0 0 12px;">Verify Your Email</h2>
                                <p style="color:#6B7280; font-size:15px; line-height:1.6; margin:0 0 32px;">
                                    Thanks for signing up! Use the OTP below to complete your registration.
                                    This code expires in <strong>5 minutes</strong>.
                                </p>

                                <!-- OTP Box -->
                                <div style="background-color:#F3F4F6; border-radius:8px; padding: 24px; text-align:center; margin-bottom:32px;">
                                    <p style="margin:0 0 8px; color:#6B7280; font-size:13px; text-transform:uppercase; letter-spacing:1px;">Your OTP Code</p>
                                    <p style="margin:0; font-size:40px; font-weight:bold; color:#4F46E5; letter-spacing:8px;">{otp}</p>
                                </div>

                                <p style="color:#9CA3AF; font-size:13px; line-height:1.6; margin:0;">
                                    If you didn't request this, you can safely ignore this email.
                                    Someone may have entered your email address by mistake.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color:#F9FAFB; padding: 24px 32px; text-align:center; border-top: 1px solid #E5E7EB;">
                                <p style="margin:0; color:#9CA3AF; font-size:12px;">
                                    © 2025 CV Builder. All rights reserved.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Your OTP Code - CV Builder"
    msg['From'] = Config.MAIL_USERNAME
    msg['To'] = to_email

    msg.attach(MIMEText(html, 'html'))

    try:
        if Config.MAIL_USE_SSL:
            with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(Config.MAIL_USERNAME, to_email, msg.as_string())
        else:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                if Config.MAIL_USE_TLS:
                    server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(Config.MAIL_USERNAME, to_email, msg.as_string())

        return {"message": "Email sent successfully"}

    except smtplib.SMTPException as e:
        return {"error": str(e)}



def register_user(data):
    email = data.get('email')

    if User.query.filter_by(email=email).first():
        return {"message": "Email already registered"}, 400

    otp = generate_otp()

    r.setex(f"otp:{email}", 300, otp)
    r.setex(f"pending:{email}", 300, json.dumps({
        "name": data.get('name'),
        "email": email,
        "password": data.get('password')
    }))

    send_otp_email(email, otp)

    return {"message": "OTP sent to your email. Please verify to complete registration."}, 200


def verify_otp_and_create_user(data):
    email = data.get('email')
    otp_input = data.get('otp')

    stored_otp = r.get(f"otp:{email}")
    pending_data = r.get(f"pending:{email}")

    if not stored_otp or not pending_data:
        return {"message": "OTP expired or not found. Please register again."}, 400

    if stored_otp != otp_input:
        return {"message": "Invalid OTP."}, 400

    # OTP valid — create the user
    user_data = json.loads(pending_data)
    user = User(
        name=user_data['name'],
        email=user_data['email'],
        password_hash=generate_password_hash(user_data['password'])
    )
    db.session.add(user)
    db.session.commit()

    # Clean up Redis
    r.delete(f"otp:{email}")
    r.delete(f"pending:{email}")

    return {
        "message": "User registered successfully",
        "user": {"id": str(user.id), "name": user.name, "email": user.email}
    }, 201

def resend_otp(data):
    email = data.get('email')

    if not r.get(f"pending:{email}"):
        return {"message": "No pending registration found. Please register first."}, 400

    otp = generate_otp()

    r.setex(f"otp:{email}", 300, otp)
    r.expire(f"pending:{email}", 300)  # sync expiry with new OTP

    send_otp_email(email, otp)

    return {"message": "OTP resent to your email."}, 200

def login_user(data):
    user = User.query.filter_by(email=data.get('email')).first()

    
    if not user:
        return {"message": "User not found"}, 404

    if not check_password_hash(user.password_hash, data.get('password')):
        return {"message": "Invalid email or password"}, 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {"id": str(user.id), "name": user.name, "email": user.email}
    }, 200


def forget_password(data):
    email = data.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        return {"message": "If this email exists, OTP has been sent."}, 200

    otp = generate_otp()

    # Store OTP in Redis (5 min)
    r.setex(f"reset_otp:{email}", 300, otp)

    send_otp_email(email, otp)

    return {"message": "OTP sent to your email."}, 200


def verify_password_reset_otp(data):
    email = data.get('email')
    otp_input = data.get('otp')

    stored_otp = r.get(f"reset_otp:{email}")

    if not stored_otp:
        return {"message": "OTP expired or not found."}, 400

    if stored_otp != otp_input:
        return {"message": "Invalid OTP."}, 400

    # Delete OTP
    r.delete(f"reset_otp:{email}")

    # Create short-lived reset token (5 min)
    reset_token = str(uuid.uuid4())
    r.setex(f"reset_token:{reset_token}", 300, email)

    return {
        "message": "OTP verified.",
        "reset_token": reset_token
    }, 200


def reset_password(data):
    reset_token = data.get('reset_token')
    new_password = data.get('new_password')

    email = r.get(f"reset_token:{reset_token}")

    if not email:
        return {"message": "Invalid or expired reset token."}, 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return {"message": "User not found."}, 404

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    # Delete reset token after success
    r.delete(f"reset_token:{reset_token}")

    return {"message": "Password reset successful."}, 200