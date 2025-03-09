import random


def simulate_football_match(team1, team2):
    # מספר ההתקפות הכולל במשחק
    total_attacks = 200

    # פונקציה לחישוב הסתברות להתקפה על בסיס ציון הקישור
    def calc_attack_probability(team1_midfield, team2_midfield):
        total = team1_midfield + team2_midfield
        return team1_midfield / total if total > 0 else 0.5

    # פונקציה לבחירת רמת הסיכון של ההתקפה
    def choose_risk_level():
        rand = random.random()
        if rand < 0.55:
            return 1
        elif rand < 0.75:
            return 2
        elif rand < 0.90:
            return 3
        elif rand < 0.97:
            return 4
        else:
            return 5

    # פונקציה לחישוב אם נכבש שער
    def calculate_goal(risk_level, attack, defense):
        if risk_level == 4:
            goal_chance = 0.10 + (attack - defense) * 0.01
            return random.random() < min(max(goal_chance, 0.10), 0.15)
        elif risk_level == 5:
            goal_chance = 0.30 + (attack - defense) * 0.02
            return random.random() < min(max(goal_chance, 0.30), 0.40)
        return False

    # אתחול תוצאות
    team1_score = 0
    team2_score = 0

    # חישוב הסתברות להתקפה עבור כל קבוצה
    team1_attack_prob = calc_attack_probability(team1['midfield'], team2['midfield'])

    # סימולציית המשחק
    for _ in range(total_attacks):
        # בחירת הקבוצה התוקפת
        attacking_team = team1 if random.random() < team1_attack_prob else team2
        defending_team = team2 if attacking_team == team1 else team1

        # בחירת רמת הסיכון
        risk_level = choose_risk_level()

        # חישוב אם נכבש שער (רק עבור רמות סיכון 4 ו-5)
        if risk_level >= 4:
            if calculate_goal(risk_level, attacking_team['attack'], defending_team['defense']):
                if attacking_team == team1:
                    team1_score += 1
                else:
                    team2_score += 1

    return team1_score, team2_score

