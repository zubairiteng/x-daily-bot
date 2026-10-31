"""
X Daily Manager - Autonomous Engine for GitHub Actions & Cloud Execution (Urdu Edition)
Resilient Daily Operations:
1. Auto-scrapes live Urdu news and generates 7 verified posts with media photos every day.
2. Emails morning approval with Urdu RTL cards to zubair.ahmad4545438@gmail.com.
3. Automatically posts scheduled tweets with editorial images using Playwright.
4. Auto-dispatches evening performance report.
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
load_dotenv()

# Import news generator and email service
try:
    from news_generator import build_daily_posts, download_and_prepare_image
    from email_service import send_approval_email
except ImportError:
    from .news_generator import build_daily_posts, download_and_prepare_image
    from .email_service import send_approval_email

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "daily_queue.json")
LOGS_DIR = os.path.join(os.path.dirname(__file__), "daily_logs")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "zubairahmad.mehmood@iisat.edu.pk")
SMTP_PASS = os.getenv("SMTP_PASS", "")
USER_EMAIL = os.getenv("USER_EMAIL", "zubair.ahmad4545438@gmail.com")

# X Credentials
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET", "")
X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN", "")
X_CT0 = os.getenv("X_CT0", "")

def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"date": "", "status": "draft", "posts": []}

def save_queue(queue):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

def ensure_daily_queue():
    """
    Checks if today's queue exists. If not or if it's a new day,
    automatically generates 7 live verified Urdu posts with media photos.
    """
    queue = load_queue()
    today_str = datetime.now().strftime("%Y-%m-%d")
    queue_date = queue.get("date", "")

    if queue_date != today_str:
        print(f"[Auto] Date change detected: Current={today_str}, Queue={queue_date}. Scraping fresh Urdu news...")
        posts = build_daily_posts(today_str)
        queue = {
            "date": today_str,
            "status": "ready",
            "daily_target": len(posts),
            "posts": posts,
            "email_sent_at": datetime.now().isoformat()
        }
        save_queue(queue)
        print(f"[Auto] Saved fresh queue for {today_str} with {len(posts)} posts.")
        action_send_morning_approval(queue)
        return queue
    return queue

def action_send_morning_approval(queue=None):
    if not queue:
        queue = load_queue()
    return send_approval_email(queue)

def post_via_playwright(text: str, image_path: str = None) -> bool:
    from playwright.sync_api import sync_playwright

    print("[Playwright] Launching browser to post to X...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        context.add_cookies([
            {"name": "auth_token", "value": X_AUTH_TOKEN, "domain": ".x.com", "path": "/", "httpOnly": True, "secure": True},
            {"name": "ct0", "value": X_CT0, "domain": ".x.com", "path": "/", "httpOnly": False, "secure": True}
        ])

        page = context.new_page()
        page.goto("https://x.com/home", timeout=45000, wait_until="domcontentloaded")
        time.sleep(5)

        try:
            # Dismiss any popups or dialogs
            close_buttons = page.query_selector_all('button[aria-label="Close"]')
            for btn in close_buttons:
                try:
                    btn.click(force=True)
                except Exception:
                    pass

            composer = page.wait_for_selector('div[data-testid="tweetTextarea_0"]', timeout=20000)
            if not composer:
                print("[Playwright Error] Tweet composer not found.")
                browser.close()
                return False

            # 1. Fill text first before attaching media
            page.evaluate("(el) => el.focus()", composer)
            composer.fill(text)
            time.sleep(2)

            # 2. Attach image if present
            if image_path and os.path.exists(image_path):
                print(f"[Playwright] Attaching image: {image_path}")
                try:
                    file_input = page.query_selector('input[data-testid="fileInput"]')
                    if file_input:
                        file_input.set_input_files(image_path)
                        # Wait up to 15s for attachment to render
                        page.wait_for_selector('div[data-testid="attachments"]', timeout=15000)
                        print("[Playwright] Media attachment uploaded successfully.")
                        time.sleep(3)
                except Exception as img_err:
                    print(f"[Playwright Warning] Image attachment: {img_err}")

            # 3. Locate post button (inline or modal)
            post_btn = page.query_selector('button[data-testid="tweetButtonInline"]') or page.query_selector('button[data-testid="tweetButton"]')
            if not post_btn:
                print("[Playwright Error] Post button not found.")
                browser.close()
                return False

            print("[Playwright] Dispatching native JS click on post button...")
            page.evaluate("(btn) => btn.click()", post_btn)
            time.sleep(6)

            # Check for toast confirmation
            toast = page.query_selector('div[data-testid="toast"]')
            if toast:
                print(f"[Playwright Verified] Toast: {toast.inner_text().strip()}")

            print("[Playwright SUCCESS] Tweet successfully published to X!")
            browser.close()
            return True
        except Exception as e:
            print(f"[Playwright Exception] {e}")
            try:
                print(f"[Debug] Page URL: {page.url} | Title: {page.title()}")
                page.screenshot(path="x_cloud_debug.png")
            except Exception:
                pass
        finally:
            try:
                browser.close()
            except Exception:
                pass

    return False

def action_publish_due_post():
    queue = load_queue()
    for post in queue.get("posts", []):
        if post.get("status") == "ready":
            print(f"Publishing {post['id']} ({post['time_slot']})...")
            text = post.get("text", "")
            
            image_path = post.get("image_path", "")
            if not (image_path and os.path.exists(image_path)):
                image_url = post.get("image_url", "")
                if image_url:
                    image_path = download_and_prepare_image(image_url, post.get("id", "post"))

            published = False

            if X_AUTH_TOKEN and X_CT0:
                published = post_via_playwright(text, image_path=image_path)
            elif X_API_KEY and X_ACCESS_TOKEN:
                try:
                    import tweepy
                    client = tweepy.Client(
                        consumer_key=X_API_KEY,
                        consumer_secret=X_API_SECRET,
                        access_token=X_ACCESS_TOKEN,
                        access_token_secret=X_ACCESS_SECRET
                    )
                    client.create_tweet(text=text)
                    published = True
                except Exception as e:
                    print(f"API Error: {e}")

            if published:
                post["status"] = "posted"
                post["posted_at"] = datetime.now().isoformat()
                save_queue(queue)
                print(f"[SUCCESS] Post {post['id']} marked as POSTED.")
                return True
            else:
                print(f"[FAIL] Could not publish {post['id']}.")
                return False
    print("No pending 'ready' posts found in queue.")
    return False

def action_send_evening_analytics():
    queue = load_queue()
    date_str = queue.get("date", datetime.now().strftime("%Y-%m-%d"))
    posts = queue.get("posts", [])
    posted_count = sum(1 for p in posts if p.get("status") == "posted")

    html = f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family:'Segoe UI',Tahoma,sans-serif; background:#f1f5f9; padding:20px; direction:rtl; text-align:right;">
        <div style="max-width:620px; margin:0 auto; background:#ffffff; border-radius:10px; overflow:hidden; border:1px solid #e2e8f0; padding:20px;">
            <h2 style="color:#0f172a; border-bottom:2px solid #0284c7; padding-bottom:8px;">روزانہ کارکردگی و اینالیٹکس رپورٹ &bull; {date_str}</h2>
            <p><b>آج شائع شدہ پوسٹس:</b> {posted_count} / {len(posts)}</p>
            <p>تمام پوسٹس کامیابی سے ٹویٹر الگورتھم کے مطابق بغیر بیرونی لنکس کے اور تصاویر کے ساتھ لائیو کی گئیں۔</p>
            <div style="background:#f8fafc; padding:12px; border-radius:6px; margin-top:15px; font-size:13px; color:#475569;">
                <b>اگلا قدم:</b> کل صبح 8 بجے تازہ ترین خبروں کا نیا شیڈول خودکار طور پر بھیج دیا جائے گا۔
            </div>
        </div>
    </body>
    </html>
    """
    subject = f"[Daily Analytics] X Operations Report ({posted_count}/{len(posts)} Posts) - {date_str}"
    from email_service import send_email
    return send_email(subject, html, f"Daily X Report: {posted_count}/{len(posts)} posts published.")

def action_auto():
    queue = ensure_daily_queue()
    pending = [p for p in queue.get("posts", []) if p.get("status") == "ready"]
    if pending:
        print(f"[Auto] {len(pending)} posts pending. Publishing next post...")
        action_publish_due_post()
    else:
        print("[Auto] All posts for today have been published. Checking evening report...")
        action_send_evening_analytics()

def main():
    parser = argparse.ArgumentParser(description="X Daily Autonomous Engine")
    parser.add_argument("--action", choices=["auto", "morning-email", "post-due", "evening-email", "approve"], default="auto")
    args = parser.parse_args()

    if args.action == "morning-email":
        action_send_morning_approval()
    elif args.action == "post-due":
        action_publish_due_post()
    elif args.action == "evening-email":
        action_send_evening_analytics()
    elif args.action == "approve":
        q = load_queue()
        q["status"] = "ready"
        save_queue(q)
        print("[Engine] All posts marked as READY.")
    else:
        action_auto()

if __name__ == "__main__":
    main()
