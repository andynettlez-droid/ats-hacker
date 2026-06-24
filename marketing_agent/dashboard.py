import json
import os
import praw
from dotenv import load_dotenv

load_dotenv()

# Initialize API Clients
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="ATS Hacker Marketing Agent v1.0",
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
)

DRAFTS_FILE = "drafts.json"

def load_drafts():
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_drafts(drafts):
    with open(DRAFTS_FILE, "w") as f:
        json.dump(drafts, f, indent=4)

def run_dashboard():
    print("========================================")
    print("🚀 ATS HACKER - MARKETING DASHBOARD 🚀")
    print("========================================")
    
    drafts = load_drafts()
    pending_drafts = [d for d in drafts if d["status"] == "pending"]
    
    if not pending_drafts:
        print("[*] No pending drafts to review. Run scraper.py to find leads.")
        return

    print(f"[*] Found {len(pending_drafts)} leads ready for your review.\n")
    
    for draft in pending_drafts:
        print(f"📌 POST TITLE: {draft['title']}")
        print(f"🔗 URL: {draft['url']}")
        print(f"\n🤖 DRAFTED REPLY:\n{draft['draft_reply']}\n")
        
        choice = input("Do you want to post this? (y = yes, n = skip/reject, q = quit): ").strip().lower()
        
        if choice == 'y':
            try:
                submission = reddit.submission(id=draft["post_id"])
                submission.reply(draft["draft_reply"])
                print("[+] Successfully posted to Reddit!")
                draft["status"] = "posted"
            except Exception as e:
                print(f"[!] Error posting: {e}")
                draft["status"] = "error"
        elif choice == 'q':
            break
        else:
            print("[-] Draft rejected.")
            draft["status"] = "rejected"
            
        print("-" * 40)
        
    # Save the updated statuses
    save_drafts(drafts)
    print("[*] Dashboard closed.")

if __name__ == "__main__":
    run_dashboard()
