"""
Full end-to-end test - Run competition and save to DB
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Competitions.dash100 import Dash100
from Competitions.dash5k import Run5k
from Competitions.penalty_shootout import PenaltyShootout
from Helpers import SQL_db as db
import json

def test_full_flow(comp_type):
    """
    Test full competition flow:
    1. Run competition
    2. Calculate attribute changes
    3. Save to DB
    4. Verify in DB
    """
    
    competition_id = input(f"Enter {comp_type} competition_id: ")
    
    print(f"\n{'='*70}")
    print(f"🎯 Testing {comp_type} - Full Flow")
    print(f"Competition ID: {competition_id}")
    print(f"{'='*70}\n")
    
    try:
        # Step 1: Create competition instance
        print("📋 Step 1: Creating competition instance...")
        if comp_type == "Dash100":
            comp = Dash100(competition_id=competition_id)
        elif comp_type == "Run5K":
            comp = Run5k(competition_id=competition_id)
        elif comp_type == "PenaltyShootout":
            comp = PenaltyShootout(competition_id=competition_id)
        else:
            print("❌ Invalid competition type")
            return False
        
        print(f"✅ Competition created with {len(comp.participants)} participants")
        
        # Step 2: Run competition
        print("\n🏁 Step 2: Running competition simulation...")
        results = comp.run_competition()
        print(f"✅ Competition completed with {len(results)} results")
        
        # Show top 3 results
        print("\n🏆 Top 3 Results:")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. Token: {result['token']}")
            print(f"     Score: {result['score']}")
            print(f"     Rank: {result['rank_position']}")
        
        if comp_type == "PenaltyShootout":
            gk_info = comp.get_goalkeeper_rewards()
            print(f"\n🥅 Goalkeeper: {gk_info['goalkeeper_name']}")
            print(f"   Total Saves: {gk_info['total_saves']}")
        
        # Step 3: Calculate attribute changes
        print("\n📊 Step 3: Calculating attribute changes...")
        attr_changes = comp.calculate_attribute_changes()
        print(f"✅ Calculated changes for {len(attr_changes)} players")
        
        # Show sample
        sample_token = list(attr_changes.keys())[0]
        print(f"\n📝 Sample change for {sample_token}:")
        print(json.dumps(attr_changes[sample_token], indent=2))
        
        # Step 4: Save to DB
        print("\n💾 Step 4: Saving to database...")
        confirm = input("⚠️  Save to DB? (yes/no): ").strip().lower()
        
        if confirm == "yes":
            success, errors = db.insert_player_attributes_competition_effected(
                attr_changes, 
                competition_id
            )
            print(f"✅ Database save complete:")
            print(f"   Success: {success}")
            print(f"   Errors: {errors}")
            
            # Step 5: Verify in DB
            print("\n🔍 Step 5: Verifying data in DB...")
            query = f"""
                SELECT token, score, rank_position, is_winner 
                FROM `main_game`.`competition_results` 
                WHERE competition_id = {competition_id}
                ORDER BY rank_position
                LIMIT 5
            """
            
            print(f"\n📋 Running query:\n{query}\n")
            db_results = db.exec_select_query(query)
            
            if db_results:
                print("✅ Data verified in DB:")
                for row in db_results:
                    if isinstance(row, dict):
                        print(f"   Token: {row['token']}")
                        print(f"   Score: {row['score']}")
                        print(f"   Rank: {row['rank_position']}")
                        print(f"   Winner: {row['is_winner']}")
                        print()
                    else:
                        print(f"   {row}")
            else:
                print("⚠️  No data found in DB")
            
            # Step 6: Distribute prizes
            print("\n💰 Step 6: Distributing prizes...")
            comp_type_id = 1 if comp_type == "Dash100" else (2 if comp_type == "Run5K" else 3)
            prize_confirm = input("Distribute prizes? (yes/no): ").strip().lower()
            
            if prize_confirm == "yes":
                prize_result = db.distribute_competition_prizes(competition_id, comp_type_id)
                print(f"✅ Prize distribution: {prize_result}")
            else:
                print("⏭️  Skipped prize distribution")
        else:
            print("⏭️  Skipped database save")
        
        print(f"\n{'='*70}")
        print("✅ Full flow test completed successfully!")
        print(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("""
    🧪 Full Competition Flow Test
    ==============================
    
    This will test the complete flow:
    1. Run competition simulation
    2. Calculate attribute changes
    3. Save results to DB
    4. Verify data in DB
    5. Distribute prizes
    
    Choose competition type:
    1. Dash100 (100m sprint)
    2. Run5K (5km run)
    3. PenaltyShootout
    4. Exit
    """)
    
    choice = input("Enter choice (1-4): ").strip()
    
    comp_types = {
        "1": "Dash100",
        "2": "Run5K",
        "3": "PenaltyShootout"
    }
    
    if choice in comp_types:
        test_full_flow(comp_types[choice])
    elif choice == "4":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
