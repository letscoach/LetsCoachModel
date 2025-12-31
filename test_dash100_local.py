"""
Test Dash100 competition locally with real data
"""
import os
import sys

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachModel')

print("=" * 80)
print("LOCAL TEST - Dash100 Competition 28")
print("=" * 80)

try:
    from Competitions.dash100 import Dash100
    from Helpers.SQL_db import exec_select_query
    
    # Create competition instance
    print("\n1. Creating Dash100 instance for competition 28...")
    competition = Dash100(competition_id=28)
    
    print(f"\n2. Participants: {len(competition.participants)}")
    for i, p in enumerate(competition.participants, 1):
        print(f"   {i}. Token: ...{p['token'][-10:]}")
    
    # Run competition
    print("\n3. Running competition...")
    results = competition.run_competition()
    
    print(f"\n4. Results: {len(results)} results")
    for r in results:
        print(f"   Token: ...{r['token'][-10:]}, Score: {r['score']}, Rank: {r['rank_position']}")
    
    # Calculate attribute changes
    print("\n5. Calculating attribute changes...")
    attr_changes = competition.calculate_attribute_changes()
    
    print(f"\n6. Attribute changes: {len(attr_changes)} players")
    for token, data in attr_changes.items():
        print(f"   Token: ...{token[-10:]}")
        print(f"     Score: {data.get('score')}, Rank: {data.get('rank_position')}, Winner: {data.get('is_winner')}")
    
    # Apply changes (THIS IS THE CRITICAL PART)
    print("\n7. Applying attribute changes...")
    from Helpers.SQL_db import insert_player_attributes_competition_effected
    success, errors = insert_player_attributes_competition_effected(attr_changes, 28)
    
    print(f"\n8. Result: {success} succeeded, {errors} errors")
    
    # Check database
    print("\n9. Checking database...")
    query = "SELECT COUNT(*) FROM competition_results WHERE competition_id = 28"
    count = exec_select_query(query)
    total = count[0][0] if count else 0
    print(f"   Total results in DB: {total}")
    
    if total > 0:
        query2 = "SELECT token, score, rank_position, is_winner FROM competition_results WHERE competition_id = 28 ORDER BY rank_position"
        results_db = exec_select_query(query2)
        print("\n   Results in DB:")
        for r in results_db:
            print(f"     Rank {r[2]}: ...{r[0][-10:]}, Score={r[1]}, Winner={r[3]}")
        print("\n" + "=" * 80)
        print("SUCCESS!")
        print("=" * 80)
    else:
        print("\n   ERROR: No results in database!")
        print("   insert_player_attributes_competition_effected FAILED")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
