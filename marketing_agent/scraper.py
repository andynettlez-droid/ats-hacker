import json
import os
import time
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TARGET_SUBREDDITS = ["resumes", "jobs", "recruitinghell"]
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
    # IMPORTANT: Replies must be genuinely helpful FIRST and transparently disclose
    # that you built the tool. Covert/undisclosed promotion violates Reddit's
    # self-promotion rules and FTC endorsement guidance, and gets accounts + the
    # domain banned. Only post where the subreddit's rules permit self-promotion,
    # and prefer leading with real value over the plug.
    prompt = f"""
    You are the software engineer who built a $5 tool called 'ATS Hacker'.
    A Reddit user is frustrated about their job search.
    Their post title: {post_title}
    Their post body: {post_body}

    Draft a reply that is genuinely helpful and honest. Requirements:
    - Lead with empathy and TWO concrete, actionable pieces of resume/ATS advice the
      person can use even if they never touch your tool.
    - Clearly DISCLOSE that you built the tool. Use plain language such as:
      "Full disclosure, I built a small $5 tool called ATS Hacker that..." 
    - The mention should be a soft, optional offer, not a hard sell.
    - Do NOT pretend to be a neutral, uninvolved user. Do NOT hide the commercial interest.
    - Keep it under 5 sentences and sound like a real person, not a marketer.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

def run_scraper():
    print("[*] Starting ATS Hacker lead finder (DEMO MODE: using sample posts)...")
    drafts = load_drafts()
    processed_ids = [d["post_id"] for d in drafts]

    # DEMO MODE NOTE:
    # The posts below are hardcoded samples so you can exercise the drafting engine
    # without hitting Reddit. To find real leads, use Reddit's official API via PRAW
    # with the credentials in .env (REDDIT_CLIENT_ID/SECRET/USERNAME/PASSWORD) and
    # respect each subreddit's self-promotion rules and rate limits. Do not scrape
    # Reddit in ways that violate its API Terms or robots restrictions.
    mocked_posts = [
        {
            "id": "mock_123",
            "title": "I've applied to 400 jobs and haven't gotten a single interview. Is my resume getting rejected by the ATS?",
            "selftext": "I'm a software engineer with 4 years of experience. I feel like my resume is just going into a black hole. Is workday automatically throwing it out?",
            "permalink": "/r/resumes/comments/mock_123"
        },
        {
            "id": "mock_456",
            "title": "Not getting interviews, resume help please",
            "selftext": "I tailor my resume to every single job, but I just get automated rejection emails the next day. Help!",
            "permalink": "/r/jobs/comments/mock_456"
        }
    ]

    for post in mocked_posts:
        post_id = post['id']
        title = post['title']
        selftext = post['selftext']
        url = f"https://www.reddit.com{post['permalink']}"
        
        if post_id in processed_ids:
            continue
            
        text_to_search = (title + " " + selftext).lower()
        if any(kw in text_to_search for kw in KEYWORDS):
            print(f"[+] Found match: {title}")
            print("    -> Sending to OpenAI to draft empathetic reply...")
            draft_text = generate_reply(title, selftext)
            
            drafts.append({
                "post_id": post_id,
                "title": title,
                "url": url,
                "draft_reply": draft_text,
                "status": "pending"
            })
            save_drafts(drafts)
            processed_ids.append(post_id)
            print(f"    -> Draft generated and saved.")
            
        time.sleep(1) # Be polite

    print("[*] Scrape complete. Run `python dashboard.py` to review and post drafts!")

if __name__ == "__main__":
    run_scraper()
