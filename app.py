from flask import Flask, request, jsonify
import requests
import os
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

dailyco_api_key = os.getenv("DAILY_CO_API_KEY", "YOUR_DAILY_CO_API_KEY")
dailyco_base_url = "https://api.daily.co/v1/rooms"
token_api_url = "https://api.daily.co/v1/meeting-tokens"

headers = {
    "Authorization": f"Bearer {dailyco_api_key}",
    "Content-Type": "application/json"
}

meetings = []

@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        data = request.json
        scheduled = data.get("scheduled", False)
        expiration = int(time.time()) + (3600 if scheduled else 1800)

        response = requests.post(dailyco_base_url, headers=headers, json={
            "privacy": "private",
            "properties": {
                "enable_knocking": True,
                "exp": expiration,
                "start_audio_off": True,
                "start_video_off": True
            }
        })
        meeting_data = response.json()

        if "url" in meeting_data:
            room_name = meeting_data["name"]
            host_token = generate_token(room_name, is_owner=True)
            participant_token = generate_token(room_name, is_owner=False)

            host_url = f"{meeting_data['url']}?t={host_token}"
            participant_url = f"{meeting_data['url']}?t={participant_token}"
            meetings.append({"id": room_name, "name": room_name, "url": participant_url})

            return jsonify({"host_url": host_url, "participant_url": participant_url}), 201
        else:
            return jsonify({"error": "Failed to create meeting", "details": meeting_data}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/get-meetings", methods=["GET"])
def get_meetings():
    return jsonify({"meetings": meetings}), 200


def generate_token(room_name, is_owner=False):
    try:
        response = requests.post(token_api_url, headers=headers, json={
            "properties": {
                "room_name": room_name,
                "is_owner": is_owner,
                "exp": int(time.time()) + 3600
            }
        })
        return response.json().get("token")
    except Exception as e:
        return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
