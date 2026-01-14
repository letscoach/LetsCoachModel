#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 DEBUG TEST RUNNER
Run KIND 1 vs KIND 2 matches with logging to easily compare
"""

import subprocess
import sys
import datetime

print("\n" + "="*80)
print("  🎮 DEBUG TEST RUNNER - KIND FACTOR COMPARISON")
print("="*80)
print(f"\nתאריך: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

print("📋 Instructions:")
print("1. Make sure you have 2 players with:")
print("   - Same Endurance (recommend: 50)")
print("   - Freshness reset to 100")
print("   - Same team")
print("")
print("2. Create 2 matches:")
print("   - MATCH 1: KIND 1 (League) - get match_id and update match_ids below")
print("   - MATCH 2: KIND 2 (Friendly) - get match_id and update match_ids below")
print("")
print("3. Run this script to see detailed logs\n")

# Configuration - UPDATE THESE AFTER CREATING MATCHES
MATCH_ID_KIND1 = None  # Set to KIND 1 match_id
MATCH_ID_KIND2 = None  # Set to KIND 2 match_id

if MATCH_ID_KIND1 is None or MATCH_ID_KIND2 is None:
    print("❌ ERROR: Update MATCH_ID_KIND1 and MATCH_ID_KIND2 in this script")
    print("\nHow to get match IDs:")
    print("1. Create match in database")
    print("2. Query: SELECT match_id FROM matches WHERE kind = 1 ORDER BY created_at DESC LIMIT 1")
    sys.exit(1)

print(f"🎯 Test Setup:")
print(f"   - KIND 1 (League) Match ID: {MATCH_ID_KIND1}")
print(f"   - KIND 2 (Friendly) Match ID: {MATCH_ID_KIND2}")

input("\n⏳ Press Enter to run debug test...\n")

# Create a Python script to run matches with logging
test_script = f"""
import sys
sys.path.insert(0, '.')
from Helpers.SQL_db import exec_update_query, exec_select_query
from Game.Matches import game_launcher

print("\\n" + "="*80)
print("  TEST 1: KIND 1 (LEAGUE) MATCH")
print("="*80)
match_1 = exec_select_query("SELECT * FROM matches WHERE match_id = {MATCH_ID_KIND1}")
if match_1:
    result_1 = game_launcher(match_1[0])
    print(f"\\n✅ Match completed\\n")

print("\\n" + "="*80)
print("  TEST 2: KIND 2 (FRIENDLY) MATCH")
print("="*80)
match_2 = exec_select_query("SELECT * FROM matches WHERE match_id = {MATCH_ID_KIND2}")
if match_2:
    result_2 = game_launcher(match_2[0])
    print(f"\\n✅ Match completed\\n")
"""

# Run the test
try:
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        cwd=".",
        capture_output=False,
        text=True
    )
except Exception as e:
    print(f"❌ Error running test: {e}")

print("\n" + "="*80)
print("  ✨ TEST COMPLETE")
print("="*80)
print("\n📊 Check the logs above for:")
print("   1. 📊 CALCULATION - Is Factor different?")
print("   2. 📌 BEFORE DB INSERT - Is Delta different?")
print("   3. 🔄 DB UPDATE - What value was sent?")
print("\n💾 To save logs to file:")
print("   python run_match_manual.py > match_debug.log 2>&1")
print("")
