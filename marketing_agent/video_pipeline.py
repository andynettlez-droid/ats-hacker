import os
import json
import time
import sys
import argparse
import re
import requests
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI

# Load env variables
# Locate .env in same directory
base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path)

# Initialize OpenAI Client
openai_key = os.getenv("OPENAI_API_KEY")
# If it's a placeholder, treat it as empty
if openai_key == "sk-proj-your_openai_api_key_here":
    openai_key = ""

openai_client = OpenAI(api_key=openai_key) if openai_key else None

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
if HEYGEN_API_KEY == "your_heygen_api_key_here":
    HEYGEN_API_KEY = ""

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
if ELEVENLABS_API_KEY == "your_elevenlabs_api_key_here":
    ELEVENLABS_API_KEY = ""
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

# Defaults
DEFAULT_AVATAR_ID = os.getenv("HEYGEN_AVATAR_ID", "74dd6e182f0d415ab740c1097d49304b")
DEFAULT_VOICE_ID = os.getenv("HEYGEN_VOICE_ID", "16a09e4706f74997ba4ed05ea11470f6")

REMOTION_DIR = os.path.abspath(os.path.join(base_dir, "../marketing/remotion"))
PUBLIC_DIR = os.path.join(REMOTION_DIR, "public")
OUT_DIR = os.path.join(REMOTION_DIR, "out")
RUNS_DIR = os.path.join(base_dir, "runs")
AUDIO_DIR = os.path.join(PUBLIC_DIR, "audio")

