"""
Quick DB Query Tool - Interactive DB explorer
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Helpers import SQL_db as db
import json

def run_query(query):
    """Run a query and display results"""
    try:
        print(f"\n🔍 Running query:\n{query}\n")
        results = db.exec_select_query(query)
        
        if not results:
            print("❌ No results found")
            return
        
        print(f"✅ Found {len(results)} rows:\n")
        
        # Display results
        for i, row in enumerate(results, 1):
            if isinstance(row, dict):
                print(f"Row {i}:")
                for key, value in row.items():
                    print(f"  {key}: {value}")
                print()
            else:
                print(f"Row {i}: {row}")
        
        return results
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("""
    🗄️  Quick DB Query Tool
    =======================
    
    Choose an option:
    
    1. Show all competitions
    2. Show competition participants
    3. Show competition results
    4. Show players
    5. Show competition types
    6. Custom query
    7. Exit
    """)
    
    choice = input("Enter choice (1-7): ").strip()
    
    if choice == "1":
        query = """
        SELECT 
            c.id,
            ct.name AS type_name,
            c.status_id,
            c.start_time,
            c.end_time,
            COUNT(cp.token) AS participants
        FROM `main_game`.`competitions` c
        LEFT JOIN `main_game`.`competition_types` ct ON c.competition_type_id = ct.id
        LEFT JOIN `main_game`.`competition_participants` cp ON c.id = cp.competition_id
        GROUP BY c.id, ct.name, c.status_id, c.start_time, c.end_time
        ORDER BY c.id DESC
        LIMIT 20
        """
        run_query(query)
        
    elif choice == "2":
        comp_id = input("Enter competition_id: ")
        query = f"""
        SELECT 
            cp.token,
            p.name
        FROM `main_game`.`competition_participants` cp
        LEFT JOIN `main_game`.`players` p ON cp.token = p.token
        WHERE cp.competition_id = {comp_id}
        """
        run_query(query)
        
    elif choice == "3":
        comp_id = input("Enter competition_id: ")
        query = f"""
        SELECT 
            token,
            score,
            rank_position,
            is_winner
        FROM `main_game`.`competition_results`
        WHERE competition_id = {comp_id}
        ORDER BY rank_position
        """
        run_query(query)
        
    elif choice == "4":
        query = """
        SELECT token, name 
        FROM `main_game`.`players` 
        LIMIT 20
        """
        run_query(query)
        
    elif choice == "5":
        query = """
        SELECT * FROM `main_game`.`competition_types`
        """
        run_query(query)
        
    elif choice == "6":
        print("\nEnter your SQL query (end with semicolon on a new line):")
        lines = []
        while True:
            line = input()
            if line.strip().endswith(';'):
                lines.append(line)
                break
            lines.append(line)
        
        query = '\n'.join(lines)
        run_query(query)
        
    elif choice == "7":
        print("Goodbye!")
        return
    else:
        print("Invalid choice")


if __name__ == "__main__":
    while True:
        try:
            main()
            print("\n" + "="*50 + "\n")
            again = input("Run another query? (yes/no): ").strip().lower()
            if again != 'yes':
                break
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
