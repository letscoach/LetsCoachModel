"""
Locking mechanism to prevent race conditions in competition execution
"""
import time
from Helpers.SQL_db import exec_select_query, exec_update_query

def acquire_competition_lock(competition_id, timeout=30):
    """
    Try to acquire a lock on the competition.
    Returns True if lock acquired, False otherwise.
    
    Uses database row locking via SELECT FOR UPDATE
    """
    try:
        # Try to acquire lock
        query = f"""
        SELECT id, status_id 
        FROM competitions 
        WHERE id = {competition_id} 
        AND status_id = 14
        FOR UPDATE NOWAIT
        """
        result = exec_select_query(query)
        
        if result and len(result) > 0:
            print(f"🔒 Lock acquired for competition {competition_id}")
            return True
        else:
            print(f"⚠️ Competition {competition_id} not available for locking")
            return False
            
    except Exception as e:
        print(f"❌ Failed to acquire lock for competition {competition_id}: {e}")
        return False

def check_competition_already_running(competition_id):
    """
    Check if competition is already being processed
    by checking if status changed very recently (last 60 seconds)
    """
    query = f"""
    SELECT 
        id,
        status_id,
        end_time,
        TIMESTAMPDIFF(SECOND, end_time, NOW()) as seconds_since_end
    FROM competitions
    WHERE id = {competition_id}
    """
    result = exec_select_query(query)
    
    if result and len(result) > 0:
        comp = result[0]
        # If status is 15 (closed) and end_time was set in last 60 seconds
        if comp.get('status_id') == 15:
            seconds_since_end = comp.get('seconds_since_end', 999)
            if seconds_since_end is not None and seconds_since_end < 60:
                print(f"⚠️ Competition {competition_id} was just completed {seconds_since_end}s ago - likely race condition!")
                return True
    
    return False
