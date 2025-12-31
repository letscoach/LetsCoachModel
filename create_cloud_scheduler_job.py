"""
יצירת Google Cloud Scheduler Job לריצת המשחקים בקביעות
"""

from google.cloud import scheduler_v1
from google.api_core.gapic_v1 import client_info as grpc_client_info
import json
import os

# הגדרות
PROJECT_ID = "zinc-strategy-446518-s7"
LOCATION = "us-central1"
JOB_NAME = "matches-scheduler"
SCHEDULE = "*/5 * * * *"  # כל 5 דקות
TIMEZONE = "UTC"

# ה-URL שלך - Cloud Run Backend
BACKEND_URL = "https://letcoach-backend-dev-354078768099.us-central1.run.app/scheduler/run-matches"

def create_scheduler_job():
    """יצירת Cloud Scheduler Job"""
    
    print("🚀 יצירת Cloud Scheduler Job")
    print("=" * 60)
    
    # צור client
    client = scheduler_v1.CloudSchedulerClient()
    
    # בנה את ה-parent path
    parent = client.common_location_path(PROJECT_ID, LOCATION)
    
    # בנה את ה-job
    job = {
        "name": f"{parent}/jobs/{JOB_NAME}",
        "description": "Scheduled job to run matches every 5 minutes",
        "schedule": SCHEDULE,
        "time_zone": TIMEZONE,
        "http_target": {
            "uri": BACKEND_URL,
            "http_method": scheduler_v1.HttpMethod.POST,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": b"{}",
        },
    }
    
    try:
        print(f"📌 Project: {PROJECT_ID}")
        print(f"📌 Location: {LOCATION}")
        print(f"📌 Job Name: {JOB_NAME}")
        print(f"📌 Schedule: {SCHEDULE} (כל 5 דקות)")
        print(f"📌 URL: {BACKEND_URL}\n")
        
        # צור את ה-job
        response = client.create_job(request={"parent": parent, "job": job})
        
        print("✅ Job נוצר בהצלחה!")
        print(f"   {response.name}")
        return response
        
    except Exception as e:
        error_msg = str(e)
        
        # בדוק אם ה-job כבר קיים
        if "ALREADY_EXISTS" in error_msg or "already exists" in error_msg:
            print("⚠️  ה-Job כבר קיים!")
            print("   בחר שם אחר או הסר את הישן קודם")
            return None
        else:
            print(f"❌ שגיאה: {e}")
            return None

def delete_scheduler_job():
    """מחיקת Cloud Scheduler Job"""
    
    print("🗑️  מחיקת Cloud Scheduler Job")
    print("=" * 60)
    
    client = scheduler_v1.CloudSchedulerClient()
    parent = client.common_location_path(PROJECT_ID, LOCATION)
    job_path = client.job_path(PROJECT_ID, LOCATION, JOB_NAME)
    
    try:
        client.delete_job(request={"name": job_path})
        print(f"✅ Job {JOB_NAME} נמחק בהצלחה!")
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")

def list_scheduler_jobs():
    """הצגת כל ה-Jobs ב-Scheduler"""
    
    print("📋 רשימת כל ה-Jobs")
    print("=" * 60)
    
    client = scheduler_v1.CloudSchedulerClient()
    parent = client.common_location_path(PROJECT_ID, LOCATION)
    
    try:
        jobs = client.list_jobs(request={"parent": parent})
        
        job_list = list(jobs)
        print(f"נמצאו {len(job_list)} jobs:\n")
        
        for i, job in enumerate(job_list, 1):
            print(f"{i}. {job.name.split('/')[-1]}")
            print(f"   Schedule: {job.schedule}")
            print(f"   Status: {job.state}")
            if job.http_target:
                print(f"   URL: {job.http_target.uri}")
            print()
        
        return job_list
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        return []

if __name__ == "__main__":
    import sys
    
    # קבל ארגומנט מ-command line
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = "create"
    
    if command == "create":
        create_scheduler_job()
    elif command == "delete":
        delete_scheduler_job()
    elif command == "list":
        list_scheduler_jobs()
    else:
        print("שימוש: python create_cloud_scheduler_job.py [create|delete|list]")
