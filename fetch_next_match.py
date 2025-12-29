#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
סקריפט לשליפת המשחק הבא - ללא צורך ב-credentials
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("🚀 מתחיל לשלוף נתוני המשחק הבא...")

try:
    from google.cloud.sql.connector import Connector
    import sqlalchemy
    from sqlalchemy import text
    
    print(f"\n🔌 מתחבר ל-Google Cloud SQL...")
    
    # Initialize Connector WITHOUT credentials - use password auth only
    connector = Connector()
    
    def getconn():
        return connector.connect(
            "zinc-strategy-446518-s7:us-central1:letscoach-dev",
            "pymysql",
            user="me",
            password="Ab123456",
            db="main_game",
            enable_iam_auth=False,  # ⚠️ חשוב! ללא IAM
        )
    
    # Create engine
    engine = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
    )
    
    print("✅ התחברות הצליחה!")
    
    # Query the database
    print(f"\n📊 שולף נתונים על המשחק הבא...")
    
    with engine.connect() as conn:
        # קבל את ה-match_day הבא
        result = conn.execute(text("""
            SELECT MIN(match_day) as next_match_day 
            FROM matches 
            WHERE match_result IS NULL
        """)).fetchone()
        
        next_match_day = result[0] if result and result[0] else 1
        print(f"🎯 Match Day הבא: {next_match_day}")
        
        # שלוף משחקים
        query = text(f"""
            SELECT 
                m.*,
                ht.team_name as home_team_name,
                at.team_name as away_team_name,
                l.league_name
            FROM matches m
            LEFT JOIN teams ht ON m.home_team_id = ht.team_id
            LEFT JOIN teams at ON m.away_team_id = at.team_id
            LEFT JOIN leagues l ON m.league_id = l.league_id
            WHERE m.match_day = {next_match_day}
            ORDER BY m.match_datetime
            LIMIT 5
        """)
        
        results = conn.execute(query).fetchall()
        
        if not results:
            print(f"\n❌ לא נמצאו משחקים ל-match_day {next_match_day}")
        else:
            print(f"\n✅ נמצאו {len(results)} משחקים ל-match_day {next_match_day}:")
            print("\n" + "="*80)
            
            for i, row in enumerate(results, 1):
                match = row._asdict()
                print(f"\n🏆 משחק #{i}:")
                print(f"   Match ID: {match['match_id']}")
                print(f"   📅 תאריך: {match['match_datetime']}")
                print(f"   🏟️  ליגה: {match.get('league_name', 'N/A')} (ID: {match['league_id']})")
                print(f"   🏠 בית: {match.get('home_team_name', 'Unknown')} (ID: {match['home_team_id']})")
                print(f"   ✈️  חוץ: {match.get('away_team_name', 'Unknown')} (ID: {match['away_team_id']})")
                print(f"   📊 סטטוס: {match.get('match_result', 'טרם שוחק')}")
                print(f"   🎮 סוג משחק: {match.get('kind', 'N/A')}")
                
            print("\n" + "="*80)
            
            # המשחק הראשון
            first = results[0]._asdict()
            print(f"\n🎯 המשחק הבא להרצה:")
            print(f"   Match ID: {first['match_id']}")
            print(f"   {first.get('home_team_name')} vs {first.get('away_team_name')}")
    
    connector.close()
    print(f"\n✅ סיימתי!")
    
except Exception as e:
    print(f"\n❌ שגיאה: {e}")
    import traceback
    traceback.print_exc()
