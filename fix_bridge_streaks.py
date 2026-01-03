import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from logic.backtest_runner import BacktestRunner
from logic.data_repository import get_all_managed_bridges, get_all_data_ai
from logic.db_manager import DB_NAME

def fix_all_streaks():
    print(">>> Starting Streak Fix for ALL Bridges...")
    
    # 1. Load data
    all_data = get_all_data_ai()
    if not all_data:
        print("Error: No data found.")
        return

    # 2. Load bridges
    bridges = get_all_managed_bridges(DB_NAME)
    print(f"Loaded {len(bridges)} bridges.")
    
    # 3. Initialize Runner
    runner = BacktestRunner()
    
    updates = []
    
    # 4. Iterate and calculate
    print("Calculating streaks...")
    for i, bridge in enumerate(bridges):
        name = bridge.get('name')
        if not name: continue
        
        # Run backtest for last 30 days (enough to find streak)
        # We only need the current streak from the runner logic
        # But wait, BacktestRunner returns 'avg_streak', but we want CURRENT streak.
        # BacktestRunner currently calculates current streak implicitly but doesn't expose it directly in return dict
        # EXCEPT it does calculate it internally.
        
        # Let's inspect runner return...
        # It returns stats. But we know the logic:
        # Check history used in popup. The popup history has 'result': 'win'/'loss'.
        # We can calculate streak from that history easily.
        
        # Run sync backtest
        res = runner.run_backtest(name, all_data, days=60)
        
        if 'error' in res:
            print(f"Skipping {name}: {res['error']}")
            continue
            
        history = res.get('history', []) # Newest first (reversed in run_backtest return)
        
        # Calculate current streak from history
        current_streak = 0
        if history:
            # History is newest first
            # Check if newest is win
            for entry in history:
                if entry['result'] == 'win':
                    current_streak += 1
                else:
                    break # Stop at first loss
            
            # If the first entry is loss, streak should be 0 (or negative if we tracked lose streak, but let's stick to win streak)
            # Standard logic: if last result was loss, streak = 0.
        
        # Get prediction
        current_prediction = res.get('current_prediction', '')
        
        updates.append((current_streak, current_prediction, name))
        
        if i % 10 == 0:
            print(f"Processed {i+1}/{len(bridges)}...", end='\r')
            
    print(f"\nExample update: {updates[0] if updates else 'None'}")
    
    # 5. Batch Update DB
    print("Updating Database...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.executemany(
            "UPDATE ManagedBridges SET current_streak = ?, next_prediction_stl = ? WHERE name = ?",
            updates
        )
        conn.commit()
        print(f"Updated {cursor.rowcount} bridges.")
    except Exception as e:
        print(f"Error updating DB: {e}")
    finally:
        conn.close()
        
    print(">>> Fix Complete. Please restart Application.")

if __name__ == "__main__":
    fix_all_streaks()
