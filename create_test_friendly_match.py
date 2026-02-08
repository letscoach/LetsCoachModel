#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
יצירת משחק ידידות עם הימור לצורך בדיקה
"""
import sys
import io
import os
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ['SQL_INSTANCE'] = 'zinc-strategy-446518-s7:us-central1:letscoach-dev'

from Helpers.SQL_db import exec_select_query, exec_update_query

def create_friendly_match_with_bet(home_team_id, away_team_id, bet_amount=100):
    """יצירת משחק ידידות עם הימור"""
    # זמן המשחק - עכשיו (כדי שיהיה אפשר להריץ מיד)
    match_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    query = f"""
        INSERT INTO matches (home_team_id, away_team_id, match_datetime, match_day, kind, bet_amount)
        VALUES ({home_team_id}, {away_team_id}, '{match_datetime}', 0, 2, {bet_amount})
    """
    
    try:
        exec_update_query(query)
        # קבלת ה-match_id שנוצר
        result = exec_select_query("SELECT LAST_INSERT_ID() as match_id")
        match_id = result[0]['match_id'] if result else None
        return match_id
    except Exception as e:
        print(f"❌ שגיאה ביצירת המשחק: {e}")
        return None

def add_bet_transactions(home_user_id, away_user_id, match_id, bet_amount):
    """הוספת טרנזקציות חיוב להימור (כמו שהBackend עושה)"""
    queries = [
        f"""
        INSERT INTO transactions (user_id, token_coin_id, amount, description, transaction_type)
        VALUES ('{home_user_id}', 1, -{bet_amount}, 'Friendly Match Bet Entry (Match #{match_id})', 'debit')
        """,
        f"""
        INSERT INTO transactions (user_id, token_coin_id, amount, description, transaction_type)
        VALUES ('{away_user_id}', 1, -{bet_amount}, 'Friendly Match Bet Entry (Match #{match_id})', 'debit')
        """
    ]
    
    try:
        for q in queries:
            exec_update_query(q)
        return True
    except Exception as e:
        print(f"❌ שגיאה בהוספת טרנזקציות: {e}")
        return False

def main():
    print("=" * 60)
    print("🎲 יצירת משחק ידידות עם הימור לבדיקה")
    print("=" * 60)
    
    # קבוצות לבדיקה
    home_team_id = 229  # ET - dev (LC0ed65f7614999a61706e60e7a4cf4f582ac469)
    away_team_id = 226  # אאא (0xa6f77ca8c8f30b3a9621b8f01504f33968aa5041)
    bet_amount = 150    # סכום ההימור
    
    home_user_id = 'LC0ed65f7614999a61706e60e7a4cf4f582ac469'
    away_user_id = '0xa6f77ca8c8f30b3a9621b8f01504f33968aa5041'
    
    print(f"\n📋 פרטי המשחק:")
    print(f"   Home: Team {home_team_id} (User: {home_user_id[:20]}...)")
    print(f"   Away: Team {away_team_id} (User: {away_user_id[:20]}...)")
    print(f"   Bet Amount: {bet_amount} coins")
    
    # יצירת המשחק
    print(f"\n🎮 יוצר משחק ידידות...")
    match_id = create_friendly_match_with_bet(home_team_id, away_team_id, bet_amount)
    
    if not match_id:
        print("❌ נכשל ביצירת המשחק")
        return
    
    print(f"✅ נוצר משחק #{match_id}")
    
    # הוספת טרנזקציות חיוב (סימולציה של מה שה-Backend עושה)
    print(f"\n💸 מוסיף טרנזקציות חיוב...")
    if add_bet_transactions(home_user_id, away_user_id, match_id, bet_amount):
        print(f"✅ שני המשתמשים חויבו {bet_amount} coins כל אחד")
    
    print(f"\n" + "=" * 60)
    print(f"✅ המשחק מוכן להרצה!")
    print(f"   הרץ: python test_betting_e2e.py {match_id}")
    print(f"=" * 60)

if __name__ == "__main__":
    main()