# Ensure target directories exist
os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(RUNS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

SAFE_DEFAULT_PROPS = {
    "hook1": "Resume not surfacing?",
    "hook2": "Check the match.",
    "subline": "Recruiters search and rank resumes by job-description language.",
    "beforeScore": 34,
    "afterScore": 91,
    "missing": ["SQL", "workflow automation", "stakeholder reporting", "metrics"],
    "cta": "Get your score free. Link in bio",
    "voiceover_text": "Your resume can look qualified and still be hard to find. Recruiters search for job-specific language. Signal by ATSHacker reads the role, spots missing keywords and proof points, then helps rewrite your bullets around what you actually did. No fake experience. Just a clearer match.",
}

VIRAL_SIGNAL_PROPS = {
    "hook1": "Resume invisible?",
    "hook2": "Check the match.",
    "subline": "Recruiters search resumes by job-description language before deeper review.",
    "beforeScore": 38,
    "afterScore": 91,
    "missing": ["SQL", "workflow automation", "stakeholder reporting", "metrics"],
    "cta": "Check your score free. Link in bio",
    "voiceover_text": "Your resume can look qualified and still be hard to find. Recruiters search for job-specific language. Signal by ATSHacker reads the role, spots missing keywords and proof points, then helps rewrite your bullets around what you actually did. No fake experience. Just a clearer match.",
}

STUDIO_BREAKTHROUGH_PROPS = {
    "hook1": "Your resume has to pass through filters.",
    "hook2": "Signal clears the path.",
    "subline": "Company searches reward clear role language, measurable proof, and clean structure.",
    "beforeScore": 38,
    "afterScore": 92,
    "missing": ["SQL", "workflow automation", "stakeholder reporting", "cloud delivery"],
    "cta": "Check your score free. Link in bio",
    "voiceover_text": "Your resume is not broken. It is trying to pass through company filters before a recruiter opens it. Signal reads the job, finds the missing role language, rebuilds your real proof, and phases the resume into the hiring manager screen. No fake experience. Just a clearer match.",
    "musicSrc": "audio/signal-studio-bed.mp3",
    "musicVolume": 0.18,
    "voiceoverSrc": "audio/signal-studio-voiceover.mp3",
    "voiceoverVolume": 0.92,
    "sfxSrc": "audio/signal-studio-sfx.mp3",
    "sfxVolume": 0.07,
    "avatarVideoUrl": "avatar.mp4",
    "avatarStartFrame": 0,
    "avatarEndFrame": 132,
    "avatarLabel": "Career coach",
}

RESUME_CRIME_SCENE_PROPS = {
    "hook": "This resume got a 34/100.",
    "subhook": "The person was actually qualified.",
    "resumeTitle": "Marketing Specialist Resume",
    "jobTitle": "Demand Generation Manager",
    "jobKeywords": ["Demand Gen", "LinkedIn Ads", "HubSpot", "CAC analysis"],
    "weakBullets": [
        "Responsible for social media.",
        "Helped with marketing campaigns.",
        "Worked with the team.",
    ],
    "beforeBullet": "Helped with marketing campaigns.",
    "afterBullet": "Cut CAC by 32% through LinkedIn Ads audience segmentation and HubSpot lead scoring.",
    "beforeScore": 34,
    "afterScore": 92,
    "cta": "Paste the job description. Check your free Signal score before you apply.",
    "voiceover_text": "This resume looks fine, which is exactly the problem. The job description asks for demand gen, LinkedIn Ads, HubSpot, and CAC analysis. But the resume says helped with campaigns. That is not bad experience. It is invisible experience. Same person. Same work. Better signal. Before, 34 out of 100. After, 92.",
    "musicSrc": "audio/signal-studio-bed.mp3",
    "musicVolume": 0.16,
    "voiceoverSrc": "audio/signal-studio-voiceover.mp3",
    "voiceoverVolume": 0.94,
    "sfxSrc": "audio/signal-studio-sfx.mp3",
    "sfxVolume": 0.06,
    "avatarLabel": "Recruiter review",
}

CLAIM_SAFETY_PATTERNS = [
    (re.compile(r"\bauto[-\s]?reject(?:ed|s|ion)?\b", re.IGNORECASE), "Avoid claiming an ATS auto-rejects candidates."),
    (re.compile(r"\bbeat(?:ing)?\s+(?:the\s+)?(?:bots?|ats)\b", re.IGNORECASE), "Avoid adversarial 'beat the ATS/bots' framing."),
    (re.compile(r"\bguarantee[ds]?\b|\bwill\s+land\b|\bland\s+your\s+dream\b", re.IGNORECASE), "Avoid outcome guarantees."),
    (re.compile(r"\b\d+x\s+(?:more\s+)?callbacks?\b", re.IGNORECASE), "Avoid unsupported callback multipliers."),
    (re.compile(r"\b100%\s+(?:ats\s+)?compatible\b", re.IGNORECASE), "Avoid absolute compatibility claims."),
]


def find_claim_safety_issues(payload):
    """Return claim-safety issues for generated marketing text."""
    issues = []
    if not isinstance(payload, dict):
        return [{"field": "payload", "reason": "Payload must be a JSON object."}]

    for field, value in payload.items():
        if isinstance(value, str):
            for pattern, reason in CLAIM_SAFETY_PATTERNS:
                if pattern.search(value):
                    issues.append({"field": field, "reason": reason})
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if not isinstance(item, str):
                    continue
                for pattern, reason in CLAIM_SAFETY_PATTERNS:
                    if pattern.search(item):
                        issues.append({"field": f"{field}[{idx}]", "reason": reason})
    return issues


def normalize_video_props(raw_props, topic=""):
    """Coerce generated props into the contract Remotion and the queue expect."""
    props = dict(SAFE_DEFAULT_PROPS)
    if isinstance(raw_props, dict):
        props.update(raw_props)

    for field in ("hook1", "hook2", "subline", "cta", "voiceover_text"):
        props[field] = str(props.get(field, SAFE_DEFAULT_PROPS[field])).strip()

    props["hook1"] = props["hook1"][:60] or SAFE_DEFAULT_PROPS["hook1"]
    props["hook2"] = props["hook2"][:80] or SAFE_DEFAULT_PROPS["hook2"]
    props["subline"] = props["subline"][:180] or SAFE_DEFAULT_PROPS["subline"]
    props["cta"] = props["cta"][:90] or SAFE_DEFAULT_PROPS["cta"]
    props["voiceover_text"] = props["voiceover_text"][:700] or SAFE_DEFAULT_PROPS["voiceover_text"]

    try:
        props["beforeScore"] = max(0, min(100, int(props.get("beforeScore", SAFE_DEFAULT_PROPS["beforeScore"]))))
    except (TypeError, ValueError):
        props["beforeScore"] = SAFE_DEFAULT_PROPS["beforeScore"]

    try:
        props["afterScore"] = max(0, min(100, int(props.get("afterScore", SAFE_DEFAULT_PROPS["afterScore"]))))
    except (TypeError, ValueError):
        props["afterScore"] = SAFE_DEFAULT_PROPS["afterScore"]

    if props["afterScore"] <= props["beforeScore"]:
        props["afterScore"] = min(100, max(75, props["beforeScore"] + 20))

    missing = props.get("missing")
    if not isinstance(missing, list):
        missing = SAFE_DEFAULT_PROPS["missing"]
    props["missing"] = [str(item).strip()[:40] for item in missing if str(item).strip()][:6]
    if not props["missing"]:
        props["missing"] = list(SAFE_DEFAULT_PROPS["missing"])

    issues = find_claim_safety_issues(props)
    if issues:
        issue_text = "; ".join(f"{i['field']}: {i['reason']}" for i in issues)
        raise ValueError(f"Claim safety check failed for topic '{topic}': {issue_text}")

    return props


def safe_slug(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "video"


def write_run_manifest(props, composition, status, output_file=None, run_dir=None):
    """Persist a bounded audit trail for each video generation run."""
    if run_dir is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = os.path.join(RUNS_DIR, f"{stamp}-{safe_slug(composition)}-{safe_slug(props.get('hook1', 'video'))}")
        os.makedirs(run_dir, exist_ok=True)

    manifest = {
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "composition": composition,
        "status": status,
        "outputFile": output_file,
        "claimSafetyIssues": find_claim_safety_issues(props),
        "props": props,
    }
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(run_dir, "props.json"), "w", encoding="utf-8") as f:
        json.dump(props, f, indent=2)
    print(f"[+] Run manifest written: {run_dir}")
    return run_dir


def public_audio_ref(filename):
    return f"audio/{filename}"


def elevenlabs_request(url, payload, dest_path, timeout=90):
    """Generate an audio asset with ElevenLabs and write it to Remotion public/audio."""
    if not ELEVENLABS_API_KEY:
        return False

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(response.content)
    if os.path.getsize(dest_path) < 1024:
        raise RuntimeError(f"ElevenLabs output is too small: {dest_path}")
    return True


def generate_elevenlabs_tts(text, dest_name="signal-studio-voiceover.mp3"):
    """Generate studio voiceover through ElevenLabs TTS."""
    dest_path = os.path.join(AUDIO_DIR, dest_name)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": {
            "stability": 0.48,
            "similarity_boost": 0.82,
            "style": 0.28,
            "use_speaker_boost": True,
        },
    }
    print("[*] Generating ElevenLabs studio voiceover...")
    elevenlabs_request(url, payload, dest_path)
    print(f"[+] Voiceover saved: {dest_path}")
    return public_audio_ref(dest_name)


