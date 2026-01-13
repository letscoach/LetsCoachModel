
import Helpers.SQL_db as db

# שאילתה ספציפית למשחקים הבעייתיים שציינת
query = "SELECT match_id, away_team_id FROM matches WHERE match_id IN (745, 746)"

try:
    print("--- Connecting to DB and fetching matches ---")
    results = db.exec_select_query(query)
    
    for row in results:
        # המרה ל-dict אם התוצאה היא RowProxy או משהו דומה
        if hasattr(row, '_asdict'):
            row_dict = row._asdict()
        else:
            row_dict = dict(row)
            
        match_id = row_dict.get('match_id')
        away_team = row_dict.get('away_team_id')
        
        print(f"Match ID: {match_id}")
        print(f"Away Team Value: {away_team}")
        print(f"Away Team Type: {type(away_team)}")
        print(f"Is None? {away_team is None}")
        print("-------------------------------------")

except Exception as e:
    print(f"Error: {e}")
