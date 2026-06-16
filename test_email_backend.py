from __future__ import annotations

from jarvis.app.email_sender import EmailSender


sender = EmailSender()

SENDER_EMAIL = "your_real_sender_email@gmail.com"
APP_PASSWORD = "your_16_character_gmail_app_password"
RECEIVER_EMAIL = "your_receiver_email@gmail.com"

print("CONFIGURE EMAIL:")
print(
    sender.update_settings(
        enabled=True,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_security="starttls",
        smtp_username=SENDER_EMAIL,
        sender_email=SENDER_EMAIL,
        sender_name="Jarvis",
    )
)

print("\nSAVE SMTP PASSWORD:")
print(sender.set_smtp_password(APP_PASSWORD))

print("\nCURRENT SETTINGS:")
print(sender.get_public_settings())

print("\nSEND TEST EMAIL:")
print(sender.send_test_email(RECEIVER_EMAIL))