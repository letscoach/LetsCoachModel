import sys
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'

sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachModel')
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachBackend')

from Helpers.SQL_db import exec_select_query

print('🔍 בדיקת כל התחרויות האחרונות')
print('=' * 80)

# מצא את התחרויות האחרונות עם תוצאות
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
LEFT JOIN competition_results cr ON c.id = cr.competition_id
GROUP BY c.id, c.competition_type_id, c.status_id
ORDER BY c.id DESC
LIMIT 15
"""

result = exec_select_query(query)

if result:
    print(f'\n📋 15 התחרויות האחרונות:\n')
    
    competitions_with_results_no_prizes = []
    
    for row in result:
        comp_id = row['competition_id']
        comp_type = row['competition_type_id']
        status = row['status_id']
        participants = row['num_participants']
        transactions = row['num_transactions']
        
        # סטטוס names
        status_name = {0: 'לא פעיל', 1: 'פעיל', 2: 'הסתיים', 3: 'בוטל'}.get(status, 'לא ידוע')
        
        icon = '✅' if transactions > 0 else ('⚠️' if participants > 0 else '⭕')
        
        print(f'{icon} תחרות {comp_id} - Type {comp_type} - {status_name}')
        print(f'   משתתפים: {participants} | טרנזקציות: {transactions}')
        
        if participants > 0 and transactions == 0:
            competitions_with_results_no_prizes.append((comp_id, comp_type))
        
        print()
    
    if competitions_with_results_no_prizes:
        print('=' * 80)
        print(f'\n🔴 נמצאו {len(competitions_with_results_no_prizes)} תחרויות עם תוצאות אבל ללא פרסים:')
        for comp_id, comp_type in competitions_with_results_no_prizes:
            print(f'   - תחרות {comp_id} (Type {comp_type})')
    else:
        print('=' * 80)
        print('\n✅ כל התחרויות עם תוצאות קיבלו פרסים!')
else:
    print('\n❌ לא נמצאו תחרויות')
