#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
סקריפט להריץ משחק ידני להבדיקת הפונקציה
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'c:\\Users\\gideo\\PycharmProjects\\LetsCoachModel2')

from datetime import datetime
from Helpers.SQL_db import get_matches_by_match_day

# בדוק איזה match_day אתה רוצה להריץ (ברירת מחדל: match_day 1)
match_day_to_run = 1
if len(sys.argv) > 1:
    try:
        match_day_to_run = int(sys.argv[1])
    except:
        pass

# בא נקבל את כל המשחקים של match_day הספציפי
print(f"🔍 מחפש משחקים בדאטהבייס ל-match_day {match_day_to_run}...")
matches_lst = get_matches_by_match_day(match_day_to_run)

if not matches_lst:
    print(f"❌ אין משחקים בדאטהבייס ל-match_day {match_day_to_run}")
    sys.exit(1)

print(f"✅ נמצאו {len(matches_lst)} משחקים ל-match_day {match_day_to_run}")

# בא נראה את כל המשחקים של היום הזה
print(f"\n📋 משחקים ל-match_day {match_day_to_run}:")
for i, match in enumerate(matches_lst, 1):
    print(f"  {i}. Match ID {match.get('match_id')}: {match.get('home_team_id')} vs {match.get('away_team_id')} @ {match.get('match_datetime')}")

# בא נריץ את המשחק הראשון בלבד
first_match = matches_lst[0]
print(f"\n🎯 מריץ את המשחק הראשון בלבד (Match ID: {first_match['match_id']})")
print(f"  {first_match['home_team_id']} (Home) vs {first_match['away_team_id']} (Away)")
print(f"  DateTime: {first_match.get('match_datetime')}")

# בא נבדוק אם יש 'kind' בפרטי המשחק
if 'kind' not in first_match:
    print("  ⚠️ הוספת 'kind' = 'league'")
    first_match['kind'] = 'league'

from Game.Matches import game_launcher

print(f"\n🎮 הרצת המשחק...")
try:
    result = game_launcher(first_match)
    print(f"\n✅ המשחק הסתיים בהצלחה!")
    print(f"תוצאה: {result}")
except Exception as e:
    print(f"\n❌ שגיאה בהרצת המשחק: {e}")
    import traceback
    traceback.print_exc()
