#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסט ישיר - קריאה לפונקציית חלוקת פרסים
"""

import sys
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'C:\Users\gideo\PycharmProjects\LetsCoachBackend\sql_cred.json'
sys.path.insert(0, r'C:\Users\gideo\PycharmProjects\LetsCoachModel')

from Helpers.SQL_db import exec_select_query, distribute_competition_prizes

print("=" * 80)
print("🔍 טסט ישיר - חלוקת פרסים")
print("=" * 80)

# שלב 1: מצא תחרות שיש לה תוצאות אבל אין לה prizes
query = """
SELECT DISTINCT cr.competition_id, c.competition_type_id
FROM competition_results cr
JOIN competitions c ON cr.competition_id = c.id
WHERE cr.competition_id NOT IN (
    SELECT DISTINCT SUBSTRING_INDEX(SUBSTRING_INDEX(description, 'ID: ', -1), ')', 1)
    FROM transactions 
    WHERE transaction_type = 'Prize'
)
ORDER BY cr.competition_id DESC
LIMIT 5
"""

print("\n📋 מחפש תחרויות עם תוצאות אבל בלי פרסים...")
competitions = exec_select_query(query)

if competitions:
    print(f"✅ נמצאו {len(competitions)} תחרויות:\n")
    
    for comp in competitions:
        if isinstance(comp, dict):
            comp_id = comp['competition_id']
            comp_type = comp['competition_type_id']
        else:
            comp_id, comp_type = comp
        
        # בדוק כמה תוצאות יש
        count_query = f"SELECT COUNT(*) as count FROM competition_results WHERE competition_id = {comp_id}"
        count_result = exec_select_query(count_query)
        count = count_result[0]['count'] if isinstance(count_result[0], dict) else count_result[0][0]
        
        print(f"   Competition {comp_id} (Type {comp_type}): {count} results")
    
    # קח את הראשונה
    first_comp = competitions[0]
    if isinstance(first_comp, dict):
        test_comp_id = first_comp['competition_id']
        test_comp_type = first_comp['competition_type_id']
    else:
        test_comp_id, test_comp_type = first_comp
    
    print(f"\n{'='*80}")
    print(f"🎯 מריץ חלוקת פרסים לתחרות {test_comp_id} (Type {test_comp_type})")
    print(f"{'='*80}\n")
    
    # הרץ את הפונקציה
    try:
        result = distribute_competition_prizes(test_comp_id, test_comp_type)
        
        print(f"\n{'='*80}")
        print(f"✅ הפונקציה הסתיימה!")
        print(f"   תוצאה: {result}")
        print(f"{'='*80}\n")
        
        # בדוק אם נוצרו transactions
        check_query = f"""
        SELECT COUNT(*) as count 
        FROM transactions 
        WHERE description LIKE '%{test_comp_id}%'
        AND transaction_type = 'Prize'
        """
        
        trans_result = exec_select_query(check_query)
        trans_count = trans_result[0]['count'] if isinstance(trans_result[0], dict) else trans_result[0][0]
        
        if trans_count > 0:
            print(f"✅✅✅ SUCCESS! נוצרו {trans_count} transactions!")
        else:
            print(f"❌ לא נוצרו transactions!")
            print(f"   תוצאה מהפונקציה: {result}")
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ שגיאה בהרצת הפונקציה!")
        print(f"   Error: {e}")
        print(f"{'='*80}\n")
        import traceback
        traceback.print_exc()

else:
    print("⚠️ לא נמצאו תחרויות עם תוצאות ללא פרסים")
    print("   כל התחרויות כבר קיבלו פרסים, או שאין תחרויות עם תוצאות")

print("\n" + "=" * 80)
print("✅ טסט הסתיים!")
print("=" * 80)
