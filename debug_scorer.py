
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from logic.analytics.dashboard_scorer import get_top_scored_pairs, LoScorer
from logic.db_manager import DB_NAME

print("--- Testing LoScorer Import ---")
try:
    if LoScorer:
        print(f"LoScorer class: {LoScorer}")
    else:
        print("LoScorer is None/False")
except NameError:
    print("LoScorer NameError")

print("\n--- Testing get_top_scored_pairs ---")
try:
    # Need dummy data
    stats = [('00', 10, 5), ('11', 8, 4)]
    consensus = [('22-33', 5, 'C1, C2')]
    high_win = []
    pending_k2n = []
    gan_stats = []
    top_memory_bridges = []
    
    scores = get_top_scored_pairs(stats, consensus, high_win, pending_k2n, gan_stats, top_memory_bridges)
    print(f"Scores Type: {type(scores)}")
    print(f"Scores Length: {len(scores) if scores else 'None'}")
    if scores:
        print(f"First Score: {scores[0]}")
except Exception as e:
    print(f"Error calling get_top_scored_pairs: {e}")
    import traceback
    traceback.print_exc()
