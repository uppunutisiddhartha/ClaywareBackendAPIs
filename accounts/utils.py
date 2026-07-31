from twilio.rest import Client
from django.conf import settings


client = Client(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)


def send_otp(phone_number):
    """
    Send OTP using Twilio Verify
    """

    try:

        verification = (
            client.verify
            .v2
            .services(settings.TWILIO_VERIFY_SERVICE_SID)
            .verifications
            .create(
                to=f"+91{phone_number}",
                channel="sms"
            )
        )

        return verification.status

    except Exception as e:
        raise Exception(str(e))


def verify_otp(phone_number, otp):
    """
    Verify OTP using Twilio Verify
    """

    try:

        verification_check = (
            client.verify
            .v2
            .services(settings.TWILIO_VERIFY_SERVICE_SID)
            .verification_checks
            .create(
                to=f"+91{phone_number}",
                code=otp
            )
        )

        return verification_check.status

    except Exception as e:
        raise Exception(str(e))