import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import poisson
import random


def normalize_rank(rank, exponent=1.5):
    # Normalize the 1-100 rank to a 0.5-1.5 scale, with an exponential transformation
    normalized = 0.5 + (rank - 1) * (1 / 99)
    # Apply a power transformation to amplify differences
    return normalized ** exponent

def predict_match_outcome(offense_team1, defense_team1, midfield_team1, offense_team2, defense_team2, midfield_team2):
    # Normalize the rankings
    offense_team1 = normalize_rank(offense_team1) * normalize_rank(midfield_team1)
    defense_team1 = (2 - normalize_rank(defense_team1)) * normalize_rank(midfield_team1)
    offense_team2 = normalize_rank(offense_team2) * normalize_rank(midfield_team2)
    defense_team2 = (2 - normalize_rank(defense_team2)) * normalize_rank(midfield_team2)

    # Define average goals in the league for normalization
    avg_goals = 1.4

    # Calculate expected goals for each team
    expected_goals_team1 = offense_team1 * defense_team2 * avg_goals
    expected_goals_team2 = offense_team2 * defense_team1 * avg_goals

    # Initialize a dictionary to store the probabilities of different match outcomes
    outcome_probabilities = {}

    # Calculate probabilities for each possible outcome up to 7 total goals
    for goals_team1 in range(8):
        for goals_team2 in range(8 - goals_team1):
            prob = (poisson.pmf(goals_team1, expected_goals_team1) *
                    poisson.pmf(goals_team2, expected_goals_team2))
            outcome_probabilities[f'{goals_team1}-{goals_team2}'] = prob

    return outcome_probabilities


def visualize_outcomes(outcomes):
    # Separate wins, losses, and draws
    wins = [(k, v) for k, v in outcomes.items() if k.split('-')[0] > k.split('-')[1]]
    losses = [(k, v) for k, v in outcomes.items() if k.split('-')[0] < k.split('-')[1]]
    draws = [(k, v) for k, v in outcomes.items() if k.split('-')[0] == k.split('-')[1]]

    # Sort wins by goal difference and then goals scored
    wins.sort(key=lambda x: (int(x[0].split('-')[0]) - int(x[0].split('-')[1]), int(x[0].split('-')[0])), reverse=True)

    # Sort losses by goal difference and then goals conceded
    losses.sort(key=lambda x: (int(x[0].split('-')[1]) - int(x[0].split('-')[0]), int(x[0].split('-')[1])))

    # Sort draws by the number of goals
    draws.sort(key=lambda x: int(x[0].split('-')[0]), reverse=True)

    # Combine the sorted outcomes
    ordered_outcomes = wins + draws + losses

    # Extract labels and probabilities
    labels = [outcome[0] for outcome in ordered_outcomes]
    probabilities = [outcome[1] for outcome in ordered_outcomes]

    # Plot
    plt.figure(figsize=(12, 6))
    plt.bar(labels, probabilities, color='skyblue')
    plt.xlabel('Match Outcome')
    plt.ylabel('Probability')
    plt.title('Probability Distribution of Match Outcomes (Ordered)')
    plt.xticks(rotation=90)
    plt.show()

def choose_outcome(probabilities):
    outcomes = list(probabilities.keys())
    probs = list(probabilities.values())

    # Normalize probabilities to ensure they sum to 1
    total_prob = sum(probs)
    normalized_probs = [prob / total_prob for prob in probs]

    # Randomly choose an outcome based on the probabilities
    chosen_outcome = random.choices(outcomes, weights=normalized_probs, k=1)[0]

    return chosen_outcome

def assign_goal_minutes(chosen_outcome):
    # Split the chosen outcome to get goals for each team
    goals_team1, goals_team2 = map(int, chosen_outcome.split('-'))

    # Function to assign minutes for each goal for a team
    def assign_minutes_for_team_goals(num_goals):
        goal_minutes = []
        if num_goals > 0:
            interval = 90 / num_goals
            for goal in range(num_goals):
                # Ensure each goal is assigned within its interval, avoiding start minute overlap
                start_minute = goal * interval
                minute = np.random.uniform(start_minute + 1, min(start_minute + interval, 90))
                goal_minutes.append(round(minute))
        return goal_minutes

    # Assign minutes to goals for each team
    minutes_team1 = assign_minutes_for_team_goals(goals_team1)
    minutes_team2 = assign_minutes_for_team_goals(goals_team2)

    # Merge and sort the minutes, tagging them with the respective team
    goal_events = [('Team 1', minute) for minute in minutes_team1] + [('Team 2', minute) for minute in minutes_team2]
    goal_events.sort(key=lambda x: x[1])  # Sort by minute

    return goal_events

def represent_goal_events(goal_events):
    if not goal_events:
        return "No goals scored in the match."

    representation = "Goals scored:\n"
    for team, minute in goal_events:
        representation += f"Minute {minute}: {team} scored a goal.\n"

    return representation


# Example usage with the addition of midfield strength
offense_team1, defense_team1, midfield_team1 = 60, 60, 60
offense_team2, defense_team2, midfield_team2 = 58, 60, 58

# Predict match outcomes
outcome_probabilities = predict_match_outcome(offense_team1, defense_team1, midfield_team1, offense_team2,
                                              defense_team2, midfield_team2)

# Visualize the outcomes
visualize_outcomes(outcome_probabilities)


def game (team1, team2, match_id):
    pass
# Example usage: choose a match outcome based on the calculated probabilities

chosen_outcome = choose_outcome(outcome_probabilities)
print(f'Chosen Outcome: {chosen_outcome}')
goal_events = assign_goal_minutes(chosen_outcome)
representation = represent_goal_events(goal_events)
print(representation)
