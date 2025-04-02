import os
import json
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Flask app
app = Flask(__name__)
CORS(app)  # <- включаем CORS

# Папка Google Drive
FOLDER_ID = "1ji1tWY-qDFbSjzV7G6POvmS4NNJRHjf7"

# Креды из ENV
credentials_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
credentials = service_account.Credentials.from_service_account_info(credentials_info)
drive_service = build("drive", "v3", credentials=credentials)

@app.route("/stories")
def get_stories():
    now = datetime.utcnow()
    time_48h_ago = (now - timedelta(hours=48)).isoformat() + "Z"

    results = drive_service.files().list(
        q=f"'{FOLDER_ID}' in parents and modifiedTime > '{time_48h_ago}' and trashed = false",
        fields="files(id, name, mimeType, webContentLink, modifiedTime)",
        orderBy="modifiedTime desc"
    ).execute()

    return jsonify(results.get("files", []))

@app.route("/")
def index():
    return "✅ GDrive Stories API is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
