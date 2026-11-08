@echo off
cd /d "c:\Users\DELL\Desktop\automation\Xpost"
git fetch origin main --quiet
git checkout origin/main -- daily_queue.json 2>nul
git pull origin main --quiet
"C:\Users\DELL\AppData\Local\Programs\Python\Python311\python.exe" daily_engine.py --action auto >> local_watchdog.log 2>&1
git diff --quiet daily_queue.json || (
    git add daily_queue.json
    git commit -m "chore: update post queue status (local) [skip ci]" --quiet
    git push origin main --quiet
)
