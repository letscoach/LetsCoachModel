#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduler להרצת משחקים ותחרויות אוטומטית בזמנים קבועים
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
                
                # וודא שיש 'kind' - אם לא, ברירת מחדל ל-League (1)
                if 'kind' not in match or match['kind'] is None:
                    match['kind'] = 1  # 1 = League match (not string!)
                
                # הרץ את המשחק
                result = game_launcher(match)
                
                logger.info(f"✅ משחק {match_id} הסתיים בהצלחה")
                send_log_message(f"✅ Scheduler: משחק {match_id} הסתיים")
                
            except Exception as e:
                logger.error(f"❌ שגיאה במשחק {match.get('match_id', 'Unknown')}: {e}")
                send_log_message(f"❌ Scheduler: שגיאה במשחק {match.get('match_id', 'Unknown')}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"❌ שגיאה כללית בScheduler (משחקים): {e}")
        send_log_message(f"❌ Scheduler: שגיאה כללית (משחקים): {e}")


def run_scheduled_competitions():
    """
    פונקציה שמריצה את כל התחרויות שצריכות להתחיל כעת
    """
    try:
        logger.info("🏆 Checking for competitions to run...")
        
        # קבל את כל התחרויות שצריכות להתחיל בזמן הזה
        competitions = db.get_current_competitions()
        
        if not competitions:
            logger.info("אין תחרויות לריצה כרגע")
            return
        
        logger.info(f"נמצאו {len(competitions)} תחרויות לריצה")
        send_log_message(f"🎯 Scheduler: נמצאו {len(competitions)} תחרויות לריצה")
        
        # ריצה של כל תחרות
        for competition in competitions:
            try:
                competition_id = competition.get('competition_id')
                competition_type_id = competition.get('competition_type_id')
                competition_type_name = competition.get('competition_type_name', 'Unknown')
                
                logger.info(f"🏃 מריץ תחרות {competition_id}: {competition_type_name} (Type ID: {competition_type_id})")
                send_log_message(f"▶️ Scheduler: מריץ תחרות {competition_id}: {competition_type_name}")
                
                # עדכן סטטוס ל-'running' (status_id = 15 or similar, check your DB)
                # Note: You may need to adjust status_id based on your DB
                # db.update_competition_status(competition_id, 15)  # Running status
                
                # הרץ את התחרות לפי סוג (competition_type_id)
                result = None
                
                # Type 1 = sprint_100m
                if competition_type_id == 1:
                    from Competitions.dash100 import Dash100
                    comp = Dash100(competition_id=competition_id)
                    result = comp.run_and_update()
                    
                # Type 2 = run_5k
                elif competition_type_id == 2:
                    from Competitions.dash5k import Run5k
                    comp = Run5k(competition_id=competition_id)
                    result = comp.run_and_update()
                    
                # Type 3 = penalty_kick (shooters)
                elif competition_type_id == 3:
                    from Competitions.penalty_shootout import PenaltyShootout
                    comp = PenaltyShootout(competition_id=competition_id)
                    result = comp.run_and_update()
                    
                # Type 4 = penalty_goalie (future implementation)
                elif competition_type_id == 4:
                    logger.warning(f"⚠️ Penalty Goalie competition not yet implemented")
                    send_log_message(f"⚠️ Scheduler: Penalty Goalie לא מומש עדיין")
                    continue
                    
                else:
                    logger.warning(f"⚠️ סוג תחרות לא מוכר: {competition_type_id}")
                    send_log_message(f"⚠️ Scheduler: סוג תחרות לא מוכר: {competition_type_id}")
                    continue
                
                # עדכן סטטוס ל-'completed' (status_id = 15 based on your screenshot)
                db.update_competition_status(competition_id, 15)
                
                logger.info(f"✅ תחרות {competition_id} הסתיימה בהצלחה")
                
                # Extract winner info
                winner_token = 'N/A'
                if result and isinstance(result, dict):
                    results_list = result.get('results', [])
                    if results_list and len(results_list) > 0:
                        winner_token = results_list[0].get('token', 'N/A')
                
                send_log_message(f"✅ Scheduler: תחרות {competition_id} הסתיימה - מנצח: {winner_token}")
                
            except Exception as e:
                logger.error(f"❌ שגיאה בתחרות {competition.get('competition_id', 'Unknown')}: {e}")
                send_log_message(f"❌ Scheduler: שגיאה בתחרות {competition.get('competition_id', 'Unknown')}: {e}")
                # Optional: Update status to error
                try:
                    # db.update_competition_status(competition.get('competition_id'), 16)  # Error status
                    pass
                except:
                    pass
                continue
    
    except Exception as e:
        logger.error(f"❌ שגיאה כללית בScheduler (תחרויות): {e}")
        send_log_message(f"❌ Scheduler: שגיאה כללית (תחרויות): {e}")


class MatchScheduler:
    """
    מנהל Scheduler להרצת משחקים ותחרויות אוטומטית
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self, check_interval_minutes=5):
        """
        התחל את הScheduler
        
        :param check_interval_minutes: כל כמה דקות לבדוק משחקים ותחרויות (ברירת מחדל: 5)
        """
        if self.is_running:
            logger.warning("Scheduler כבר רץ")
            return
        
        try:
            # הוסף job למשחקים - מריץ כל X דקות
            self.scheduler.add_job(
                run_scheduled_matches,
                CronTrigger(minute=f'*/{check_interval_minutes}'),
                id='match_scheduler',
                name='Scheduled Match Runner',
                replace_existing=True
            )
            
            # הוסף job לתחרויות - Job נפרד שרץ כל X דקות
            self.scheduler.add_job(
                run_scheduled_competitions,
                CronTrigger(minute=f'*/{check_interval_minutes}'),
                id='competition_scheduler',
                name='Scheduled Competition Runner',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info(f"✅ Scheduler התחיל - בדיקה כל {check_interval_minutes} דקות")
            send_log_message(f"✅ Scheduler התחיל:\n  🎮 משחקים: כל {check_interval_minutes} דקות\n  🏆 תחרויות: כל {check_interval_minutes} דקות")
            
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
