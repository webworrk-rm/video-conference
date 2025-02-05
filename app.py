from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os

app = Flask(__name__)

# ✅ Corrected CORS setup (Allow all origins or restrict as needed)
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

# ✅ API to create a meeting (Private with host controls)
@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        print("✅ Received request to create a meeting")

        # Create a meeting with **private** access and knock feature enabled
        response = requests.post(dailyco_base_url, headers=headers, json={
            "privacy": "private",
            "enable_knocking": True  # Forces participants to wait for approval
        })
        data = response.json()

        print("✅ Daily.co Response:", data)

        if "url" in data:
            host_url = f"{data['url']}?t=host"
            participant_url = f"{data['url']}?t=participant"
            print(f"✅ Meeting created: Host URL = {host_url}, Participant URL = {participant_url}")
            return jsonify({
                "url": participant_url,  # Participants get this link
                "host_url": host_url      # Host gets this link
            }), 201
        else:
            print("❌ ERROR: Daily.co API failed", data)
            return jsonify({"error": "Failed to create meeting", "details": data}), 500
    except Exception as e:
        print("❌ Create Meeting Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
