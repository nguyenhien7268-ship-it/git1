
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())


from services.data_service import DataService
from services.analysis_service import AnalysisService
# get_pending_k2n_bridges IS available in logic.dashboard_analytics
from logic.dashboard_analytics import get_pending_k2n_bridges 
from logic.db_manager import DB_NAME

class SimpleLogger:
    def log(self, msg):
        try:
            print(f"[SVC LOG] {msg}")
        except UnicodeEncodeError:
            # Fallback for systems with poor unicode support
            # Encode to ASCII, replacing errors with backslash escape sequence strings
            encoded_msg = msg.encode('ascii', errors='backslashreplace').decode('ascii')
            print(f"[SVC LOG] {encoded_msg}")
        except:
             print("[SVC LOG] (Failed to print message)")

def debug_data():
    ds = DataService(DB_NAME)
    data = ds.load_data()
    print(f"Loaded {len(data)} records")
    
    # ... bridge fetch ...
    
    print("\n--- Testing Direct dashboard_scorer Call ---")
    try:
        from logic.analytics import dashboard_scorer
        stats = dashboard_scorer.get_loto_stats_last_n_days(data, n=7)
        print(f"Direct Stats Result Type: {type(stats)}")
        print(f"Direct Stats Count: {len(stats) if stats else 0}")
        if stats:
            print(f"First Stat: {stats[0]}")
    except Exception as e:
        print(f"Error calling dashboard_scorer direct: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Testing AnalysisService.prepare_dashboard_data (pending_k2n_data) ---")
    try:
        # Instantiate service with Logger
        service = AnalysisService(DB_NAME, logger=SimpleLogger())
        # Minimal run
        res = service.prepare_dashboard_data(data, data_limit=50)
        
        # Check Pending K2N
        pending = res.get('pending_k2n_data')
        print(f"Pending K2N Type: {type(pending)}")
        if isinstance(pending, list):
             print(f"Pending K2N Count: {len(pending)}")
             
        # Check Top Scores
        scores = res.get('top_scores')
        print(f"Top Scores Type: {type(scores)}")
        if scores:
            print(f"Top Scores Count: {len(scores)}")
            if len(scores) > 0:
                print(f"First Score Item: {scores[0]}")
        else:
            print("Top Scores is EMPTY or None")
            
        # Check other components to isolate failure
        print(f"Vote Keys: {len(res.get('consensus', []))}")
        print(f"Hot Keys: {len(res.get('stats_n_day', []))}")
        print(f"High Win: {len(res.get('high_win', []))}")
            
    except Exception as e:
        print(f"Error executing prepare_dashboard_data: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Error executing prepare_dashboard_data: {e}")


if __name__ == "__main__":
    debug_data()
