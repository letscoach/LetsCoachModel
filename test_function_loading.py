#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקה מהירה - האם הפונקציה distribute_competition_prizes נטענת נכון?
"""

import sys
sys.path.insert(0, r'C:\Users\gideo\PycharmProjects\LetsCoachModel')

print("=" * 70)
print("🔍 בדיקת טעינת הפונקציה distribute_competition_prizes")
print("=" * 70)

try:
    from Helpers import SQL_db as db
    
    # בדוק אם הפונקציה קיימת
    if hasattr(db, 'distribute_competition_prizes'):
        print("\n✅ הפונקציה distribute_competition_prizes קיימת!")
        
        # הדפס את signature של הפונקציה
        import inspect
        sig = inspect.signature(db.distribute_competition_prizes)
        print(f"   Signature: distribute_competition_prizes{sig}")
        
        # הדפס את ה-docstring
        doc = db.distribute_competition_prizes.__doc__
        if doc:
            print(f"\n📝 Documentation:")
            print(f"   {doc[:200]}...")
    else:
        print("\n❌ הפונקציה distribute_competition_prizes לא קיימת ב-SQL_db!")
        print("   רשימת הפונקציות הזמינות:")
        funcs = [name for name in dir(db) if callable(getattr(db, name)) and not name.startswith('_')]
        for func in funcs[:20]:
            print(f"   - {func}")
    
    print("\n" + "=" * 70)
    
    # בדוק גם את הקלאסים של התחרויות
    print("\n🏁 בדיקת קלאסי התחרויות:")
    
    from Competitions.dash100 import Dash100
    from Competitions.dash5k import Run5k
    from Competitions.penalty_shootout import PenaltyShootout
    
    print("✅ Dash100 נטען")
    print("✅ Run5k נטען")
    print("✅ PenaltyShootout נטען")
    
    # בדוק את ה-method run_and_update
    import inspect
    
    print("\n📋 Method run_and_update ב-Dash100:")
    source = inspect.getsource(Dash100.run_and_update)
    if 'distribute_competition_prizes' in source:
        print("   ✅ קורא ל-distribute_competition_prizes")
    else:
        print("   ❌ לא קורא ל-distribute_competition_prizes!")
    
    print("\n📋 Method run_and_update ב-Run5k:")
    source = inspect.getsource(Run5k.run_and_update)
    if 'distribute_competition_prizes' in source:
        print("   ✅ קורא ל-distribute_competition_prizes")
    else:
        print("   ❌ לא קורא ל-distribute_competition_prizes!")
    
    print("\n📋 Method run_and_update ב-PenaltyShootout:")
    source = inspect.getsource(PenaltyShootout.run_and_update)
    if 'distribute_competition_prizes' in source:
        print("   ✅ קורא ל-distribute_competition_prizes")
    else:
        print("   ❌ לא קורא ל-distribute_competition_prizes!")
    
except Exception as e:
    print(f"\n❌ שגיאה: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ בדיקה הסתיימה!")
