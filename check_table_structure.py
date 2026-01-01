import sys
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'c:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'
sys.path.insert(0, r'c:\Users\gideo\PycharmProjects\LetsCoachModel')

from Helpers.SQL_db import exec_select_query

print("🔍 בדיקת structure של competition_results")
print("=" * 60)

query = "DESCRIBE competition_results"
result = exec_select_query(query)

print("\nStructure:")
for row in result:
    print(row)

print("\n" + "=" * 60)
print("🔍 בדיקת constraints")

query2 = """
SELECT 
    TABLE_NAME,
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE
FROM information_schema.TABLE_CONSTRAINTS
WHERE TABLE_NAME = 'competition_results'
AND TABLE_SCHEMA = 'main_game'
"""
result2 = exec_select_query(query2)

print("\nConstraints:")
for row in result2:
    print(row)
