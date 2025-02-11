from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MongoDB Connection
client = MongoClient("your_mongodb_connection_url")
db = client["video_conference"]
meetings_collection = db["meetings"]

@app.route('/create-meeting', methods=['POST'])
def create_meeting():
    meeting_id = str(uuid.uuid4())[:8]
    meeting = {
        "meeting_id": meeting_id,
        "title": request.json.get("title", "Untitled Meeting"),
        "host_link": f"https://meet.jit.si/{meeting_id}-host",
        "participant_link": f"https://meet.jit.si/{meeting_id}-participant"
    }
    meetings_collection.insert_one(meeting)
    return jsonify(meeting)

if __name__ == '__main__':
    app.run(debug=True)
