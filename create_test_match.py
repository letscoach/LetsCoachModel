#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
סקריפט ליצירת משחק בודד וודא ש-kind נשמר נכון
"""
import sys
import os

from datetime import datetime, timedelta

print("🎮 יוצר משחק חדש לבדיקה...")

# התחברות ישירה ל-Google Cloud SQL
try:
    from google.cloud.sql.connector import Connector
    import sqlalchemy
    from sqlalchemy import text
    
    print(f"\n🔌 מתחבר ל-Google Cloud SQL...")
    
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
    
    engine = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
        pool_pre_ping=True,
    )
    
    print("✅ התחברות הצליחה!")
    
    # צור משחק בודד
    new_match = {
        "league_id": 1,
        "match_day": 999,
        "home_team_id": 1,
        "away_team_id": 2,
        "match_datetime": datetime.now() + timedelta(hours=1),
        "kind": 1
    }
    
    print(f"\n📊 פרטי המשחק:")
    print(f"   League ID: {new_match['league_id']}")
    print(f"   Match Day: {new_match['match_day']}")
    print(f"   Home Team: {new_match['home_team_id']}")
    print(f"   Away Team: {new_match['away_team_id']}")
    print(f"   DateTime: {new_match['match_datetime']}")
    print(f"   Kind: {new_match['kind']} (1 = League)")
    
    # שמור ב-DB
    print(f"\n💾 שומר את המשחק ב-DB...")
    
    with engine.connect() as conn:
        # Insert query
        query = text("""
            INSERT INTO matches (league_id, match_day, home_team_id, away_team_id, match_datetime, kind)
            VALUES (:league_id, :match_day, :home_team_id, :away_team_id, :match_datetime, :kind)
        """)
        
        result = conn.execute(query, new_match)
        conn.commit()
        match_id = result.lastrowid
        
        print(f"✅ המשחק נשמר בהצלחה!")
        print(f"   Match ID: {match_id}")
        
        # וודא שהמשחק נשמר עם kind=1
        print(f"\n🔍 מאמת שהמשחק נשמר עם kind=1...")
        
        verify_query = text("""
            SELECT match_id, league_id, match_day, home_team_id, away_team_id, kind
            FROM matches
            WHERE match_id = :match_id
        """)
        
        saved = conn.execute(verify_query, {"match_id": match_id}).fetchone()
        
        if saved:
            print(f"\n📋 המשחק שנשמר:")
            print(f"   Match ID: {saved.match_id}")
            print(f"   League ID: {saved.league_id}")
            print(f"   Match Day: {saved.match_day}")
            print(f"   Home Team: {saved.home_team_id}")
            print(f"   Away Team: {saved.away_team_id}")
            print(f"   Kind: {saved.kind} {'✅' if saved.kind == 1 else '❌'}")
            
            if saved.kind == 1:
                print(f"\n🎉 מעולה! השדה kind נשמר כראוי!")
                print(f"\n🎮 כעת אפשר להריץ את המשחק עם:")
                print(f"   Match ID: {match_id}")
            else:
                print(f"\n❌ שגיאה! השדה kind לא נשמר כראוי")
                print(f"   ערך שנשמר: {saved.kind}")
        else:
            print(f"❌ לא מצאתי את המשחק!")
    
    connector.close()
    
except Exception as e:
    print(f"\n❌ שגיאה: {e}")
    import traceback
    traceback.print_exc()
