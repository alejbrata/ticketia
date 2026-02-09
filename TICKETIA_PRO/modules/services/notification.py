import os
from flask import render_template
from flask_mail import Message

class NotificationService:
    @staticmethod
    def send_email(subject, recipients, body=None, html=None, attachments=None):
        from app import mail
        try:
            msg = Message(
                subject=subject,
                sender=os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@ticketia.com'),
                recipients=recipients
            )
            if body: msg.body = body
            if html: msg.html = html
            
            if attachments:
                for att in attachments:
                    with open(att['path'], 'rb') as fp:
                        msg.attach(
                            filename=att['filename'],
                            content_type=att.get('content_type', 'application/pdf'),
                            data=fp.read()
                        )
            
            mail.send(msg)
            return True
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    @staticmethod
    def send_whatsapp(to_number, body, media_url=None):
        # Placeholder for Twilio logic (to be moved here later)
        pass