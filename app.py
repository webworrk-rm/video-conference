from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import uuid
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "your_mongodb_connection_url")
client = MongoClient(MONGO_URI)
db = client["video_conference"]
meetings_collection = db["meetings"]

@app.route('/create-meeting', methods=['POST'])
def create_meeting():
    """Creates a new meeting and generates host/participant links"""
    meeting_id = str(uuid.uuid4())[:8]
    meeting = {
        "meeting_id": meeting_id,
        "title": request.json.get("title", "Untitled Meeting"),
        "description": request.json.get("description", ""),
        "date_time": request.json.get("date_time", str(datetime.utcnow())),
        "host_link": f"https://meet.jit.si/{meeting_id}-host",
        "participant_link": f"https://meet.jit.si/{meeting_id}-participant"
    }
    meetings_collection.insert_one(meeting)
    return jsonify(meeting)

@app.route('/get-meeting/<meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    """Retrieves meeting details using the meeting ID"""
    meeting = meetings_collection.find_one({"meeting_id": meeting_id})
    if meeting:
        return jsonify(meeting)
    return jsonify({"error": "Meeting not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
