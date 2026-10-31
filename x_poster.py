"""
X (Twitter) Automated Poster via Playwright
Uses a persistent browser session so login persists via Google SSO without asking for passwords.
"""

import json
import os
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.path.dirname(__file__), "browser_session")
QUEUE_FILE = os.path.join(os.path.dirname(__file__), "daily_queue.json")

def post_tweet_to_x(text: str, headless: bool = False) -> bool:
    """
    Posts a single tweet or opening post to X using the persistent browser context.
    """
    print(f"\n[Poster] Preparing to post to X: {text[:60]}...")
    os.makedirs(SESSION_DIR, exist_ok=True)

    with sync_playwright() as p:
        # Launch with persistent context to retain Google/X cookies
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            channel="msedge",
            headless=headless,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = context.new_page()
        page.goto("https://x.com/compose/post", timeout=45000)
        time.sleep(4)

        # Check if login is required
        current_url = page.url
        if "login" in current_url or "i/flow/login" in current_url:
            print("[Poster] Session requires initial login.")
            print("[Poster] Please complete the 1-click 'Sign in with Google' in the opened browser window.")
            print("[Poster] Once logged in, your session will be permanently remembered for automatic posting.")
            # Wait up to 90 seconds for user to complete 1-click Google SSO
            for _ in range(30):
                time.sleep(3)
                if "login" not in page.url:
                    print("[Poster] Logged in successfully!")
                    break

        try:
            # Locate tweet composer input
            composer = page.wait_for_selector('div[data-testid="tweetTextarea_0"]', timeout=15000)
            if composer:
                composer.fill(text)
                time.sleep(2)

                # Click Post button
                post_button = page.wait_for_selector('button[data-testid="tweetButton"]', timeout=10000)
                if post_button and post_button.is_enabled():
                    post_button.click()
                    print("[Poster] Post button clicked successfully!")
                    time.sleep(5)
                    context.close()
                    return True
                else:
                    print("[Poster] Post button not active.")
        except Exception as e:
            print(f"[Poster Error]: {e}")
        finally:
            try:
                context.close()
            except Exception:
                pass

    return False

def post_next_due_post():
    if not os.path.exists(QUEUE_FILE):
        print(f"Queue file {QUEUE_FILE} not found.")
        return

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for post in data.get("posts", []):
        if post.get("status") == "ready":
            print(f"Posting {post['id']} ({post['time_slot']})...")
            text = post.get("text")
            if post.get("format") == "thread":
                text = post.get("tweets", [""])[0]

            success = post_tweet_to_x(text, headless=False)
            if success:
                post["status"] = "posted"
                post["posted_at"] = datetime.now().isoformat()
                with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"Successfully posted {post['id']}!")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--post-due":
        post_next_due_post()
    else:
        print("X Poster initialized. Run with --post-due to execute next scheduled post.")
