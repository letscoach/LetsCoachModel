"""
Test script to verify competition score changes
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Competitions.dash100 import Dash100
from Competitions.dash5k import Run5k
from Competitions.penalty_shootout import PenaltyShootout
import json

def test_dash100():
    print("\n" + "="*70)
    print("🏃 Testing Dash100 Competition")
    print("="*70)
    
    # Replace with actual competition_id from your DB
    competition_id = input("Enter Dash100 competition_id to test: ")
    
    try:
        comp = Dash100(competition_id=competition_id)
        results = comp.run_competition()
        
        print("\n📊 Results:")
        for i, result in enumerate(results[:5], 1):  # Show top 5
            print(f"{i}. Token: {result['token']}")
            print(f"   Score: {result['score']}")
            print(f"   Rank: {result['rank_position']}")
            print(f"   DNF: {result.get('dnf', False)}")
            print()
        
        # Check attribute changes format
        attr_changes = comp.calculate_attribute_changes()
        first_player = list(attr_changes.values())[0]
        print("✅ Sample attribute change:")
        print(json.dumps(first_player, indent=2))
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_run5k():
    print("\n" + "="*70)
    print("🏃‍♂️ Testing Run5K Competition")
    print("="*70)
    
    competition_id = input("Enter Run5K competition_id to test: ")
    
    try:
        comp = Run5k(competition_id=competition_id)
        results = comp.run_competition()
        
        print("\n📊 Results:")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. Token: {result['token']}")
            print(f"   Score: {result['score']}")
            print(f"   Rank: {result['rank_position']}")
            print(f"   DNF: {result.get('dnf', False)}")
            print()
        
        attr_changes = comp.calculate_attribute_changes()
        first_player = list(attr_changes.values())[0]
        print("✅ Sample attribute change:")
        print(json.dumps(first_player, indent=2))
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_penalty_shootout():
    print("\n" + "="*70)
    print("⚽ Testing PenaltyShootout Competition")
    print("="*70)
    
    competition_id = input("Enter PenaltyShootout competition_id to test: ")
    
    try:
        comp = PenaltyShootout(competition_id=competition_id)
        results = comp.run_competition()
        
        print("\n📊 Results:")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. Token: {result['token']}")
            print(f"   Score: {result['score']}")
            print(f"   Rank: {result['rank_position']}")
            print(f"   Goals: {result.get('total_goals', 'N/A')}")
            print(f"   Shots: {result.get('total_shots', 'N/A')}")
            print()
        
        # Check goalkeeper info
        gk_info = comp.get_goalkeeper_rewards()
        print("🥅 Goalkeeper Info:")
        print(json.dumps(gk_info, indent=2))
        
        attr_changes = comp.calculate_attribute_changes()
        
        # Show first player
        first_player = list(attr_changes.values())[0]
        print("\n✅ Sample kicker attribute change:")
        print(json.dumps(first_player, indent=2))
        
        # Show goalkeeper if exists
        gk_token = gk_info.get('goalkeeper_token')
        if gk_token and gk_token in attr_changes:
            print("\n🥅 Goalkeeper attribute change:")
            print(json.dumps(attr_changes[gk_token], indent=2))
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("""
    🧪 Competition Score Testing
    ============================
    
    This script tests the new score format changes:
    - Dash100: Shows time in seconds (e.g., "10.52s")
    - Run5K: Shows time in MM:SS format (e.g., "14:32")
    - PenaltyShootout: Shows goals/shots (e.g., "12/15")
    
    Choose a competition to test:
    1. Dash100 (100m sprint)
    2. Run5K (5km run)
    3. PenaltyShootout
    4. All (run all tests)
    5. Exit
    """)
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        test_dash100()
    elif choice == "2":
        test_run5k()
    elif choice == "3":
        test_penalty_shootout()
    elif choice == "4":
        print("\nRunning all tests...")
        test_dash100()
        test_run5k()
        test_penalty_shootout()
    elif choice == "5":
        print("Goodbye!")
        return
    else:
        print("Invalid choice")
        return
    
    print("\n" + "="*70)
    print("✅ Test completed!")
    print("="*70)


if __name__ == "__main__":
    main()
