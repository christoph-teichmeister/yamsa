from apps.mail.services.base_email_service import BaseYamsaEmailService, EmailExtraContext, EmailUserTextContext


class TestEmailService(BaseYamsaEmailService):
    """
    Email to my admins to inform them about something important.
    """

    subject = "Test Email!"

    email_extra_context = EmailExtraContext(
        show_cta=True,
        cta_btn_link="https://yamsa.onrender.com",
        cta_btn_text="Test Link",
    )

    email_user_text_context = EmailUserTextContext(
        text_list=[
            "This is a test email.",
            "Click the link below to go somewhere.",
        ]
    )
