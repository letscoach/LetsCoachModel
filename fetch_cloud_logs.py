import os
from google.cloud import logging
from datetime import datetime, timedelta

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'

print('📜 משיכת לוגים מ-Google Cloud Logging')
print('=' * 80)

# יצירת client
client = logging.Client(project='zinc-strategy-446518-s7')

# חפש לוגים מ-10 הדקות האחרונות
now = datetime.utcnow()
ten_min_ago = now - timedelta(minutes=10)

# Query לחיפוש לוגים עם המילים "PRIZE" או "distribute" או "💰"
filter_str = f'''
timestamp >= "{ten_min_ago.isoformat()}Z"
AND (
    textPayload=~".*PRIZE.*" 
    OR textPayload=~".*distribute.*"
    OR textPayload=~".*💰.*"
    OR textPayload=~".*INSERT.*"
)
'''

print(f'\n🔍 מחפש לוגים מ-{ten_min_ago.strftime("%H:%M:%S")} עד {now.strftime("%H:%M:%S")}\n')
print('=' * 80)

try:
    # משיכת לוגים
    entries = list(client.list_entries(filter_=filter_str, order_by=logging.DESCENDING, max_results=100))
    
    if entries:
        print(f'\n✅ נמצאו {len(entries)} לוגים:\n')
        
        for i, entry in enumerate(reversed(entries), 1):  # הפוך כדי להראות בסדר כרונולוגי
            timestamp = entry.timestamp.strftime('%H:%M:%S')
            payload = entry.payload if isinstance(entry.payload, str) else str(entry.payload)
            
            # הצג רק שורות רלוונטיות
            if any(keyword in payload for keyword in ['💰', 'PRIZE', 'INSERT', 'distribute', '🔵']):
                print(f'[{timestamp}] {payload}')
    else:
        print('⚠️  לא נמצאו לוגים עם המילים: PRIZE, distribute, 💰, INSERT')
        print('\nבוא ננסה לחפש כל לוג מה-service:')
        
        # חיפוש כללי יותר
        general_filter = f'timestamp >= "{ten_min_ago.isoformat()}Z"'
        general_entries = list(client.list_entries(filter_=general_filter, order_by=logging.DESCENDING, max_results=20))
        
        if general_entries:
            print(f'\n📋 20 הלוגים האחרונים:\n')
            for entry in reversed(general_entries):
                timestamp = entry.timestamp.strftime('%H:%M:%S')
                payload = entry.payload if isinstance(entry.payload, str) else str(entry.payload)
                print(f'[{timestamp}] {payload[:200]}...')
        else:
            print('\n❌ בכלל לא נמצאו לוגים מ-10 הדקות האחרונות')
            
except Exception as e:
    print(f'❌ שגיאה: {e}')
    import traceback
    traceback.print_exc()

print('\n' + '=' * 80)
