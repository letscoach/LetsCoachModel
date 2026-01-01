import sys
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'

sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachModel')
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachBackend')

print('🔍 בדיקת חלוקת פרסים - הרצה ישירה')
print('=' * 70)

from Helpers.SQL_db import exec_select_query, distribute_competition_prizes

query = """
SELECT DISTINCT cr.competition_id, c.competition_type_id
FROM competition_results cr
JOIN competitions c ON cr.competition_id = c.id
ORDER BY cr.competition_id DESC
LIMIT 1
"""

result = exec_select_query(query)

print(f"\n🔍 Debug - Result type: {type(result)}")
if result:
    print(f"   Result length: {len(result)}")
    print(f"   First row type: {type(result[0])}")
    print(f"   First row: {result[0]}")
    if hasattr(result[0], '_asdict'):
        print(f"   As dict: {result[0]._asdict()}")

if result and len(result) > 0:
    row = result[0]
    comp_id = row['competition_id']
    comp_type = row['competition_type_id']
    
    print(f'\n✅ תחרות: ID={comp_id}, Type={comp_type}')
    print('\n' + '='*70)
    print('🚀 קורא ל-distribute_competition_prizes...')
    print('='*70 + '\n')
    
    prize_result = distribute_competition_prizes(comp_id, comp_type)
    
    print('\n' + '='*70)
    print('📊 תוצאה:')
    print(prize_result)
else:
    print('❌ לא נמצאו תחרויות')
