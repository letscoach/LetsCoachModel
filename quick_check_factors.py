#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Quick Database Check for Kind Factors
Direct database query to verify factors
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Try to connect and check factors
try:
    import pymysql
    from google.cloud.sql.connector import Connector
    
    print("🔍 Attempting to connect to database...\n")
    
    connector = Connector()
    conn = connector.connect(
        "zinc-strategy-446518-s7:us-central1:letscoach-dev",
        "pymysql",
        user="me",
        password="Ab123456",
        db="main_game",
        cursorclass=pymysql.cursors.DictCursor,
        timeout=10
    )
    
    print("✅ Connected to database!\n")
    
    # Query the match_kinds table
    with conn.cursor() as cursor:
        print("="*80)
        print("  🎮 MATCH KINDS TABLE - FACTORS CHECK")
        print("="*80 + "\n")
        
        cursor.execute("SELECT * FROM match_kinds ORDER BY id")
        kinds = cursor.fetchall()
        
        if not kinds:
            print("❌ No match_kinds found in database!")
        else:
            print(f"📊 Found {len(kinds)} match types:\n")
            
            for kind in kinds:
                print(f"KIND {kind['id']}:")
                print(f"  - name: {kind.get('name', 'N/A')}")
                print(f"  - attribute_delta_factor: {kind.get('attribute_delta_factor')}")
                print(f"  - freshness_delta_factor: {kind.get('freshness_delta_factor')}")
                print(f"  - satisfaction_delta_factor: {kind.get('satisfaction_delta_factor')}")
                print()
        
        # Check if factors are correctly different
        print("─"*80)
        print("  ✨ FACTOR COMPARISON\n")
        
        if len(kinds) >= 2:
            fresh_1 = float(kinds[0].get('freshness_delta_factor', 1.0))
            fresh_2 = float(kinds[1].get('freshness_delta_factor', 1.0))
            
            if fresh_1 == fresh_2:
                print(f"❌ PROBLEM: KIND 1 and KIND 2 have SAME freshness factor!")
                print(f"   Both are: {fresh_1}")
                print(f"\n   This explains why freshness values are identical in results!")
            else:
                print(f"✅ Factors are DIFFERENT:")
                print(f"   KIND 1: {fresh_1}")
                print(f"   KIND 2: {fresh_2}")
                print(f"   Ratio: {fresh_2 / fresh_1:.2f}x")
                
                # Test calculation
                print(f"\n   Test calculation (90 mins, endurance 50):")
                base_delta = -22.5
                print(f"   KIND 1: {base_delta} * {fresh_1} = {base_delta * fresh_1}")
                print(f"   KIND 2: {base_delta} * {fresh_2} = {base_delta * fresh_2}")
                print(f"   Difference: {abs(base_delta * fresh_1 - base_delta * fresh_2):.2f} points")
        
        print("\n" + "="*80 + "\n")
    
    conn.close()
    
except ImportError as e:
    print(f"❌ Missing package: {e}")
    print("   Install with: pip install pymysql google-cloud-sql-python-connector")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
