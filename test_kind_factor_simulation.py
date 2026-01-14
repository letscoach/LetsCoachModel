#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Test Script for Kind Factor Simulation
Compares freshness changes for KIND 1 (League) vs KIND 2 (Friendly)
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'c:\\Users\\gideo\\PycharmProjects\\LetsCoachModel')

from Helpers import SQL_db as db
from Game.post_game import SatisfactionCalculator
import json

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_section(text):
    """Print a section header"""
    print(f"\n{'─'*80}")
    print(f"  {text}")
    print(f"{'─'*80}\n")

def run_simulation():
    print_header("🎮 KIND FACTOR SIMULATION - Freshness Delta Comparison")
    
    # Get match kind factors from database
    print_section("1️⃣  FETCHING MATCH KIND FACTORS FROM DATABASE")
    
    factors_1 = db.get_match_kind_factors(1)  # League
    factors_2 = db.get_match_kind_factors(2)  # Friendly
    factors_3 = db.get_match_kind_factors(3)  # Cup
    
    print(f"✅ KIND 1 (League)   Factors:")
    print(f"   - attribute_delta_factor: {factors_1.get('attribute_delta_factor')}")
    print(f"   - freshness_delta_factor: {factors_1.get('freshness_delta_factor')}")
    print(f"   - satisfaction_delta_factor: {factors_1.get('satisfaction_delta_factor')}")
    
    print(f"\n✅ KIND 2 (Friendly) Factors:")
    print(f"   - attribute_delta_factor: {factors_2.get('attribute_delta_factor')}")
    print(f"   - freshness_delta_factor: {factors_2.get('freshness_delta_factor')}")
    print(f"   - satisfaction_delta_factor: {factors_2.get('satisfaction_delta_factor')}")
    
    print(f"\n✅ KIND 3 (Cup)      Factors:")
    print(f"   - attribute_delta_factor: {factors_3.get('attribute_delta_factor')}")
    print(f"   - freshness_delta_factor: {factors_3.get('freshness_delta_factor')}")
    print(f"   - satisfaction_delta_factor: {factors_3.get('satisfaction_delta_factor')}")
    
    # Test freshness calculation formula
    print_section("2️⃣  TESTING FRESHNESS CALCULATION FORMULA")
    
    # Simulate player performance for 90 minutes with endurance 50
    endurance = 50
    minutes_played = 90
    extra_time_factor = 1.0
    
    base_freshness = 35 - (endurance / 4)
    freshness_per_minute = base_freshness / 90
    base_freshness_delta = -(base_freshness * (minutes_played / 90) * extra_time_factor)
    
    print(f"📊 Simulation Parameters:")
    print(f"   - Endurance: {endurance}")
    print(f"   - Minutes Played: {minutes_played}")
    print(f"   - Extra Time Factor: {extra_time_factor}")
    print(f"   - Base Freshness Loss: {base_freshness} ({35} - {endurance}/4)")
    print(f"   - Base Freshness Delta (raw): {base_freshness_delta}")
    
    # Calculate with factors
    freshness_kind1 = base_freshness_delta * factors_1['freshness_delta_factor']
    freshness_kind2 = base_freshness_delta * factors_2['freshness_delta_factor']
    freshness_kind3 = base_freshness_delta * factors_3['freshness_delta_factor']
    
    print(f"\n📈 Expected Freshness Delta After Factors:")
    print(f"   KIND 1 (League):   {base_freshness_delta} * {factors_1['freshness_delta_factor']} = {freshness_kind1}")
    print(f"   KIND 2 (Friendly): {base_freshness_delta} * {factors_2['freshness_delta_factor']} = {freshness_kind2}")
    print(f"   KIND 3 (Cup):      {base_freshness_delta} * {factors_3['freshness_delta_factor']} = {freshness_kind3}")
    
    print(f"\n💡 Expected Results (if freshness starts at 100):")
    print(f"   KIND 1: 100 + {freshness_kind1} = {100 + freshness_kind1}")
    print(f"   KIND 2: 100 + {freshness_kind2} = {100 + freshness_kind2}")
    print(f"   KIND 3: 100 + {freshness_kind3} = {100 + freshness_kind3}")
    
    difference_kind1_to_kind2 = abs(freshness_kind1 - freshness_kind2)
    print(f"\n🔍 Difference between KIND 1 and KIND 2: {difference_kind1_to_kind2}")
    
    # Test satisfaction calculation
    print_section("3️⃣  TESTING SATISFACTION CALCULATION")
    
    # Mock player results
    results = [
        {
            'player_id': 'test_player_1',
            'token': 'test_token_1',
            'team': 'home',
            'performance': {
                'overall_score': 7.5,
                'scored_goal': 1,
                'assist': 0,
                'defense_action': 2,
                'team_won': True,
                'minutes_played': 90
            }
        }
    ]
    
    # Test satisfaction for each kind
    satisfaction_kind1 = SatisfactionCalculator.calculate_satisfaction_changes(
        results, 
        team1_score=2, 
        team2_score=1, 
        man_of_the_match='test_player_1',
        factors=factors_1
    )
    
    satisfaction_kind2 = SatisfactionCalculator.calculate_satisfaction_changes(
        results, 
        team1_score=2, 
        team2_score=1, 
        man_of_the_match='test_player_1',
        factors=factors_2
    )
    
    satisfaction_kind3 = SatisfactionCalculator.calculate_satisfaction_changes(
        results, 
        team1_score=2, 
        team2_score=1, 
        man_of_the_match='test_player_1',
        factors=factors_3
    )
    
    print(f"📊 Satisfaction Changes (Team Won 2-1):")
    if satisfaction_kind1:
        player_sat_1 = next((s for s in satisfaction_kind1 if s['player_id'] == 'test_player_1'), None)
        if player_sat_1:
            print(f"   KIND 1 (League):   {player_sat_1.get('satisfaction_delta', 0)}")
    
    if satisfaction_kind2:
        player_sat_2 = next((s for s in satisfaction_kind2 if s['player_id'] == 'test_player_1'), None)
        if player_sat_2:
            print(f"   KIND 2 (Friendly): {player_sat_2.get('satisfaction_delta', 0)}")
    
    if satisfaction_kind3:
        player_sat_3 = next((s for s in satisfaction_kind3 if s['player_id'] == 'test_player_1'), None)
        if player_sat_3:
            print(f"   KIND 3 (Cup):      {player_sat_3.get('satisfaction_delta', 0)}")
    
    # Summary
    print_section("4️⃣  VERIFICATION SUMMARY")
    
    if factors_1['freshness_delta_factor'] == factors_2['freshness_delta_factor']:
        print(f"⚠️  WARNING: KIND 1 and KIND 2 have SAME freshness_delta_factor!")
        print(f"   This explains why fresh values are identical!")
    else:
        print(f"✅ Factors are different:")
        print(f"   KIND 1: {factors_1['freshness_delta_factor']}")
        print(f"   KIND 2: {factors_2['freshness_delta_factor']}")
    
    # Calculate expected difference
    expected_diff = abs(freshness_kind1 - freshness_kind2)
    if expected_diff > 0.01:
        print(f"\n✅ Formula expects {expected_diff:.2f} point difference between KIND 1 and KIND 2")
    else:
        print(f"\n❌ No difference in calculation - factors must be same in database!")
    
    print("\n" + "="*80)
    print("  ✨ Simulation Complete")
    print("="*80 + "\n")

if __name__ == '__main__':
    try:
        run_simulation()
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
