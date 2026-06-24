import json
import os
import time
from dotenv import load_dotenv
import praw
from openai import OpenAI

load_dotenv()

# Initialize API Clients
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="ATS Hacker Marketing Agent v1.0",
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TARGET_SUBREDDITS = "resumes+jobs+recruitinghell"
KEYWORDS = ["ats", "rejected", "workday", "resume help", "not getting interviews"]
DRAFTS_FILE = "drafts.json"

def load_drafts():
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_drafts(drafts):
    with open(DRAFTS_FILE, "w") as f:
        json.dump(drafts, f, indent=4)

def generate_reply(post_title, post_body):
    prompt = f"""
    You are an empathetic software engineer who built a $5 tool called 'ATS Hacker'. 
    A Reddit user is frustrated about their job search.
    Their post title: {post_title}
    Their post body: {post_body}
    
    Draft a highly empathetic, helpful, human-sounding reply. DO NOT sound like a bot or a marketer.
    Sympathize with their struggle, give them 1 piece of actual resume advice, and then mention:
    "If you think the ATS is filtering you out, I built a $5 script that forces your resume to semantically match the job description. Happy to send the link if you want to try it."
    Keep it under 4 sentences.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

def run_scraper():
    print(f"[*] Starting Reddit Scraper on r/{TARGET_SUBREDDITS}")
    subreddit = reddit.subreddit(TARGET_SUBREDDITS)
    drafts = load_drafts()
    processed_ids = [d["post_id"] for d in drafts]

    for submission in subreddit.new(limit=20):
        if submission.id in processed_ids:
            continue
            
        text_to_search = (submission.title + " " + submission.selftext).lower()
        if any(kw in text_to_search for kw in KEYWORDS):
            print(f"[+] Found match: {submission.title}")
            draft_text = generate_reply(submission.title, submission.selftext)
            
            drafts.append({
                "post_id": submission.id,
                "title": submission.title,
                "url": submission.url,
                "draft_reply": draft_text,
                "status": "pending"
            })
            save_drafts(drafts)
            print(f"    -> Draft generated and saved.")
            
    print("[*] Sleeping for 15 minutes...")

if __name__ == "__main__":
    # Run once for testing
    run_scraper()
