#!/usr/bin/env python3
"""
יצירת Cloud Scheduler Job ל-Matches Scheduler
"""

from google.cloud import scheduler_v1
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'

print("✅ יצירת Cloud Scheduler Job")
print("=" * 70 + "\n")

PROJECT_ID = "zinc-strategy-446518-s7"
LOCATION = "us-central1"
JOB_NAME = "matches-scheduler"
SCHEDULE = "*/5 * * * *"
BACKEND_URL = "https://letcoach-backend-dev-354078768099.us-central1.run.app/scheduler/run-matches"

def main():
    client = scheduler_v1.CloudSchedulerClient()
    parent = client.common_location_path(PROJECT_ID, LOCATION)
    
    # בנה Job - בלי timezone field
    job = {
        "name": f"{parent}/jobs/{JOB_NAME}",
        "description": "Scheduled job to run matches every 5 minutes",
        "schedule": SCHEDULE,
        "http_target": {
            "uri": BACKEND_URL,
            "http_method": scheduler_v1.HttpMethod.POST,
            "headers": {"Content-Type": "application/json"},
            "body": b"{}",
        },
    }
    
    try:
        print(f"📌 Project: {PROJECT_ID}")
        print(f"📌 Location: {LOCATION}")
        print(f"📌 Job Name: {JOB_NAME}")
        print(f"📌 Schedule: {SCHEDULE} (כל 5 דקות)")
        print(f"📌 URL: {BACKEND_URL}\n")
        
        response = client.create_job(request={"parent": parent, "job": job})
        
        print("🎉 Job נוצר בהצלחה!")
        print(f"\n📊 פרטי ה-Job שנוצר:")
        print(f"   - Name: {response.name.split('/')[-1]}")
        print(f"   - Schedule: {response.schedule}")
        print(f"   - URL: {response.http_target.uri}")
        print(f"   - Status: {response.state}")
        print(f"\n✨ ה-Job יתחיל להריץ משחקים כל 5 דקות באופן אוטומטי!")
        
    except Exception as e:
        if "ALREADY_EXISTS" in str(e):
            print(f"✅ {JOB_NAME} כבר קיים בעבר!")
            print(f"   זה מעולה - Job כבר פעיל!\n")
            
            # הצג את הפרטים של ה-Job הקיים
            try:
                job_path = client.job_path(PROJECT_ID, LOCATION, JOB_NAME)
                existing_job = client.get_job(request={"name": job_path})
                print(f"📊 פרטי ה-Job הקיים:")
                print(f"   - Schedule: {existing_job.schedule}")
                print(f"   - URL: {existing_job.http_target.uri}")
                print(f"   - Status: {existing_job.state}")
            except:
                pass
        else:
            print(f"❌ שגיאה: {e}")

if __name__ == "__main__":
    main()
