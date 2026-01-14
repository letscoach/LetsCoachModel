# 🔍 DEBUG LOGGING - מערכת עקיבה אחרי FRESHNESS

## Logs Added (3 Strategic Points)

### 1️⃣ CALCULATION LOGS (post_game.py, line 525-530)

Shows the freshness_delta being calculated PER PLAYER with all components:

```
🎮 Processing League match with factors: attribute=1.0, freshness=1.0, satisfaction=1.0
  📊 Player player_id_1 (Player Name):
     - Endurance: 50
     - Base Delta (raw): -22.5
     - Factor: 1.0
     - Final Delta: -22.5

  📊 Player player_id_2 (Another Player):
     - Endurance: 50
     - Base Delta (raw): -22.5
     - Factor: 1.0
     - Final Delta: -22.5
```

**What to look for**:

- Is the Factor showing 1.0 or 0.5?
- Is Final Delta different for KIND 1 vs KIND 2?

---

### 2️⃣ BEFORE DB INSERT LOGS (SQL_db.py, line 245-246)

Shows what freshness_delta is about to be sent to database:

```
📌 BEFORE DB INSERT - Player player_id_1:
   - freshness_delta value: -22.5

📌 BEFORE DB INSERT - Player player_id_2:
   - freshness_delta value: -11.25
```

**What to look for**:

- Is the value here DIFFERENT for KIND 1 vs KIND 2?
- If same value → bug is in calculation (step 1)
- If different value → bug is in database query

---

### 3️⃣ DATABASE UPDATE LOGS (SQL_db.py, line 165-169)

Shows exact SQL being executed:

```
🔄 DB UPDATE - Player player_id_1: freshness_delta=-22.5, operator=+
   Query: UPDATE player_dynamic_attributes SET attribute_value = CASE...
✅ Freshness updated for player_id_1

🔄 DB UPDATE - Player player_id_2: freshness_delta=-11.25, operator=+
   Query: UPDATE player_dynamic_attributes SET attribute_value = CASE...
✅ Freshness updated for player_id_2
```

**What to look for**:

- Does the freshness_delta value in log match BEFORE DB INSERT?
- If different → something's modifying the value before DB insert
- If same → query might be wrong

---

## איך להשתמש בלוגים

כאשר אתה מריץ שתי משחיקים (KIND 1 ו-KIND 2), יופיע בפלט:

```
1. אם הלוגים בשלב 1 שונים:
   ✅ הכפל הפקטור עובד - בדוק שלבים 2 ו-3

2. אם הלוגים בשלב 1 זהים אבל הם שונים בשלב 2:
   ❌ יש ערך שונה המתווסף איפשהו - חפש בקוד

3. אם הלוגים בשלב 2 זהים לשלב 1:
   🔍 בדוק את ה-SQL query בשלב 3
   - אולי יש בעיה בפורמט הquery
   - אולי יש בעיה בתוך את calculate_freshness_drop

---

## תוצאות צפויות

### Kind 1 (League) - Factor 1.0
```

📊 Player XXX:

- Base Delta: -22.5
- Factor: 1.0
- Final Delta: -22.5

📌 BEFORE DB INSERT: -22.5
🔄 DB UPDATE: -22.5

```

### Kind 2 (Friendly) - Factor 0.5
```

📊 Player XXX:

- Base Delta: -22.5
- Factor: 0.5
- Final Delta: -11.25

📌 BEFORE DB INSERT: -11.25
🔄 DB UPDATE: -11.25

````

---

## קובץ Log
כל הלוגים יופיעו בקונסול כאשר משחק מסתיים.
אם קשה לעקוב, אפשר להפנות לקובץ:

```bash
python run_match_manual.py > match_debug.log 2>&1
````

ואז לחפש:

- `📊` - חישובים
- `📌` - לפני DB
- `🔄` - SQL UPDATE
