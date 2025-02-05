from flask import Flask, request, jsonify
import requests
from flask_pymongo import PyMongo
import os
from flask_cors import CORS

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

# ✅ API to create a meeting and send link to frontend without storing in DB
@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        print("✅ Received request to create a meeting")

        response = requests.post(dailyco_base_url, headers=headers, json={"privacy": "private"})
        data = response.json()

        print("✅ Daily.co Response:", data)

        if "url" in data:
            print(f"✅ Meeting created: URL = {data['url']}")
            return jsonify({"url": data["url"]}), 201
        else:
            print("❌ ERROR: Daily.co API failed", data)
            return jsonify({"error": "Failed to create meeting", "details": data}), 500
    except Exception as e:
        print("❌ Create Meeting Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