def generate_elevenlabs_sound(prompt, dest_name, duration_seconds=30, prompt_influence=0.45):
    """Generate a quiet music bed or subtle SFX asset through ElevenLabs sound generation."""
    dest_path = os.path.join(AUDIO_DIR, dest_name)
    url = "https://api.elevenlabs.io/v1/sound-generation"
    payload = {
        "text": prompt,
        "duration_seconds": duration_seconds,
        "prompt_influence": prompt_influence,
    }
    print(f"[*] Generating ElevenLabs audio asset: {dest_name}")
    elevenlabs_request(url, payload, dest_path, timeout=120)
    print(f"[+] Audio asset saved: {dest_path}")
    return public_audio_ref(dest_name)


def prepare_studio_audio(props, force=False):
    """
    Add ElevenLabs-generated voice, quiet music bed, and restrained SFX to props.
    Falls back to the existing quiet orbit bed if ElevenLabs credentials are not present.
    """
    if not ELEVENLABS_API_KEY:
        print("[!] ElevenLabs API key missing. Using existing quiet music bed; no generated voiceover/SFX.")
        props["musicSrc"] = props.get("musicSrc") if os.path.exists(os.path.join(PUBLIC_DIR, props.get("musicSrc", ""))) else "audio/signal-quiet-orbit.wav"
        props["musicVolume"] = min(float(props.get("musicVolume", 0.2)), 0.22)
        props.pop("voiceoverSrc", None)
        props.pop("sfxSrc", None)
        return props

    voice_name = "signal-studio-voiceover.mp3"
    bed_name = "signal-studio-bed.mp3"
    sfx_name = "signal-studio-sfx.mp3"
    voice_path = os.path.join(AUDIO_DIR, voice_name)
    bed_path = os.path.join(AUDIO_DIR, bed_name)
    sfx_path = os.path.join(AUDIO_DIR, sfx_name)

    if force or not os.path.exists(voice_path):
        props["voiceoverSrc"] = generate_elevenlabs_tts(props["voiceover_text"], voice_name)
    else:
        props["voiceoverSrc"] = public_audio_ref(voice_name)

    if force or not os.path.exists(bed_path):
        props["musicSrc"] = generate_elevenlabs_sound(
            "A quiet premium cinematic electronic underscore for a career technology ad. Confident, futuristic, restrained, warm low pulse, subtle shimmer, no drums louder than the voice, no harsh whooshes.",
            bed_name,
            duration_seconds=30,
            prompt_influence=0.35,
        )
    else:
        props["musicSrc"] = public_audio_ref(bed_name)

    if force or not os.path.exists(sfx_path):
        props["sfxSrc"] = generate_elevenlabs_sound(
            "Very subtle sci-fi signal pulse and soft glass barrier dissolve. Premium, quiet, non-annoying, no cartoon sounds, no loud impacts.",
            sfx_name,
            duration_seconds=26,
            prompt_influence=0.52,
        )
    else:
        props["sfxSrc"] = public_audio_ref(sfx_name)

    props["musicVolume"] = min(float(props.get("musicVolume", 0.18)), 0.22)
    props["voiceoverVolume"] = min(float(props.get("voiceoverVolume", 0.92)), 0.96)
    props["sfxVolume"] = min(float(props.get("sfxVolume", 0.07)), 0.1)
    return props

