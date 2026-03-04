#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
סקריפט לבדיקת הימורים במשחק ידידות מקצה לקצה
"""
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set DEV environment
os.environ['SQL_INSTANCE'] = 'zinc-strategy-446518-s7:us-central1:letscoach-dev'

from Helpers.SQL_db import (
    exec_select_query, 
    get_match_betting_info,
    process_friendly_match_betting
)

def check_pending_friendly_matches():
    """מציאת כל משחקי הידידות שממתינים להרצה"""
    query = """
        SELECT m.match_id, m.home_team_id, m.away_team_id, m.bet_amount, m.kind,
               m.match_datetime, m.result,
               ht.user_id as home_owner, at.user_id as away_owner
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.team_id
        JOIN teams at ON m.away_team_id = at.team_id
        WHERE m.kind = 2
        AND m.result IS NULL
        ORDER BY m.match_datetime DESC
        LIMIT 10
    """
    matches = exec_select_query(query)
    return matches

def check_user_balance(user_id):
    """בדיקת יתרת משתמש מסכום הטרנזקציות"""
    query = f"SELECT COALESCE(SUM(amount), 0) as balance FROM transactions WHERE user_id = '{user_id}'"
    result = exec_select_query(query)
    if result:
        return result[0].get('balance', 0)
    return 0

def check_transactions(user_id, limit=5):
    """בדיקת טרנזקציות אחרונות של משתמש"""
    query = f"""
        SELECT id, amount, transaction_type, description, timestamp
        FROM transactions
        WHERE user_id = '{user_id}'
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    return exec_select_query(query)

def run_friendly_match(match_id):
    """הרצת משחק ידידות ספציפי"""
    from Game.Matches import game_launcher
    
    # קבלת פרטי המשחק
    query = f"""
        SELECT m.*, ht.user_id as home_owner, at.user_id as away_owner
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.team_id
        JOIN teams at ON m.away_team_id = at.team_id
        WHERE m.match_id = {match_id}
    """
    matches = exec_select_query(query)
    if not matches:
        print(f"❌ משחק {match_id} לא נמצא")
        return None
    
    match = matches[0]
    print(f"\n🎮 מריץ משחק ידידות {match_id}")
    print(f"   {match['home_team_id']} vs {match['away_team_id']}")
    print(f"   הימור: {match.get('bet_amount', 0)} coins")
    
    # שמירת יתרות לפני המשחק
    home_balance_before = check_user_balance(match['home_owner'])
    away_balance_before = check_user_balance(match['away_owner'])
    print(f"\n💰 יתרות לפני המשחק:")
    print(f"   Home ({match['home_owner']}): {home_balance_before}")
    print(f"   Away ({match['away_owner']}): {away_balance_before}")
    
    # הרצת המשחק
    result = game_launcher(match)
    print(f"\n⚽ תוצאה: {result}")
    
    # בדיקת יתרות אחרי המשחק
    home_balance_after = check_user_balance(match['home_owner'])
    away_balance_after = check_user_balance(match['away_owner'])
    print(f"\n💰 יתרות אחרי המשחק:")
    home_diff = float(home_balance_after) - float(home_balance_before)
    away_diff = float(away_balance_after) - float(away_balance_before)
    print(f"   Home ({match['home_owner'][:20]}...): {home_balance_after} (שינוי: {home_diff:+.0f})")
    print(f"   Away ({match['away_owner'][:20]}...): {away_balance_after} (שינוי: {away_diff:+.0f})")
    
    # בדיקת טרנזקציות
    print(f"\n📝 טרנזקציות אחרונות Home:")
    for tx in check_transactions(match['home_owner'], 3):
        print(f"   {tx['transaction_type']}: {tx['amount']} - {tx.get('description', 'N/A')}")
    
    print(f"\n📝 טרנזקציות אחרונות Away:")
    for tx in check_transactions(match['away_owner'], 3):
        print(f"   {tx['transaction_type']}: {tx['amount']} - {tx.get('description', 'N/A')}")
    
    return result

def main():
    print("=" * 60)
    print("🎲 בדיקת הימורים במשחקי ידידות - End to End")
    print("=" * 60)
    
    # מציאת משחקים ממתינים
    print("\n🔍 מחפש משחקי ידידות ממתינים...")
    pending = check_pending_friendly_matches()
    
    if not pending:
        print("❌ אין משחקי ידידות ממתינים")
        print("\n💡 כדי לבדוק:")
        print("   1. פתח את הממשק http://localhost:5173")
        print("   2. צור משחק ידידות עם הימור")
        print("   3. הצטרף עם משתמש אחר")
        print("   4. הרץ את הסקריפט הזה שוב")
        return
    
    print(f"\n✅ נמצאו {len(pending)} משחקי ידידות ממתינים:")
    for i, m in enumerate(pending, 1):
        bet = m.get('bet_amount', 0) or 0
        print(f"   {i}. Match {m['match_id']}: Team {m['home_team_id']} vs Team {m['away_team_id']} | Bet: {bet} coins")
    
    # בחירת משחק להרצה
    if len(sys.argv) > 1:
        match_id = int(sys.argv[1])
    else:
        match_id = pending[0]['match_id']
        print(f"\n🎯 משתמש במשחק הראשון: {match_id}")
        print("   (ניתן להעביר match_id כפרמטר: python test_betting_e2e.py <match_id>)")
    
    # הרצת המשחק
    print("\n" + "-" * 60)
    run_friendly_match(match_id)
    print("-" * 60)
    print("\n✅ הבדיקה הסתיימה!")

if __name__ == "__main__":
    main()
