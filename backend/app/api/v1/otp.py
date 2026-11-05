from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.otp_service import request_email_otp, verify_email_otp, mint_custom_token_for_email

router = APIRouter()


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    code: str


@router.post('/auth/otp/request')
async def otp_request(payload: OTPRequest):
    if request_email_otp(payload.email):
        return {"ok": True}
    raise HTTPException(status_code=500, detail='Failed to send OTP')


@router.post('/auth/otp/verify')
async def otp_verify(payload: OTPVerify):
    if not verify_email_otp(payload.email, payload.code):
        raise HTTPException(status_code=400, detail='Invalid or expired code')
    token = mint_custom_token_for_email(payload.email)
    return {"ok": True, "customToken": token}