import json
import os
import webbrowser
import pyperclip

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
    print("=====================================================")
    print("[*] ATS HACKER - HUMAN-IN-THE-LOOP DASHBOARD [*]")
    print("=====================================================")
    
    drafts = load_drafts()
    pending_drafts = [d for d in drafts if d["status"] == "pending"]
    
    if not pending_drafts:
        print("[*] No pending drafts to review. Run scraper.py to find leads.")
        return

    print(f"[*] Found {len(pending_drafts)} leads ready for your review.\n")
    
    for draft in pending_drafts:
        print(f"[*] POST TITLE: {draft['title']}")
        print(f"[*] URL: {draft['url']}")
        print(f"\n[*] DRAFTED REPLY:\n{draft['draft_reply']}\n")
        
        choice = input("Do you want to post this? (y = open & copy, n = reject, q = quit): ").strip().lower()
        
        if choice == 'y':
            # Copy to clipboard
            try:
                pyperclip.copy(draft['draft_reply'])
                print("[+] AI Reply copied to your clipboard!")
            except Exception as e:
                print("[-] Could not copy to clipboard. Please copy it manually.")
                
            # Open browser
            print("[*] Opening Reddit in your browser... Paste the reply (Ctrl+V) and hit Comment!")
            webbrowser.open(draft['url'])
            
            # Ask if they actually posted it
            post_confirm = input("Did you successfully post the comment? (y/n): ").strip().lower()
            if post_confirm == 'y':
                draft["status"] = "posted"
                print("[+] Marked as posted.")
            else:
                print("[-] Left as pending.")
                
        elif choice == 'q':
            break
        else:
            print("[-] Draft rejected.")
            draft["status"] = "rejected"
            
        print("-" * 50)
        
    save_drafts(drafts)
    print("[*] Dashboard closed.")

if __name__ == "__main__":
    run_dashboard()