def generate_script(topic):
    """
    Generate the voiceover script and Remotion props from GPT-4o.
    """
    if not openai_client:
        print("[!] OpenAI Client not initialized (missing API key). Using mock values.")
        return get_mock_props(topic)

    prompt = f"""
    You are an expert short-form product educator making a trustworthy vertical video for 'Signal by ATS Hacker',
    a one-time resume matching tool that helps job seekers align real experience with language recruiters search for in Applicant Tracking Systems (ATS).

    Topic: {topic}

    Generate the script and rendering props for a 20-second vertical video (TikTok/Reels/Shorts format).
    Keep claims careful: do not say ATS software auto-rejects candidates, do not promise callbacks or jobs,
    and do not invent facts about a candidate's background.
    The response MUST be a JSON object with these fields (and nothing else):
    - "hook1": A strong 2-4 word hook text displayed at start (e.g. "Resume not surfacing?")
    - "hook2": A punchy secondary line (e.g. "Keywords are missing.")
    - "subline": A short explanatory sentence showing the pain (e.g. "Recruiters search resumes by keyword. Weak match = lower visibility.")
    - "beforeScore": An integer starting score (typically between 20 and 45) representing the bad resume match.
    - "afterScore": An integer target score (typically between 85 and 98) representing the optimized resume match.
    - "missing": A list of 3-4 keywords that were missing from the resume (e.g., ["Agile", "KPIs", "stakeholder"]).
    - "cta": A strong call-to-action line (e.g., "Check your score free. Link in bio")
    - "voiceover_text": The literal script spoken by the AI avatar. Keep it under 65 words so it can be spoken in under 20 seconds. It should be punchy, empathetic, and drive users to the link in bio.
    """

    print("[*] Generating video script and properties via OpenAI GPT-4o...")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=300
        )
        data = normalize_video_props(json.loads(response.choices[0].message.content.strip()), topic)
        print(f"[+] Script generated successfully!\n    Voiceover: \"{data.get('voiceover_text')}\"")
        return data
    except Exception as e:
        print(f"[-] OpenAI script generation failed: {e}. Falling back to mocks.")
        return get_mock_props(topic)

