import os
import smtplib
import ssl
import random
import time
from email.mime.text import MIMEText
from typing import Optional

from loguru import logger

try:
    import firebase_admin
    from firebase_admin import auth as fb_auth
except Exception:
    firebase_admin = None  # type: ignore
    fb_auth = None  # type: ignore

# Simple in-memory store as fallback; for production replace with Redis/DB
_OTP_STORE = {}
_OTP_TTL_SECONDS = 10 * 60


def _send_email(to_email: str, subject: str, body: str) -> bool:
    host = os.getenv('SMTP_HOST')
    port = int(os.getenv('SMTP_PORT', '587'))
    user = os.getenv('SMTP_USER')
    password = os.getenv('SMTP_PASSWORD')
    sender = os.getenv('SMTP_FROM', user or '')

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email

    if not host or not user or not password or not sender:
        logger.warning('SMTP not configured; printing OTP email to logs for development')
        logger.info(f"To: {to_email}\nSubject: {subject}\n\n{body}")
        return True

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port) as server:
            server.starttls(context=context)
            server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def request_email_otp(email: str) -> bool:
    code = f"{random.randint(0, 999999):06d}"
    expires_at = int(time.time()) + _OTP_TTL_SECONDS
    _OTP_STORE[f"email:{email}"] = {"code": code, "exp": expires_at}

    subject = 'Your verification code'
    body = f"Your verification code is: {code}\n\nIt expires in 10 minutes."
    return _send_email(email, subject, body)


def verify_email_otp(email: str, code: str) -> bool:
    key = f"email:{email}"
    record = _OTP_STORE.get(key)
    now = int(time.time())
    if not record:
        return False
    if now > record['exp']:
        _OTP_STORE.pop(key, None)
        return False
    if code.strip() != record['code']:
        return False
    # consume
    _OTP_STORE.pop(key, None)
    return True


def mint_custom_token_for_email(email: str) -> Optional[str]:
    if firebase_admin is None or fb_auth is None:
        logger.warning('firebase_admin not available; cannot mint custom token')
        return None
    try:
        # Use email as UID namespace
        uid = f"email:{email.lower()}"
        additional_claims = {"email": email}
        token = fb_auth.create_custom_token(uid, additional_claims)
        return token.decode('utf-8') if isinstance(token, bytes) else str(token)
    except Exception as e:
        logger.error(f"Failed to mint custom token: {e}")
        return None