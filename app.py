from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os

app = Flask(__name__)

# ✅ Allow CORS for all origins (Modify if needed)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ Daily.co API Configuration
dailyco_api_key = os.getenv("DAILY_CO_API_KEY", "YOUR_DAILY_CO_API_KEY")
dailyco_base_url = "https://api.daily.co/v1/rooms"

headers = {
    "Authorization": f"Bearer {dailyco_api_key}",
    "Content-Type": "application/json"
}

# In-memory waiting list
waiting_list = {}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API is running!"}), 200

from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
import time  # ✅ Import time for timestamp management

app = Flask(__name__)

# ✅ CORS Setup (Allow if necessary)
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

# ✅ API to create a **PRIVATE** meeting with host control
@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        print("✅ Received request to create a meeting")

        # Get a future timestamp for meeting expiration (1 hour from now)
        future_timestamp = int(time.time()) + 3600

        # ✅ Create a **private** meeting with knocking (approval required)
        response = requests.post(dailyco_base_url, headers=headers, json={
            "privacy": "private",  # ✅ Private Meeting
            "properties": {
                "exp": future_timestamp,
                "enable_knocking": True,  # ✅ Participants must wait for approval
                "start_audio_off": True,
                "start_video_off": True,
                "enable_chat": True
            }
        })
        data = response.json()

        print("✅ Daily.co Response:", data)

        if "url" in data:
            meeting_url = data["url"]
            
            # ✅ Generate host and participant tokens
            host_token = create_meeting_token(meeting_url, is_owner=True, exp=future_timestamp)
            participant_token = create_meeting_token(meeting_url, is_owner=False, exp=future_timestamp)

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

# ✅ Function to generate a **secure meeting token**
def create_meeting_token(meeting_url, is_owner=False, exp=None):
    try:
        token_response = requests.post(f"https://api.daily.co/v1/meeting-tokens", headers=headers, json={
            "properties": {
                "room_name": meeting_url.split("/")[-1],
                "is_owner": is_owner,  # ✅ Only the host is the owner
                "exp": exp  # ✅ Ensure the token expires properly
            }
        })
        token_data = token_response.json()
        return token_data.get("token")
    except Exception as e:
        print(f"❌ Token Generation Failed: {e}")
        return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


# ✅ API to request to join a meeting (Participant requests admission)
@app.route("/api/request-join", methods=["POST"])
def request_join():
    try:
        data = request.json
        room_name = data.get("room_name")
        user_name = data.get("user_name")

        if room_name not in waiting_list:
            return jsonify({"error": "Room not found"}), 404

        user_request = {"user_name": user_name}
        waiting_list[room_name].append(user_request)

        print(f"🔔 Join request received: {user_name} for {room_name}")

        return jsonify({"message": "Request sent to host", "room_name": room_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API for host to get waiting list
@app.route("/api/waiting-list/<room_name>", methods=["GET"])
def get_waiting_list(room_name):
    try:
        if room_name not in waiting_list:
            return jsonify({"error": "Room not found"}), 404

        return jsonify({"waiting_list": waiting_list[room_name]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API for host to admit participant
@app.route("/api/admit-participant", methods=["POST"])
def admit_participant():
    try:
        data = request.json
        room_name = data.get("room_name")
        user_name = data.get("user_name")

        if room_name not in waiting_list:
            return jsonify({"error": "Room not found"}), 404

        waiting_list[room_name] = [p for p in waiting_list[room_name] if p["user_name"] != user_name]

        print(f"✅ {user_name} admitted to {room_name}")
        return jsonify({"message": "User admitted", "user_name": user_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
