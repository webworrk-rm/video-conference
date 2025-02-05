from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os

app = Flask(__name__)

# ✅ CORS Setup (Restrict if necessary)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ Daily.co API Configuration
dailyco_api_key = os.getenv("DAILY_CO_API_KEY", "YOUR_DAILY_CO_API_KEY")
dailyco_base_url = "https://api.daily.co/v1/rooms"

headers = {
    "Authorization": f"Bearer {dailyco_api_key}",
    "Content-Type": "application/json"
}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API is running!"}), 200

# ✅ API to create a private meeting with host approval
@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        print("✅ Received request to create a meeting")

        # Create a private meeting
        response = requests.post(dailyco_base_url, headers=headers, json={
            "privacy": "private",
            "properties": {
                "exp": 3600,  # Meeting expires in 1 hour
                "start_audio_off": True,
                "start_video_off": True,
                "enable_chat": True
            }
        })
        data = response.json()

        print("✅ Daily.co Response:", data)

        if "url" in data:
            meeting_url = data["url"]
            
            # Create host and participant tokens
            host_token = create_meeting_token(meeting_url, is_owner=True)
            participant_token = create_meeting_token(meeting_url, is_owner=False)

            if host_token and participant_token:
                host_url = f"{meeting_url}?t={host_token}"
                participant_url = f"{meeting_url}?t={participant_token}"

                print(f"✅ Meeting created: Host URL = {host_url}, Participant URL = {participant_url}")
                return jsonify({
                    "host_url": host_url,
                    "participant_url": participant_url
                }), 201
            else:
                return jsonify({"error": "Failed to generate meeting tokens"}), 500
        else:
            print("❌ ERROR: Daily.co API failed", data)
            return jsonify({"error": "Failed to create meeting", "details": data}), 500

    except Exception as e:
        print("❌ Create Meeting Error:", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ Function to generate expiring meeting tokens for host & participants
def create_meeting_token(meeting_url, is_owner=False):
    try:
        token_response = requests.post(f"https://api.daily.co/v1/meeting-tokens", headers=headers, json={
            "properties": {
                "room_name": meeting_url.split("/")[-1],
                "is_owner": is_owner  # True for host, False for participants
            }
        })
        token_data = token_response.json()
        return token_data.get("token")
    except Exception as e:
        print(f"❌ Token Generation Failed: {e}")
        return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
