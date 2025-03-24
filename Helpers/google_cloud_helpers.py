import base64
import os
import time

import google.auth
from google.auth.transport.requests import Request
import json
import requests
from google.auth import jwt
from datetime import datetime, timedelta, timezone




def create_task_for_match(data):

    CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), "google_api_cred.json")
    scopes = ['https://www.googleapis.com/auth/cloud-platform']
    credentials, project = google.auth.load_credentials_from_file(CLIENT_SECRET_FILE, scopes=scopes)
    if credentials.expired or not credentials.valid:
        credentials.refresh(Request())
    API_TOKEN = credentials.token
    url = "https://cloudtasks.googleapis.com/v2/projects/zinc-strategy-446518-s7/locations/us-central1/queues/LaunchModelGame/tasks"
    schedule_time =data['match_datetime']
    del data['match_datetime']
    base64body =json.dumps(data)

    schedule_time_str = schedule_time.replace(tzinfo=timezone.utc).isoformat()
    schedule_time_str = schedule_time_str.replace("+00:00", "Z")
    base64body = base64.b64encode(base64body.encode('utf-8')).decode('utf-8')
    payload = json.dumps({
      "task": {
        "httpRequest": {
          "httpMethod": "POST",
          "url": "https://letcoach-model-354078768099.us-central1.run.app",
          "headers": {
            "Content-Type": "application/json"
          },
          "body": base64body
        },
        "scheduleTime":schedule_time_str
      }
    })
    headers = {
      'Content-Type': 'application/json',
      'Authorization': f"Bearer {API_TOKEN}"
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response