def get_mock_props(topic):
    """Fallback mock properties if API keys are missing or calls fail."""
    props = dict(SAFE_DEFAULT_PROPS)
    return normalize_video_props(props, topic)

def request_heygen_avatar(script_text, avatar_id, voice_id):
    """
    Submits a video generation task to HeyGen's API and returns the video ID.
    """
    if not HEYGEN_API_KEY:
        print("[!] HeyGen API key not found. Mocking download step.")
        return None

    url = "https://api.heygen.com/v3/videos"
    headers = {
        "x-api-key": HEYGEN_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "type": "avatar",
        "avatar_id": avatar_id,
        "script": script_text,
        "voice_id": voice_id,
        "aspect_ratio": "9:16",
        "resolution": "1080p"
    }

    print(f"[*] Contacting HeyGen API to generate avatar video...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        res_data = response.json()

        # Check standard v3 format structure
        video_id = res_data.get("data", {}).get("video_id") or res_data.get("video_id")
        if not video_id:
            print(f"[-] HeyGen response lacked video_id: {res_data}")
            return None

        print(f"[+] HeyGen video generation request submitted! Video ID: {video_id}")
        return video_id
    except Exception as e:
        print(f"[-] HeyGen request failed: {e}")
        return None

def poll_heygen_and_download(video_id):
    """
    Polls the HeyGen API until the video completes, then downloads the MP4 to the public directory.
    """
    if not video_id or not HEYGEN_API_KEY:
        return mock_avatar_download()

    url = f"https://api.heygen.com/v3/videos/{video_id}"
    headers = {
        "x-api-key": HEYGEN_API_KEY,
        "accept": "application/json"
    }

    print(f"[*] Starting polling for HeyGen video completion...")
    max_attempts = 60  # ~10 minutes
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        time.sleep(10)

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json().get("data", {})
            status = data.get("status")

            print(f"    -> Attempt {attempt}/{max_attempts}: Status is '{status}'")

            if status == "completed":
                video_url = data.get("video_url")
                if not video_url:
                    print("[-] Error: Status completed but no video_url was found.")
                    return False

                print(f"[+] Video ready! Downloading from: {video_url}")
                download_video(video_url)
                return True
            elif status == "failed":
                print(f"[-] Video generation failed on HeyGen side: {data.get('error')}")
                return False
        except Exception as e:
            print(f"[!] Polling network issue: {e}. Retrying...")

    print("[-] HeyGen polling timed out.")
    return False

def download_video(url):
    """Downloads files from a remote URL to public/avatar.mp4."""
    dest = os.path.join(PUBLIC_DIR, "avatar.mp4")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[+] Downloaded avatar to: {dest}")
    except Exception as e:
        print(f"[-] Failed to download video: {e}")

def mock_avatar_download():
    """Generates a mock avatar file in the Remotion public directory by copying an existing asset."""
    dest = os.path.join(PUBLIC_DIR, "avatar.mp4")
    if os.path.exists(dest):
        print(f"[!] API Mocking: Reusing existing avatar at {dest}")
        return True

    # Try copying an existing B-roll video to use as a placeholder
    possible_sources = [
        os.path.join(base_dir, "../marketing/autopost/videos/ad-desk.mp4"),
        os.path.join(REMOTION_DIR, "public/bg.mp4"),
        os.path.join(REMOTION_DIR, "public/bg2.mp4")
    ]

    source = None
    for p in possible_sources:
        if os.path.exists(p):
            source = p
            break

    if source:
        print(f"[!] API Mocking: Copying dummy video from {source} to {dest}")
        import shutil
        shutil.copyfile(source, dest)
        return True
    else:
        # Create a tiny dummy text/video file if no files exist
        print(f"[!] Warning: No sample video found to mock with. Writing a dummy text file at {dest}")
        with open(dest, "w") as f:
            f.write("DUMMY VIDEO DATA")
        return True

def run_remotion_render(props, composition="AvatarReveal", run_dir=None):
    """
    Writes props to temp_props.json and executes the Remotion render CLI command.
    """
    targets = {
        "AvatarReveal": ("autonomous_reveal.mp4", "autonomous-ad.mp4"),
        "SignalReveal": ("signal_reveal.mp4", "signal-reveal.mp4"),
        "SignalBreakthroughAd": ("signal_filter_breakthrough_studio.mp4", "signal-filter-breakthrough-studio.mp4"),
        "ResumeCrimeScene": ("resume_crime_scene_demand_gen.mp4", "resume-crime-scene-demand-gen.mp4"),
    }
    if composition not in targets:
        raise ValueError(f"Unsupported composition: {composition}")

    # Write props to target folder
    temp_props_path = os.path.join(REMOTION_DIR, "temp_props.json")
    with open(temp_props_path, "w") as f:
        json.dump(props, f, indent=4)

    print(f"[*] Render props written to: {temp_props_path}")

    out_name, dest_name = targets[composition]

    # Run command
    if sys.platform == "win32":
        command = f"node node_modules/@remotion/cli/remotion-cli.js render {composition} out/{out_name} --props=temp_props.json"
    else:
        command = f"npx remotion render {composition} out/{out_name} --props=temp_props.json"
    print(f"[*] Executing Remotion Render in {REMOTION_DIR}...")
    print(f"    Command: {command}")

    try:
        # Use shell=True for windows .cmd command resolution
        process = subprocess.run(
            command,
            cwd=REMOTION_DIR,
            shell=True,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        print(f"[+] Video rendered successfully! Output: marketing/remotion/out/{out_name}")
        output_file = os.path.join(OUT_DIR, out_name)
        if not os.path.exists(output_file) or os.path.getsize(output_file) < 1024:
            raise RuntimeError(f"Rendered output is missing or too small: {output_file}")
        write_run_manifest(props, composition, "rendered", output_file=output_file, run_dir=run_dir)

        # Copy to autopost queue
        dest_queue = os.path.abspath(os.path.join(base_dir, f"../marketing/autopost/videos/{dest_name}"))
        os.makedirs(os.path.dirname(dest_queue), exist_ok=True)
        import shutil
        shutil.copyfile(output_file, dest_queue)
        print(f"[+] Output copied to queue: {dest_queue}")

        # Update posts.json queue
        update_autopost_queue(props, dest_name)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Remotion rendering failed: {e}")
        write_run_manifest(props, composition, "render_failed", run_dir=run_dir)
        return False
    except RuntimeError as e:
        print(f"[-] Remotion output QA failed: {e}")
        write_run_manifest(props, composition, "qa_failed", run_dir=run_dir)
        return False
    finally:
        # Cleanup temp props
        if os.path.exists(temp_props_path):
            os.remove(temp_props_path)

def build_queue_caption(props):
    caption = f"{props.get('hook1', '')} {props.get('hook2', '')} Match the job language. Free score, link in bio #jobsearch".strip()
    if len(caption) > 220:
        caption = "Resume not surfacing? Match the job language. Free score, link in bio #jobsearch"

    if find_claim_safety_issues({"caption": caption}):
        caption = "Resume not surfacing? Match the job language. Free score, link in bio #jobsearch"

    return caption


def update_autopost_queue(props, video_file_name="autonomous-ad.mp4"):
    """Registers the new video in posts.json for marketing agent publishing."""
    queue_path = os.path.abspath(os.path.join(base_dir, "../marketing/autopost/posts.json"))
    posts = []
    if os.path.exists(queue_path):
        try:
            with open(queue_path, "r", encoding="utf-8") as f:
                posts = json.load(f)
        except Exception:
            posts = []

    post_file = f"videos/{video_file_name}"

    # Avoid duplicates
    if not any(p.get("file") == post_file for p in posts):
        caption = build_queue_caption(props)

        posts.append({
            "title": props.get("hook1", "Signal resume match check")[:96],
            "caption": caption,
            "file": post_file,
            "platforms": ["tiktok", "instagram", "youtube"],
            "scheduleDate": time.strftime("%Y-%m-%dT16:00:00Z", time.gmtime(time.time() + 86400)),
            "status": "review_required"
        })
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=4)
        print(f"[+] Added video to marketing Queue at: {queue_path}")

def main():
    parser = argparse.ArgumentParser(description="Signal by ATSHacker Video Pipeline")
    parser.add_argument("--topic", type=str, default="Job seekers whose resumes are not surfacing in recruiter searches", help="Script topic")
    parser.add_argument("--avatar", type=str, default=DEFAULT_AVATAR_ID, help="HeyGen Avatar ID")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE_ID, help="HeyGen Voice ID")
    parser.add_argument("--mock-heygen", action="store_true", help="Skip HeyGen API call and download dummy video")
    parser.add_argument("--dry-run", action="store_true", help="Generate scripts/props and copy mock assets without rendering")
    parser.add_argument("--viral", action="store_true", help="Use the curated short-form Signal mascot viral ad preset")
    parser.add_argument("--signal", action="store_true", help="Generate the longer SignalReveal product explainer template")
    parser.add_argument("--studio-breakthrough", action="store_true", help="Generate the upgraded Signal filter-breakthrough ad with ElevenLabs audio and optional HeyGen avatar")
    parser.add_argument("--crime-scene", action="store_true", help="Generate a recruiter-reacts Resume Crime Scene teardown short")
    parser.add_argument("--force-audio", action="store_true", help="Regenerate ElevenLabs audio assets even when cached files exist")
    parser.add_argument("--capcut", action="store_true", help="Create a CapCut desktop project after rendering")

    args = parser.parse_args()

    if sum([args.viral, args.signal, args.studio_breakthrough, args.crime_scene]) > 1:
        parser.error("--viral, --signal, --studio-breakthrough, and --crime-scene target different templates; choose one.")

    print("=================================================================")
    print("[*] Starting Signal by ATSHacker video pipeline")
    print("=================================================================")

    # 1. Script Generation
    if args.crime_scene:
        print("[*] Resume Crime Scene mode active: recruiter-reacts teardown with resume markup and score reveal.")
        props = normalize_video_props(RESUME_CRIME_SCENE_PROPS, args.topic)
        if args.dry_run:
            print("[*] Dry-run option specified. Skipping ElevenLabs audio generation.")
        else:
            props = prepare_studio_audio(props, force=args.force_audio)
    elif args.studio_breakthrough:
        print("[*] Studio breakthrough mode active: using Signal mascot + company filter visual + studio audio props.")
        props = normalize_video_props(STUDIO_BREAKTHROUGH_PROPS, args.topic)
        if args.dry_run:
            print("[*] Dry-run option specified. Skipping ElevenLabs audio generation.")
        else:
            props = prepare_studio_audio(props, force=args.force_audio)
    elif args.viral:
        print("[*] Viral Signal mascot preset active: using curated short-form script and props.")
        props = normalize_video_props(VIRAL_SIGNAL_PROPS, args.topic)
    elif args.signal:
        print("[*] Signal reveal mode active: using predefined long-form script and props.")
        props = {
            "hook1": "Most resumes",
            "hook2": "may be missed.",
            "subline": "Recruiters search by keywords before they ever open a resume.",
            "beforeScore": 42,
            "afterScore": 94,
            "missing": ["SQL", "Leadership", "Customer Growth", "Product Strategy", "Automation", "Stakeholder Management"],
            "cta": "Signal by ATSHacker - match the job and get seen.",
            "voiceover_text": "Most resumes are not evaluated in a vacuum. They are searched, ranked, and reviewed against the words in the job description. Signal reads the role, finds the missing skills, keywords, structure, and proof, then rewrites your bullets without inventing experience. Formatting gets cleaner. Keywords align. Achievements become obvious. What is left is you, clearly matched to the job."
        }
        props = normalize_video_props(props, args.topic)
    else:
        props = generate_script(args.topic)

    # 2. HeyGen Avatar Video Generation
    avatar_ready = False
    optional_avatar_template = args.crime_scene or args.studio_breakthrough
    if args.dry_run:
        print("[*] Dry-run option specified. Skipping HeyGen and avatar file writes.")
    elif args.mock_heygen or not HEYGEN_API_KEY:
        if optional_avatar_template:
            print("[!] HeyGen unavailable or mock flag set. Omitting optional face-cam so the resume stays the hero.")
        else:
            print("[!] HeyGen API key missing or mock flag set. Mocking avatar.")
            avatar_ready = mock_avatar_download()
    else:
        video_id = request_heygen_avatar(props["voiceover_text"], args.avatar, args.voice)
        if video_id:
            success = poll_heygen_and_download(video_id)
            if not success:
                if optional_avatar_template:
                    print("[-] Failed generating video on HeyGen. Omitting optional face-cam.")
                else:
                    print("[-] Failed generating video on HeyGen. Falling back to mock avatar.")
                    avatar_ready = mock_avatar_download()
            else:
                avatar_ready = True
        else:
            if optional_avatar_template:
                print("[-] HeyGen request failed. Omitting optional face-cam.")
            else:
                print("[-] HeyGen request failed. Falling back to mock avatar.")
                avatar_ready = mock_avatar_download()

    # Add avatar URL/path to props for Remotion references
    if avatar_ready:
        props["avatarVideoUrl"] = "avatar.mp4"
    else:
        props.pop("avatarVideoUrl", None)

    composition = "ResumeCrimeScene" if args.crime_scene else "SignalBreakthroughAd" if args.studio_breakthrough else "SignalReveal" if args.signal else "AvatarReveal"
    out_names = {
        "AvatarReveal": "autonomous_reveal.mp4",
        "SignalReveal": "signal_reveal.mp4",
        "SignalBreakthroughAd": "signal_filter_breakthrough_studio.mp4",
        "ResumeCrimeScene": "resume_crime_scene_demand_gen.mp4",
    }
    out_name = out_names[composition]
    run_dir = write_run_manifest(props, composition, "props_ready")

    # 3. Compile/Render Video via Remotion
    if args.dry_run:
        print("[+] Dry-run option specified. Script & mock assets prepared.")
        write_run_manifest(props, composition, "dry_run", run_dir=run_dir)
        print(f"[+] Props saved in run folder: {run_dir}")
        print("[*] Dry run completed successfully.")
    else:
        success = run_remotion_render(props, composition=composition, run_dir=run_dir)
        if success and args.capcut:
            from capcut_exporter import export_to_capcut
            video_out_path = os.path.join(OUT_DIR, out_name)
            export_to_capcut(
                video_path=video_out_path,
                voiceover_text=props["voiceover_text"],
                project_name="signal-reveal" if args.signal else "ats-hacker-viral-ad",
                props=props,
                auto_launch=True
            )

if __name__ == "__main__":
    main()
