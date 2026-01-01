import sys
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachModel')

from Competitions.dash100 import Dash100
from Helpers.SQL_db import exec_select_query

print("🚀 הרצת Competition 1665 - Test LOCAL")
print("=" * 60)

# Get participants
query = "SELECT * FROM competition_participants WHERE competition_id = 1665"
participants = exec_select_query(query)
print(f"\n📋 Participants: {len(participants)}")
for p in participants:
    print(f"   Token: {p['token']}, Team: {p['team_id']}")

# Run the competition
print("\n🏃 מריץ את התחרות...")
comp = Dash100(competition_id=1665)

# Run race simulation
results = comp.run_competition()
print(f"\n📊 תוצאות: {len(results)} משתתפים")

# Calculate attribute changes
changes = comp.calculate_attribute_changes()
print(f"\n✅ חישוב שינויים בוצע עבור {len(changes)} שחקנים:")
for token, data in changes.items():
    print(f"\n   Token: {token}")
    print(f"   Rank: {data.get('rank_position')}")
    print(f"   Score: {data.get('score')}")
    print(f"   Is Winner: {data.get('is_winner')}")

# Apply changes
print("\n💾 מכניס תוצאות לדאטהבייס...")
comp.apply_attribute_changes()

print("\n✅ סיום!")
