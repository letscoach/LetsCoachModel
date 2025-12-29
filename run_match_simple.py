#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
סקריפט להריץ משחק ידני מ-Google Cloud SQL
"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'c:\\Users\\gideo\\Documents\\GitHub\\LetsCoachModel2')

print("🔍 מתחיל להריץ משחק מ-Google Cloud SQL...")

# בדוק איזה match_day אתה רוצה להריץ (ברירת מחדל: match_day 1)
match_day_to_run = 1
if len(sys.argv) > 1:
    try:
        match_day_to_run = int(sys.argv[1])
    except:
        pass

print(f"\n🔌 מתחבר ל-Google Cloud SQL...")
print(f"📊 מחפש משחקים ל-match_day {match_day_to_run}...")

# Import the Helpers.SQL_db which already has connection setup
from Helpers.SQL_db import get_matches_by_match_day

# בא נקבל את כל המשחקים של match_day הספציפי
try:
    matches_lst = get_matches_by_match_day(match_day_to_run)
except Exception as e:
    print(f"❌ שגיאה בקבלת משחקים: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

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
    print("  ⚠️ הוספת 'kind' = 1 (league)")
    first_match['kind'] = 1

print(f"\n🎮 מתחיל את המשחק...")
try:
    from Game.Matches import game_launcher
    result = game_launcher(first_match)
    print(f"\n✅ המשחק הסתיים בהצלחה!")
    print(f"\n📊 תוצאה סופית:")
    if result and 'result' in result:
        print(f"   🏆 תוצאה: {result['result'].get('team1_score', 0)} - {result['result'].get('team2_score', 0)}")
    else:
        print(f"   {result}")
except Exception as e:
    print(f"\n❌ שגיאה בהרצת המשחק: {e}")
    import traceback
    traceback.print_exc()
