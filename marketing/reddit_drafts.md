# Ethical Reddit Launch Drafts

**Hard Rule:** We will only post these if the subreddit rules explicitly allow self-promotion or side-project Saturday posts. We will be 100% transparent that we built this tool. No fake personas. No astroturfing.

---

## 1. r/resumes (Educational Focus)
**Title:** Why your 2-column resume is getting you auto-rejected (and a tool I built to fix it)

**Body:**
Hey r/resumes,

I've been analyzing how Workday, Greenhouse, and Taleo actually parse PDF resumes, and I see the same mistake happening constantly: 2-column layouts.

ATS parsers read left-to-right, top-to-bottom. If you have a left column with your skills and a right column with your experience, the ATS scrambles the text. It might read "Skill: JavaScript Company: Google Skill: Python Job Title: Engineer", which completely destroys your semantic match score, leading to an instant rejection.

**How to fix it manually:**
Switch to a strictly single-column, standard formatting. Put your skills at the top or bottom. Copy all the text from your PDF and paste it into a raw `.txt` file. If the text is out of order, the ATS will read it out of order too.

**My Tool (Full Disclosure):**
I got so frustrated with this that I built a tool called ATS Hacker (ats-hacker-swart.vercel.app). Instead of just checking your resume, you paste the exact job description you want, and it uses AI to literally rewrite your bullet points to match the exact semantics the ATS is looking for. It outputs a perfectly parsed, single-column PDF.

It costs $5.00 flat per resume. No recurring $30/month subscriptions. 

I'd love feedback from this community on the output quality. Happy to answer any questions about how ATS parsing actually works under the hood!

---

## 2. r/jobs (Pain-Point Focus)
**Title:** If you're getting rejected 5 minutes after applying, a human never saw your resume.

**Body:**
Hey r/jobs,

A lot of people here are frustrated by "instant rejections." I want to clarify what is actually happening on the backend. When you apply, the Applicant Tracking System (ATS) scans your resume against the Job Description. It looks for exact semantic overlap (e.g., if the JD says "cross-functional leadership" and your resume says "managed teams", you lose points). If your score falls below their threshold, you are automatically filtered out.

**How to beat it:**
You have to manually tailor *every single resume* to the specific job description. Mirror their exact language.

**What I built (Self Promo):**
Because tailoring 50 resumes a day is exhausting, I built ATS Hacker (ats-hacker-swart.vercel.app). You upload your PDF, paste the job description, and it rewrites your resume to hit every keyword perfectly. It's a flat $5.00. No subscriptions. 

Hopefully, this helps some of you get past the robot gatekeepers and into actual human interviews.

---

## 3. r/recruitinghell (Rant/Venting Focus)
**Title:** I got so sick of Workday auto-rejects that I built a robot to fight their robots.

**Body:**
We all know the pain. You spend 45 minutes re-typing your entire resume into Workday, and you get an automated rejection email 10 minutes later. The system is entirely broken, and corporate recruiters rely on automated filters that reject perfectly qualified candidates just because they used the wrong synonym.

**The Solution:**
If they are using robots to filter us out, we should use robots to get past them. I built a tool called ATS Hacker (ats-hacker-swart.vercel.app). 

You drop your resume in, paste the ridiculous job description they posted, and it automatically rewrites your bullet points to semantically match exactly what their ATS is programmed to look for. It spits out an ATS-compliant PDF for $5 bucks. 

I built this because I despise the current state of recruiting software, and I'm refusing to charge absurd $40/month subscriptions like the other resume scanners out there. 

Fight fire with fire. Let me know what you think.
