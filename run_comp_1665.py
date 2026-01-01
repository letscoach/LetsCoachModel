import sys
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachModel')
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachBackend')

from Helpers.SQL_db import exec_select_query

print("🔍 בדיקת Competition 1665")
print("=" * 60)

# בדוק משתתפים
query1 = "SELECT * FROM competition_participants WHERE competition_id = 1665"
result1 = exec_select_query(query1)
participants = result1 if isinstance(result1, list) else [result1]

print(f"\n📋 Participants ({len(participants)}):")
for p in participants:
    print(f"   Token: {p['token']}, Team: {p['team_id']}")

# בדוק תוצאות
query2 = "SELECT * FROM competition_results WHERE competition_id = 1665"
result2 = exec_select_query(query2)
results = result2 if isinstance(result2, list) else [result2]

print(f"\n📊 Results ({len(results)}):")
if results:
    for r in results:
        if isinstance(r, dict):
            print(f"   Token: {r.get('token')}, Score: {r.get('score')}, Rank: {r.get('rank_position')}")
        else:
            print(f"   Result: {r}")
else:
    print("   ⚠️ אין תוצאות!")

print("\n" + "=" * 60)
print("🔍 בואו נריץ את התחרות ידנית!\n")

from Competitions.dash100 import Dash100

comp = Dash100(competition_id=1665)
result = comp.run()

print(f"\n✅ התוצאה: {result}")
