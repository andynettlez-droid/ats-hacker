import json
import os
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
DRAFTS_FILE = "drafts.json"

def load_drafts():
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_drafts(drafts):
    with open(DRAFTS_FILE, "w") as f:
        json.dump(drafts, f, indent=4)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/drafts", methods=["GET"])
def get_drafts():
    drafts = load_drafts()
    pending = [d for d in drafts if d.get("status") == "pending"]
    return jsonify(pending)

@app.route("/api/drafts/update", methods=["POST"])
def update_draft():
    data = request.json
    post_id = data.get("post_id")
    new_status = data.get("status")
    
    drafts = load_drafts()
    for d in drafts:
        if d["post_id"] == post_id:
            d["status"] = new_status
            break
            
    save_drafts(drafts)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
