from apps.mail.services.base_email_service import BaseYamsaEmailService, YamsaEmailContext


class TestEmail(BaseYamsaEmailService):
    """
    Email to my admins to inform them about something important.
    """

    subject = "Test E-Mail!"

    email_context = YamsaEmailContext(
        show_cta=True,
        cta_btn_link="https://yamsa.onrender.com",
        cta_btn_text="Test Link",
        text="This is a test email. Click the link below to go somewhere.",
    )
