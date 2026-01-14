#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
סקריפט להריץ משחק ידני עם Google Cloud SQL
"""
import sys
import os
import io

# Set up Google Cloud credentials BEFORE importing anything else
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'c:\\Users\\gideo\\Documents\\GitHub\\LetsCoachBackend\\sql_cred.json'

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'c:\\Users\\gideo\\Documents\\GitHub\\LetsCoachModel2')

print("🔍 מתחיל להריץ משחק...")
print(f"📁 Working directory: {os.getcwd()}")
print(f"🔑 Google credentials file: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")

# Import after setting credentials
from google.cloud.sql.connector import Connector
import pymysql
import sqlalchemy
from sqlalchemy import text

# בדוק איזה match_day אתה רוצה להריץ (ברירת מחדל: match_day 1)
match_day_to_run = 1
if len(sys.argv) > 1:
    try:
        match_day_to_run = int(sys.argv[1])
    except:
        pass

def get_matches_from_cloud_sql(match_day):
    """קבל משחקים מ-Google Cloud SQL"""
    print(f"\n🔌 מתחבר ל-Google Cloud SQL...")
    try:
        # Initialize the Connector
        connector = Connector()
        
        def getconn():
            return connector.connect(
                "zinc-strategy-446518-s7:us-central1:letscoach-dev",
                "pymysql",
                user="me",
                password="Ab123456",
                db="main_game",
                enable_iam_auth=False,
            )
        
        # Create SQLAlchemy engine
        pool = sqlalchemy.create_engine(
            "mysql+pymysql://",
            creator=getconn,
            pool_pre_ping=True,
        )
        
        print("✅ התחברות ל-Google Cloud SQL הצליחה!")
        
        # Execute query
        with pool.connect() as db_conn:
            query = f"SELECT * FROM matches WHERE match_day = {match_day}"
            print(f"📊 מריץ query: {query}")
            result = db_conn.execute(text(query)).fetchall()
            
            # Convert to dict
            matches = []
            for row in result:
                matches.append(row._asdict())
            
            return matches
    except Exception as e:
        print(f"❌ שגיאה בהתחברות: {e}")
        import traceback
        traceback.print_exc()
        return []

# בא נקבל את כל המשחקים של match_day הספציפי
print(f"\n🔍 מחפש משחקים בדאטהבייס ל-match_day {match_day_to_run}...")
matches_lst = get_matches_from_cloud_sql(match_day_to_run)

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
    print("  ⚠️ הוספת 'kind' = 1 (League)")
    first_match['kind'] = 1  # Default to 1 (League)

print(f"\n🎮 הרצת המשחק...")
try:
    from Game.Matches import game_launcher
    result = game_launcher(first_match)
    print(f"\n✅ המשחק הסתיים בהצלחה!")
    print(f"תוצאה: {result}")
except Exception as e:
    print(f"\n❌ שגיאה בהרצת המשחק: {e}")
    import traceback
    traceback.print_exc()
