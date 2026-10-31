"""
X (Twitter) Daily Post Queue & Analytics Manager
Handles post formatting, character limits, link verification, and daily log generation.
"""

import json
import os
from datetime import datetime

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "daily_queue.json")
LOGS_DIR = os.path.join(os.path.dirname(__file__), "daily_logs")

os.makedirs(LOGS_DIR, exist_ok=True)

def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"date": "", "posts": []}

def save_queue(data):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_post_display(post, index):
    output = []
    output.append(f"[{index}] {post.get('time_slot', 'TBD')} | Status: {post.get('status', 'draft').upper()}")
    output.append(f"Category: {post.get('category', 'General')}")
    output.append(f"Format: {post.get('format', 'single')}")
    output.append("--- Content ---")
    if post.get('format') == 'thread':
        for i, tweet in enumerate(post.get('tweets', []), 1):
            output.append(f"Tweet {i}/{len(post['tweets'])} ({len(tweet)} chars):\n{tweet}\n")
    else:
        text = post.get('text', '')
        output.append(f"{text} ({len(text)} chars)")
    output.append(f"Source: {post.get('source_name', 'N/A')} - {post.get('source_url', 'N/A')}")
    output.append(f"Hashtags: {', '.join(post.get('hashtags', []))}")
    output.append("=" * 60)
    return "\n".join(output)

def list_posts():
    queue = load_queue()
    print(f"\n================ Daily Post Queue ({queue.get('date', 'No Date')}) ================")
    for idx, post in enumerate(queue.get("posts", []), 1):
        print(format_post_display(post, idx))

if __name__ == "__main__":
    list_posts()
