import sys
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'

sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachModel')
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachBackend')

from Helpers.SQL_db import exec_select_query, distribute_competition_prizes

print('🎁 חלוקת פרסים לתחרויות שרצו')
print('=' * 80)

# מצא תחרויות שרצו אבל לא קיבלו פרסים
query = """
SELECT DISTINCT c.id, c.competition_type_id, COUNT(DISTINCT cr.token) as participants
FROM competition_results cr
JOIN competitions c ON cr.competition_id = c.id
LEFT JOIN transactions t ON t.description LIKE CONCAT('%Competition%', c.id, '%')
WHERE t.id IS NULL
GROUP BY c.id, c.competition_type_id
ORDER BY c.id DESC
LIMIT 10
"""

result = exec_select_query(query)

if result:
    print(f'\n📊 נמצאו {len(result)} תחרויות שצריך לחלק להן פרסים:\n')
    
    for row in result:
        comp_id = row['id']
        comp_type = row['competition_type_id']
        participants = row['participants']
        
        print(f'🏆 תחרות {comp_id} (Type {comp_type}) - {participants} משתתפים')
        print(f'   מחלק פרסים...')
        print('=' * 80)
        
        # חלק פרסים
        result = distribute_competition_prizes(comp_id, comp_type)
        
        print(f'\n📊 תוצאה: {result}')
        print('=' * 80 + '\n')
else:
    print('\n✅ אין תחרויות שצריך לחלק להן פרסים')
