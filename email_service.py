"""
Email Service for X (Twitter) Daily Operations (Urdu & Media Enhanced)
Dispatches:
1. Daily Morning Approval Requests (with 7 verified Urdu posts, photos & scheduled times)
2. Daily Evening Analytics & Feedback Reports (impressions, learnings, next day plan)
Target Recipient: zubair.ahmad4545438@gmail.com
"""

import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "zubairahmad.mehmood@iisat.edu.pk")
SMTP_PASS = os.getenv("SMTP_PASS", "")

USER_EMAIL = os.getenv("USER_EMAIL", "zubair.ahmad4545438@gmail.com")

def generate_approval_email_html(queue_data: dict) -> str:
    posts = queue_data.get("posts", [])
    date_str = queue_data.get("date", datetime.now().strftime("%Y-%m-%d"))

    posts_html = ""
    for idx, p in enumerate(posts, 1):
        category = p.get("category", "خبر")
        time_slot = p.get("time_slot", "TBD")
        source_name = p.get("source_name", "Source")
        source_url = p.get("source_url", "#")
        image_url = p.get("image_url", "")
        hashtags = " ".join(p.get("hashtags", []))
        text = p.get("text", "")

        img_html = ""
        if image_url:
            img_html = f"""
            <div style="margin-bottom: 12px; text-align: center;">
                <img src="{image_url}" alt="Post Visual" style="width: 100%; max-height: 260px; object-fit: cover; border-radius: 6px; border: 1px solid #e2e8f0;" />
            </div>
            """

        content_block = f"""
        <div style='background: #f8fafc; border-right: 4px solid #0284c7; padding: 14px; margin: 10px 0; border-radius: 4px; direction: rtl; text-align: right; font-family: "Segoe UI", Tahoma, sans-serif;'>
            <p style='margin: 0; font-size: 15px; line-height: 1.7; color: #1e293b; white-space: pre-wrap;'>{text}</p>
        </div>
        """

        posts_html += f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 12px;">
                <span style="font-size: 14px; font-weight: bold; color: #0f172a;">#{idx} &bull; {time_slot}</span>
                <span style="font-size: 13px; background: #e0f2fe; color: #0369a1; padding: 3px 10px; border-radius: 12px; font-weight: 600;">{category}</span>
            </div>
            {img_html}
            {content_block}
            <div style="font-size: 12px; color: #64748b; margin-top: 10px; direction: ltr; text-align: left;">
                <b>تصدیق شدہ ذریعہ:</b> <a href="{source_url}" style="color: #0284c7; text-decoration: none;">{source_name}</a> &bull; 
                <b>ٹیگز:</b> {hashtags}
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html dir="ltr">
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; }}
            .container {{ max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }}
            .header {{ background: #0f172a; color: #ffffff; padding: 24px; text-align: center; }}
            .content {{ padding: 24px; }}
            .action-box {{ background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 18px; text-align: center; margin-bottom: 24px; }}
            .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px; text-align: center; font-size: 12px; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0; font-size: 22px;">Daily Urdu X (Twitter) Queue &bull; {date_str}</h2>
                <p style="margin: 6px 0 0; font-size: 14px; color: #94a3b8;">7 مصدقہ اردو پوسٹس بمعہ تصاویر برائے پاکستانی صارفین</p>
            </div>
            <div class="content">
                <div class="action-box">
                    <h3 style="margin: 0 0 8px; color: #065f46; font-size: 17px;">ایک لفظ میں منظوری کا طریقہ:</h3>
                    <p style="margin: 0 0 12px; font-size: 14px; color: #047857; line-height: 1.5;">
                        تمام 7 پوسٹس کو وقت پر شیڈول کرنے کے لیے اس ای میل کے جواب میں صرف <b>Approved</b> لکھ کر ریپلائی کر دیں۔
                    </p>
                </div>

                {posts_html}
            </div>
            <div class="footer">
                <p style="margin: 0;">Autonomous Social Media Manager for @Zubair05111485</p>
                <p style="margin: 4px 0 0; font-size: 11px;">Reporting with Dawn News & BBC Urdu &bull; Cloud Powered</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_approval_email(queue_data: dict) -> bool:
    date_str = queue_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    posts_count = len(queue_data.get("posts", []))
    subject = f"[Action Required] Daily X Post Approval ({posts_count} Posts) - {date_str}"
    
    html_content = generate_approval_email_html(queue_data)
    return send_email(subject, html_content)

def send_email(subject: str, html_body: str, plain_text: str = "") -> bool:
    if not (SMTP_USER and SMTP_PASS):
        print(f"[Email Error] Missing SMTP credentials (USER: {bool(SMTP_USER)}, PASS: {bool(SMTP_PASS)}).")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Zubair Ahmad <{SMTP_USER}>"
        msg["To"] = USER_EMAIL
        msg["Reply-To"] = SMTP_USER

        if not plain_text:
            plain_text = "Daily X Urdu Posts Queue is ready. Reply 'Approved' to schedule all 7 posts."

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [USER_EMAIL], msg.as_string())

        print(f"Dispatched email to {USER_EMAIL} with subject: {subject}")
        return True
    except Exception as e:
        print(f"[Email Error] Failed to send email: {e}")
        return False
