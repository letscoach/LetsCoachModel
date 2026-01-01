import sys
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'

sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachModel')
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachBackend')

from Helpers.SQL_db import exec_select_query

print('🔍 חיפוש תחרויות שרצו (עם תוצאות)')
print('=' * 80)

query = """
SELECT DISTINCT c.id, c.competition_type_id, COUNT(*) as results,
       (SELECT COUNT(*) FROM transactions t WHERE t.description LIKE CONCAT('%Competition%', c.id, '%')) as prizes
FROM competition_results cr
JOIN competitions c ON cr.competition_id = c.id
GROUP BY c.id, c.competition_type_id
ORDER BY c.id DESC
LIMIT 10
"""

result = exec_select_query(query)

if result:
    print(f'\n📊 10 התחרויות האחרונות עם תוצאות:\n')
    
    for row in result:
        comp_id = row['id']
        comp_type = row['competition_type_id']
        num_results = row['results']
        prizes = row['prizes']
        
        status = '✅' if prizes > 0 else '❌'
        
        print(f'{status} תחרות {comp_id} (Type {comp_type})')
        print(f'   תוצאות: {num_results} | פרסים: {prizes}')
        print()
else:
    print('\n❌ לא נמצאו תחרויות עם תוצאות')
