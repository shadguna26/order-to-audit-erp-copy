from abc import ABC, abstractmethod
import logging
from app.config import settings

logger = logging.getLogger("sms_provider")


class SmsProvider(ABC):
    """Interface for sending OTP SMS messages."""

    @abstractmethod
    def send_otp(self, mobile: str, code: str) -> None:
        """Send a 6-digit OTP code to a normalized +91XXXXXXXXXX mobile number."""
        raise NotImplementedError


class ConsoleSmsProvider(SmsProvider):
    """Development SMS provider that prints OTPs to console only."""

    def send_otp(self, mobile: str, code: str) -> None:
        print(f"[SMS DEV] OTP for {mobile}: {code}")


class Msg91SmsProvider(SmsProvider):
    """Stub for MSG91 Flow API integration (never logs OTPs)."""

    def __init__(self, auth_key: str | None = None, template_id: str | None = None):
        self.auth_key = auth_key or settings.MSG91_AUTH_KEY
        self.template_id = template_id or settings.MSG91_TEMPLATE_ID

    def send_otp(self, mobile: str, code: str) -> None:
        if not self.auth_key or not self.template_id:
            raise RuntimeError("MSG91_AUTH_KEY and MSG91_TEMPLATE_ID must be configured for MSG91 provider")
        # Production implementation: POST https://control.msg91.com/api/v5/flow/
        # Never log OTP values here.
        logger.info("Dispatching OTP via MSG91 to %s", mobile[-4:])


class TwilioSmsProvider(SmsProvider):
    """Stub for Twilio Programmable SMS integration (never logs OTPs)."""

    def __init__(
        self,
        account_sid: str | None = None,
        auth_token: str | None = None,
        from_number: str | None = None,
    ):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.from_number = from_number or settings.TWILIO_FROM_NUMBER

    def send_otp(self, mobile: str, code: str) -> None:
        if not self.account_sid or not self.auth_token or not self.from_number:
            raise RuntimeError("Twilio credentials must be configured for Twilio provider")
        # Production implementation: POST Twilio Messages API
        # Never log OTP values here.
        logger.info("Dispatching OTP via Twilio to %s", mobile[-4:])


def get_sms_provider() -> SmsProvider:
    provider_name = (settings.SMS_PROVIDER or "console").strip().lower()
    if provider_name == "console":
        return ConsoleSmsProvider()
    if provider_name == "msg91":
        return Msg91SmsProvider()
    if provider_name == "twilio":
        return TwilioSmsProvider()
    raise ValueError(f"Unsupported SMS_PROVIDER: {settings.SMS_PROVIDER}")
