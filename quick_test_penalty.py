#!/usr/bin/env python3
"""Quick test for PenaltyShootout score format"""

from Competitions.penalty_shootout import PenaltyShootout

# Test competition 1667
comp = PenaltyShootout(1667)
results = comp.run_competition()

print("\n=== PENALTY SHOOTOUT RESULTS ===")
for r in results:
    token_short = r['token'][-6:]
    score = r.get('score', 'N/A')
    rank = r.get('rank_position', '?')
    print(f"Rank {rank}: {token_short} -> Score: {score}")

print("\n=== Expected format: X/Y (e.g., 12/15) ===")
