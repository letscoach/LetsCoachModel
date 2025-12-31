"""
Test script to manually run competition 28 locally and see what happens
"""
import os
import sys

# Set environment
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachModel')

print("=" * 80)
print("TESTING COMPETITION 28 - Dash100 LOCAL EXECUTION")
print("=" * 80)

# Import Dash100
from Competitions.dash100 import Dash100

# Run competition
print("\n1. Creating Dash100 instance for competition 28...")
competition = Dash100(competition_id=28)

print(f"\n2. Participants loaded: {len(competition.participants)}")
for i, p in enumerate(competition.participants, 1):
    print(f"   {i}. Token: ...{p['token'][-10:]}")

print("\n3. Running competition...")
results = competition.run_competition()

print(f"\n4. Results calculated: {len(results)} results")
for r in results:
    print(f"   - Token: ...{r['token'][-10:]}, Score: {r['score']}, Rank: {r['rank_position']}, DNF: {r.get('dnf', False)}")

print("\n5. Calculating attribute changes...")
attribute_changes = competition.calculate_attribute_changes()

print(f"\n6. Attribute changes prepared: {len(attribute_changes)} players")
for token, data in attribute_changes.items():
    print(f"   - Token: ...{token[-10:]}")
    print(f"     Score: {data.get('score', 'N/A')}, Rank: {data.get('rank_position', 'N/A')}")
    print(f"     Winner: {data.get('is_winner', 'N/A')}")
    print(f"     Attributes: {data.get('attributes', {})}")

print("\n7. Applying attribute changes (calling insert_player_attributes_competition_effected)...")
try:
    from Helpers.SQL_db import insert_player_attributes_competition_effected
    success, errors = insert_player_attributes_competition_effected(attribute_changes, 28)
    print(f"\n   SUCCESS! {success} players processed, {errors} errors")
except Exception as e:
    print(f"\n   ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n8. Checking competition_results table...")
from Helpers.SQL_db import exec_select_query
query = "SELECT * FROM competition_results WHERE competition_id = 28"
results_db = exec_select_query(query)
print(f"\n   Found {len(results_db)} results in database:")
for row in results_db:
    print(f"   - Token: ...{row[5][-10:]}, Score: {row[2]}, Rank: {row[3]}, Winner: {row[4]}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
