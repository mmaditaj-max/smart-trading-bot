import smtplib
from email.mime.text import MIMEText

from app.config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_TO


def send_email(subject: str, body: str):
    if not all([EMAIL_HOST, EMAIL_USER, EMAIL_PASSWORD, EMAIL_TO]):
        print("[Email] الإعدادات غير كاملة، تم تجاهل البريد الإلكتروني.")
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, [EMAIL_TO], msg.as_string())
        server.quit()
        print("[Email] تم إرسال الإشعار بنجاح.")
        return True
    except Exception as exc:
        print(f"[Email] فشل إرسال الإشعار: {exc}")
        return False
