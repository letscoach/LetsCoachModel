#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Direct Database Connection Check
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import pymysql
    import json
    
    # Read SQL credentials directly
    with open('c:\\Users\\gideo\\PycharmProjects\\LetsCoachBackend\\sql_cred.json', 'r') as f:
        creds = json.load(f)
    
    print("🔍 Connecting to MySQL database directly...\n")
    
    conn = pymysql.connect(
        host=creds.get('host'),
        user=creds.get('user'),
        password=creds.get('password'),
        database='main_game',
        cursorclass=pymysql.cursors.DictCursor,
        port=creds.get('port', 3306)
    )
    
    print("✅ Database connected!\n")
    print("="*80)
    print("  🎮 MATCH KINDS TABLE - FACTORS CHECK")
    print("="*80 + "\n")
    
    with conn.cursor() as cursor:
        # Query match_kinds table
        cursor.execute("""
            SELECT 
                id,
                name,
                attribute_delta_factor,
                freshness_delta_factor,
                satisfaction_delta_factor
            FROM match_kinds 
            ORDER BY id
        """)
        
        kinds = cursor.fetchall()
        
        if not kinds:
            print("❌ No match_kinds found!")
        else:
            print(f"📊 Found {len(kinds)} match types:\n")
            
            for kind in kinds:
                print(f"KIND {kind['id']}: {kind['name']}")
                print(f"  - attribute_delta_factor: {kind.get('attribute_delta_factor')}")
                print(f"  - freshness_delta_factor: {kind.get('freshness_delta_factor')}")
                print(f"  - satisfaction_delta_factor: {kind.get('satisfaction_delta_factor')}\n")
            
            # Verification
            print("─"*80)
            print("  ✨ FACTOR VERIFICATION\n")
            
            if len(kinds) >= 2:
                fresh_1 = float(kinds[0].get('freshness_delta_factor', 1.0))
                fresh_2 = float(kinds[1].get('freshness_delta_factor', 1.0))
                
                print(f"KIND 1 (League) freshness_delta_factor: {fresh_1}")
                print(f"KIND 2 (Friendly) freshness_delta_factor: {fresh_2}")
                
                if fresh_1 == fresh_2:
                    print(f"\n❌ PROBLEM FOUND:")
                    print(f"   Both kinds have the SAME factor: {fresh_1}")
                    print(f"   This explains identical freshness values!")
                    print(f"\n   🔧 ACTION NEEDED:")
                    print(f"   Update match_kinds table with different factors")
                else:
                    print(f"\n✅ Factors are different (as expected):")
                    print(f"   Ratio: KIND 2 is {fresh_2 / fresh_1:.2f}x of KIND 1")
                    
                    # Calculate expected difference
                    base = -22.5  # Simulated 90 min, endurance 50
                    expected_1 = base * fresh_1
                    expected_2 = base * fresh_2
                    diff = abs(expected_1 - expected_2)
                    
                    print(f"\n   Sample calculation (base delta = {base}):")
                    print(f"   KIND 1: {base} * {fresh_1} = {expected_1}")
                    print(f"   KIND 2: {base} * {fresh_2} = {expected_2}")
                    print(f"   Difference: {diff:.2f} points")
            
    conn.close()
    print("\n" + "="*80)
    
except FileNotFoundError:
    print("❌ sql_cred.json not found")
except ImportError as e:
    print(f"❌ Missing package: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
