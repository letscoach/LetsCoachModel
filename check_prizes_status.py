import sys
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'

sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachModel')
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachBackend')

from Helpers.SQL_db import exec_select_query

print('🔍 בדיקת סטטוס חלוקת פרסים לתחרויות')
print('=' * 80)

# מצא את כל התחרויות עם תוצאות
query = """
SELECT 
    c.id as competition_id,
    c.competition_type_id,
    c.status_id,
    COUNT(DISTINCT cr.token) as num_participants,
    (SELECT COUNT(*) 
     FROM transactions t 
     WHERE t.description LIKE CONCAT('%Competition%', c.id, '%')) as num_transactions
FROM competitions c
JOIN competition_results cr ON c.id = cr.competition_id
WHERE c.status_id = 2
GROUP BY c.id, c.competition_type_id, c.status_id
ORDER BY c.id DESC
LIMIT 10
"""

result = exec_select_query(query)

if result:
    print(f'\n📋 נמצאו {len(result)} תחרויות שהסתיימו (status_id=2):\n')
    
    competitions_without_prizes = []
    
    for row in result:
        comp_id = row['competition_id']
        comp_type = row['competition_type_id']
        participants = row['num_participants']
        transactions = row['num_transactions']
        
        status = '✅' if transactions > 0 else '❌'
        
        print(f'{status} תחרות {comp_id} (Type {comp_type}):')
        print(f'   משתתפים: {participants}')
        print(f'   טרנזקציות: {transactions}')
        
        if transactions == 0:
            competitions_without_prizes.append((comp_id, comp_type))
        
        print()
    
    if competitions_without_prizes:
        print('=' * 80)
        print(f'\n⚠️  נמצאו {len(competitions_without_prizes)} תחרויות ללא פרסים:')
        for comp_id, comp_type in competitions_without_prizes:
            print(f'   - תחרות {comp_id} (Type {comp_type})')
    else:
        print('=' * 80)
        print('\n✅ כל התחרויות קיבלו פרסים!')
else:
    print('\n❌ לא נמצאו תחרויות שהסתיימו')
