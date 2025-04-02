import os
import json
import io
from flask import Flask, request, jsonify, send_file, abort
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

app = Flask(__name__)

# Авторизация
SCOPES = ['https://www.googleapis.com/auth/drive']
credentials_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
credentials = service_account.Credentials.from_service_account_info(
    credentials_info, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

# ID папки с файлами
FOLDER_ID = os.getenv("GDRIVE_FOLDER")

@app.route("/")
def index():
    return "✅ GDrive Stories API is working."

@app.route("/stories")
def get_stories():
    try:
        cutoff_time = (datetime.utcnow() - timedelta(hours=48)).isoformat("T") + "Z"

        results = drive_service.files().list(
            q=f"'{FOLDER_ID}' in parents and trashed = false and modifiedTime > '{cutoff_time}'",
            fields="files(id, name, mimeType, modifiedTime)",
            orderBy="modifiedTime desc"
        ).execute()
        files = results.get("files", [])

        # добавляем прямую ссылку на скачивание
        for file in files:
            file["webContentLink"] = f"https://drive.google.com/uc?id={file['id']}&export=download"

        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/media")
def get_media():
    file_id = request.args.get("id")
    if not file_id:
        return abort(400, "Missing file id")

    try:
        request_drive = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_drive)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)
        file_meta = drive_service.files().get(fileId=file_id, fields="mimeType, name").execute()
        mime = file_meta["mimeType"]
        name = file_meta["name"]

        return send_file(fh, mimetype=mime, download_name=name)
    except Exception as e:
        return abort(500, f"Ошибка загрузки файла: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)
