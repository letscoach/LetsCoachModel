#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduler להרצת משחקים אוטומטית בזמנים קבועים
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from Helpers import SQL_db as db
from Helpers.telegram_manager import send_log_message
from Game.Matches import game_launcher

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def run_scheduled_matches():
    """
    פונקציה שמריצה את כל המשחקים שצריכים להתחיל כעת
    """
    try:
        send_log_message("🔄 Scheduler: בדיקת משחקים לריצה...")
        
        # קבל את כל המשחקים שצריכים להתחיל בזמן הזה
        matches = db.get_current_matches()
        
        if not matches:
            logger.info("אין משחקים לריצה כרגע")
            send_log_message("✅ Scheduler: לא נמצאו משחקים לריצה")
            return
        
        logger.info(f"נמצאו {len(matches)} משחקים לריצה")
        send_log_message(f"📋 Scheduler: נמצאו {len(matches)} משחקים לריצה")
        
        # ריצה של כל משחק
        for match in matches:
            try:
                match_id = match.get('match_id', 'Unknown')
                home_team = match.get('home_team_id', 'Unknown')
                away_team = match.get('away_team_id', 'Unknown')
                
                logger.info(f"🎮 מריץ משחק {match_id}: {home_team} vs {away_team}")
                send_log_message(f"▶️ Scheduler: מריץ משחק {match_id}")
                
                # הוסף את 'kind' אם לא קיים
                if 'kind' not in match:
                    match['kind'] = 'league'
                
                # הרץ את המשחק
                result = game_launcher(match)
                
                logger.info(f"✅ משחק {match_id} הסתיים בהצלחה")
                send_log_message(f"✅ Scheduler: משחק {match_id} הסתיים")
                
            except Exception as e:
                logger.error(f"❌ שגיאה במשחק {match.get('match_id', 'Unknown')}: {e}")
                send_log_message(f"❌ Scheduler: שגיאה במשחק {match.get('match_id', 'Unknown')}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"❌ שגיאה כללית בScheduler: {e}")
        send_log_message(f"❌ Scheduler: שגיאה כללית: {e}")


class MatchScheduler:
    """
    מנהל Scheduler להרצת משחקים אוטומטית
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self, check_interval_minutes=5):
        """
        התחל את הScheduler
        
        :param check_interval_minutes: כל כמה דקות לבדוק משחקים (ברירת מחדל: 5)
        """
        if self.is_running:
            logger.warning("Scheduler כבר רץ")
            return
        
        try:
            # הוסף job שמריץ כל X דקות
            self.scheduler.add_job(
                run_scheduled_matches,
                CronTrigger(minute=f'*/{check_interval_minutes}'),  # כל X דקות
                id='match_scheduler',
                name='Scheduled Match Runner',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info(f"✅ Scheduler התחיל - בדיקה כל {check_interval_minutes} דקות")
            send_log_message(f"✅ Scheduler התחיל - בדיקה כל {check_interval_minutes} דקות")
            
        except Exception as e:
            logger.error(f"❌ שגיאה בהתחלת Scheduler: {e}")
            send_log_message(f"❌ שגיאה בהתחלת Scheduler: {e}")
    
    def stop(self):
        """עצור את הScheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler עוצר")
            send_log_message("⏹️ Scheduler עוצר")
    
    def pause(self):
        """השהה את הScheduler"""
        if self.is_running:
            self.scheduler.pause()
            logger.info("Scheduler משהוי")
            send_log_message("⏸️ Scheduler משהוי")
    
    def resume(self):
        """המשך את הScheduler"""
        if self.is_running:
            self.scheduler.resume()
            logger.info("Scheduler מתחדש")
            send_log_message("▶️ Scheduler מתחדש")
    
    def get_jobs(self):
        """קבל את כל ה-jobs הפעילים"""
        return self.scheduler.get_jobs()


# יצור instance גלובלי של המScheduler
match_scheduler = MatchScheduler()


if __name__ == "__main__":
    # דוגמה לשימוש
    print("🚀 התחלת Scheduler...")
    match_scheduler.start(check_interval_minutes=5)
    
    try:
        # תן לScheduler לרוץ
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ עצירת Scheduler...")
        match_scheduler.stop()
        print("✅ Scheduler עוצר")
