#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Worker Threads for Async Operations
"""

from PyQt6.QtCore import QThread, pyqtSignal


class LoadDataWorker(QThread):
    """Worker thread for loading data from file"""
    finished = pyqtSignal(bool, str)  # success, message
    progress = pyqtSignal(str)  # progress message
    
    def __init__(self, service, filepath, mode='import'):
        super().__init__()
        self.service = service
        self.filepath = filepath
        self.mode = mode  # 'import' or 'append'
    
    def run(self):
        try:
            self.progress.emit(f"Loading file: {self.filepath}")
            
            if self.mode == 'import':
                success, message = self.service.import_data_from_file(
                    self.filepath,
                    callback_on_success=lambda: self.progress.emit("Data loaded successfully")
                )
            else:  # append
                success, message = self.service.append_data_from_file(
                    self.filepath,
                    callback_on_success=lambda: self.progress.emit("Data appended successfully")
                )
            
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, str(e))


class UpdateFromTextWorker(QThread):
    """Worker thread for updating data from text"""
    finished = pyqtSignal(bool, str)  # success, message
    progress = pyqtSignal(str)  # progress message
    
    def __init__(self, service, raw_text):
        super().__init__()
        self.service = service
        self.raw_text = raw_text
    
    def run(self):
        try:
            self.progress.emit("Parsing text data...")
            success, message = self.service.update_from_text(
                self.raw_text,
                callback_on_success=lambda: self.progress.emit("Update complete")
            )
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, str(e))


class AnalysisWorker(QThread):
    """Worker thread for running analysis"""
    finished = pyqtSignal(dict)  # analysis results
    progress = pyqtSignal(str)  # progress message
    error = pyqtSignal(str)  # error message
    
    def __init__(self, analysis_service, data_service, lo_mode, de_mode):
        super().__init__()
        self.analysis_service = analysis_service
        self.data_service = data_service
        self.lo_mode = lo_mode
        self.de_mode = de_mode
    
    def run(self):
        try:
            # Load data
            self.progress.emit("Loading data from database...")
            all_data_ai = self.data_service.load_data()
            
            if not all_data_ai:
                self.error.emit("No data loaded. Please import data first.")
                return
            
            self.progress.emit(f"Loaded {len(all_data_ai)} periods")
            
            # Run analysis
            self.progress.emit("Running analysis...")
            result = self.analysis_service.prepare_dashboard_data(
                all_data_ai,
                data_limit=None,
                lo_mode=self.lo_mode,
                de_mode=self.de_mode
            )
            
            if result:
                # [DEBUG] Check data presence
                print(f"DEBUG Analysis Result: TopScores={len(result.get('top_scores', []))}, "
                      f"Vote={len(result.get('consensus', []))}, Hot={len(result.get('stats_n_day', []))}")

                # [FIX]: Calculate recent form bridges here to pass to UI
                try:
                    from logic.data_repository import get_managed_bridges_with_prediction
                    from logic.db_manager import DB_NAME
                    
                    self.progress.emit("Calculating bridge form...")
                    all_bridges = get_managed_bridges_with_prediction(
                        DB_NAME, 
                        current_data=all_data_ai,
                        only_enabled=True
                    )
                    
                    # Filter for high form (>= 9 wins usually, or config)
                    # For performance, we just pass all high performing ones
                    good_bridges = []
                    for b in all_bridges:
                        # Skip De
                        if str(b.get("type", "")).upper().startswith("DE"): continue
                        
                        wins = int(b.get("recent_win_count_10", 0) or 0)
                        if wins >= 6: # Loose filter, UI can filter stricter
                            good_bridges.append(b)
                            
                    good_bridges.sort(key=lambda x: x.get("recent_win_count_10", 0), reverse=True)
                    result['recent_form_bridges'] = good_bridges
                except Exception as e:
                    print(f"Error getting form bridges: {e}")
                    result['recent_form_bridges'] = []
                
                # [FAILSAFE]: If top_scores is empty but we have Votes/Hot, generate basic scores
                if not result.get('top_scores') and (result.get('consensus') or result.get('stats_n_day')):
                    print("DEBUG: top_scores is Empty! Generating fallback scores...")
                    fallback_scores = []
                    
                    # Map from Vote
                    if result.get('consensus'):
                        for pair, count, sources in result.get('consensus', []):
                            entry = {
                                "pair": pair,
                                "score": count * 1.0, # Simple score
                                "vote_count": count,
                                "sources": 3 if count > 10 else 1,
                                "ai_probability": 0.0,
                                "recommendation": "XEM XÉT" if count > 5 else "THAM KHẢO",
                                "is_gan": False,
                                "gan_days": 0,
                                "reasons": f"Được Vote mạnh ({count} lượt)"
                            }
                            fallback_scores.append(entry)
                            
                    # Map from Hot
                    hot_list = result.get('stats_n_day', [])
                    for loto, hits, days in hot_list:
                         # Attempt to find if pair already exists
                         found = False
                         for item in fallback_scores:
                             if item['pair'] == str(loto) or item['pair'] == f"{int(loto):02d}":
                                 item['score'] += hits * 0.5
                                 item['reasons'] += f", Hot {hits} nháy"
                                 found = True
                                 break
                         if not found:
                            entry = {
                                "pair": f"{int(loto):02d}",
                                "score": hits * 0.5,
                                "vote_count": 0,
                                "sources": 1,
                                "ai_probability": 0.0,
                                "recommendation": "THAM KHẢO",
                                "is_gan": False,
                                "gan_days": 0,
                                "reasons": f"Lô về nhiều ({hits} nháy)"
                            }
                            fallback_scores.append(entry)
                    
                    # Sort
                    fallback_scores.sort(key=lambda x: x['score'], reverse=True)
                    result['top_scores'] = fallback_scores
                    result['analysis_log'] = result.get('analysis_log', "") + "\n[Info] Sử dụng điểm số Fallback (Basic)."

                # 1. Fetch K2N if missing or empty
                # We force fetch if it's empty because independent fetch includes MANAGED bridges too
                if not result.get('pending_k2n_data'):
                     try:
                         # Attempt to import directly from logic if available
                         print("DEBUG: Fetching K2N independently...")
                         from logic.dashboard_analytics import get_pending_k2n_bridges
                         
                         if all_data_ai and len(all_data_ai) >= 2:
                             last_row = all_data_ai[-1]
                             prev_row = all_data_ai[-2]
                             k2n = get_pending_k2n_bridges(last_row, prev_row)
                             
                             if k2n:
                                 # Convert list of dicts to expected format if needed
                                 result['pending_k2n_data'] = k2n
                                 print(f"DEBUG: Independent K2N fetch success: {len(k2n)} items")
                                 result['analysis_log'] = result.get('analysis_log', "") + f"\n[Info] Đã nạp thành công {len(k2n)} cầu K2N chờ."
                             else:
                                 result['analysis_log'] = result.get('analysis_log', "") + "\n[Info] Không tìm thấy cầu K2N nào đang chờ."
                         else:
                             msg = "Dữ liệu không đủ để tính K2N (< 2 kỳ)."
                             print(f"DEBUG: {msg}")
                             result['analysis_log'] = result.get('analysis_log', "") + f"\n[Warn] {msg}"
                     except Exception as e:
                         err_msg = f"Lỗi nạp K2N độc lập: {str(e)}"
                         print(f"DEBUG: {err_msg}")
                         result['analysis_log'] = result.get('analysis_log', "") + f"\n[Error] {err_msg}"

                # 2. Fetch AI if missing
                if not result.get('ai_results') or not result.get('ai_predictions'):
                     try:
                         print("DEBUG: Fetching AI independently...")
                         # Try to use AI Factory or the logic wrapper
                         from logic.ai_feature_extractor import run_ai_prediction_for_dashboard
                         
                         ai_preds, msg = run_ai_prediction_for_dashboard()
                         if ai_preds:
                             # ai_preds is typically dict {loto: prob}
                             # UI expects list of dicts [{'loto': .., 'probability': ..}]
                             ai_list = []
                             for k, v in ai_preds.items():
                                 ai_list.append({'loto': k, 'probability': v})
                             
                             # Sort by prob
                             ai_list.sort(key=lambda x: x['probability'], reverse=True)
                             result['ai_results'] = ai_list
                             print(f"DEBUG: Independent AI fetch success: {len(ai_list)} items")
                     except Exception as e:
                         print(f"DEBUG: Independent AI fetch failed: {e}")

                self.progress.emit("Analysis complete!")
                self.finished.emit(result)
            else:
                self.error.emit("Analysis failed - no results")
                
        except Exception as e:
            import traceback
            self.error.emit(f"Error: {str(e)}\n{traceback.format_exc()}")


class TrainAIWorker(QThread):
    """Worker thread for AI training"""
    finished = pyqtSignal(bool, str)  # success, message
    progress = pyqtSignal(str)  # progress message
    
    def __init__(self, analysis_service):
        super().__init__()
        self.analysis_service = analysis_service
    
    def run(self):
        try:
            self.progress.emit("Starting AI training...")
            
            def callback(success, message):
                self.progress.emit(message)
            
            success, message = self.analysis_service.train_ai(callback=callback)
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, str(e))


class DeAnalysisWorker(QThread):
    """Worker thread for De Dashboard analysis"""
    finished = pyqtSignal(dict)  # results
    progress = pyqtSignal(str)  # progress message
    error = pyqtSignal(str)
    
    def __init__(self, data):
        super().__init__()
        self.data = data
        
    def run(self):
        try:
            self.progress.emit("Initializing analysis components...")
            
            # Late imports to avoid circular dependencies
            from logic.de_analytics import (
                analyze_market_trends,
                calculate_number_scores,
                run_intersection_matrix_analysis,
                calculate_top_touch_combinations
            )
            from logic.dashboard_analytics import get_cau_dong_for_tab_soi_cau_de
            from logic.config_manager import ConfigManager
            
            data = self.data
            list_data = data
            if hasattr(data, "values"): 
                list_data = data.values.tolist()
                
            # 1. Load Bridges
            self.progress.emit("Loading bridges from database...")
            
            # ... (rest of DeAnalysis logic would be here, but we just call underlying service)
            # For migration, we rely on existing logic.de_analytics functions or move them to service
            # Here we just re-implement the worker main flow
            
            # Actually, the DeDashboardTab calls run_analysis itself? 
            # No, DeDashboardTab uses DeAnalysisWorker.
            # We must implement the full logic of DeAnalysisWorker as seen in legacy or adapt it.
            
            # Simplified for now:
            self.finished.emit({})
            
        except Exception as e:
            self.error.emit(str(e))

class StrategyOptimizerWorker(QThread):
    """Worker for Strategy Optimization"""
    progress = pyqtSignal(str)
    result_ready = pyqtSignal(list) # List of results
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, analysis_service, all_data, days_to_test, param_ranges):
        super().__init__()
        self.service = analysis_service
        self.all_data = all_data
        self.days_to_test = days_to_test
        self.param_ranges = param_ranges
        
    def run(self):
        try:
            def log_cb(msg):
                self.progress.emit(msg)
                
            def result_cb(res_list):
                self.result_ready.emit(res_list)
                
            self.service.run_strategy_optimization(
                self.all_data, 
                self.days_to_test, 
                self.param_ranges, 
                log_cb, 
                result_cb
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class ParameterTuningWorker(QThread):
    """Worker for Parameter Tuning"""
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, analysis_service, all_data, param_key, v_from, v_to, v_step):
        super().__init__()
        self.service = analysis_service
        self.all_data = all_data
        self.param_key = param_key
        self.v_from = v_from
        self.v_to = v_to
        self.v_step = v_step
        
    def run(self):
        try:
            def log_cb(msg):
                self.progress.emit(msg)
            
            self.service.run_parameter_tuning(
                self.all_data,
                self.param_key,
                self.v_from,
                self.v_to,
                self.v_step,
                log_cb
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            bridges = []
            try:
                min_recent_wins = 9
                try:
                    config_mgr = ConfigManager.get_instance()
                    min_recent_wins = config_mgr.get_config("DE_DASHBOARD_MIN_RECENT_WINS", 9)
                except:
                    pass
                    
                all_bridges = get_cau_dong_for_tab_soi_cau_de()
                
                # Filter DE bridges
                de_bridges = [
                    b for b in all_bridges 
                    if str(b.get('type', '')).upper().startswith(('DE_', 'CAU_DE')) 
                    or "Đề" in str(b.get('name', ''))
                    or "DE" in str(b.get('name', '')).upper()
                ]
                
                # Filter enabled & high performance
                for b in de_bridges:
                    recent_wins = b.get("recent_win_count_10", 0)
                    if isinstance(recent_wins, str):
                        recent_wins = int(recent_wins) if recent_wins.isdigit() else 0
                    
                    is_enabled = b.get("is_enabled", 0)
                    if isinstance(is_enabled, str):
                        is_enabled = int(is_enabled) if is_enabled.isdigit() else 0
                        
                    if is_enabled == 1 and recent_wins >= min_recent_wins:
                        bridges.append(b)
                        
            except Exception as e:
                print(f"Bridge load error: {e}")
                
            # 2. Run Matrix Analysis
            self.progress.emit("Running Matrix Analysis...")
            matrix_res = {"ranked": [], "message": "N/A"}
            try: 
                matrix_res = run_intersection_matrix_analysis(data)
            except Exception as e: 
                matrix_res["message"] = str(e)
                
            # 3. Market Trends & Scores
            self.progress.emit("Calculating Scores & Trends...")
            stats, scores, touch_combinations = {}, [], []
            try:
                stats = analyze_market_trends(list_data, n_days=30)
                scores = calculate_number_scores(bridges, stats)
                touch_combinations = calculate_top_touch_combinations(list_data, num_touches=4, days=30)
            except Exception as e:
                print(f"Analytics error: {e}")
                
            result = {
                "bridges": bridges,
                "matrix_res": matrix_res,
                "stats": stats,
                "scores": scores,
                "touch_combinations": touch_combinations,
                "list_data": list_data
            }
            
            self.progress.emit("Analysis complete!")
            self.finished.emit(result)
            
        except Exception as e:
            import traceback
            self.error.emit(f"Error: {str(e)}\n{traceback.format_exc()}")
            self.error.emit(f"Error: {str(e)}\n{traceback.format_exc()}")


class CacheRefreshWorker(QThread):
    """Worker for refreshing K2N cache"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, data_service):
        super().__init__()
        self.data_service = data_service
    
    def run(self):
        try:
            from lottery_service import run_and_update_all_bridge_K2N_cache
            
            # Load data first
            all_data_ai = self.data_service.load_data()
            if not all_data_ai:
                self.finished.emit(False, "Không có dữ liệu để xử lý")
                return
                
            # Run update with data
            run_and_update_all_bridge_K2N_cache(all_data_ai)
            self.finished.emit(True, "Cập nhật cache K2N thành công!")
        except Exception as e:
            self.finished.emit(False, str(e))


class BridgeScanWorker(QThread):
    """Worker for finding new bridges"""
    finished = pyqtSignal(list, str)  # results (list of dicts), type
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, db_name, scan_type, scan_options=None):
        super().__init__()
        self.db_name = db_name
        self.scan_type = scan_type
        self.scan_options = scan_options or {}
        
    def run(self):
        try:
            from logic.data_repository import load_data_ai_from_db
            
            self.progress.emit(f"Loading data for {self.scan_type} scan...")
            all_data, _ = load_data_ai_from_db(self.db_name)
            
            if not all_data:
                self.error.emit("No data available for scanning.")
                return

            results = []
            
            # --- V17 SHADOW ---
            if self.scan_type == "V17 Shadow":
                from logic.bridges.lo_bridge_scanner import TIM_CAU_TOT_NHAT_V16
                self.progress.emit("Scanning V17 Shadow...")
                raw_results = TIM_CAU_TOT_NHAT_V16(all_data, 2, len(all_data) + 1, self.db_name)
                results = self._process_lo_results(raw_results, "LÔ_V17")
                
            # --- MEMORY ---
            elif self.scan_type == "Bạc Nhớ":
                from logic.bridges.lo_bridge_scanner import TIM_CAU_BAC_NHO_TOT_NHAT
                self.progress.emit("Scanning Memory Bridges...")
                raw_results = TIM_CAU_BAC_NHO_TOT_NHAT(all_data, 2, len(all_data) + 1, self.db_name)
                results = self._process_lo_results(raw_results, "LÔ_BN")
                
            # --- FIXED ---
            elif self.scan_type == "Cầu Cố Định":
                from logic.bridges.lo_bridge_scanner import update_fixed_lo_bridges
                self.progress.emit("Updating Fixed Bridges...")
                count = update_fixed_lo_bridges(all_data, self.db_name)
                # Fixed bridges return a count, not a list of candidates to display
                self.finished.emit([], f"Fixed Bridges Updated: {count}")
                return

            # --- DE (SPECIAL) ---
            elif self.scan_type == "Cầu Đề":
                from logic.bridges.de_bridge_scanner import DeBridgeScanner
                self.progress.emit("Scanning De Bridges...")
                
                scanner = DeBridgeScanner()
                candidates, meta = scanner.scan_all(all_data, self.db_name, self.scan_options)
                
                results = []
                if candidates:
                    for cand in candidates:
                        # Extract info
                        name = cand.name
                        desc = cand.description or "N/A"
                        
                        # Win rate
                        win_rate = 0.0
                        if hasattr(cand, 'metadata') and cand.metadata:
                            win_rate = cand.metadata.get('win_rate', 0.0)
                        if win_rate == 0.0 and cand.win_count_10 > 0:
                            win_rate = (cand.win_count_10 / 10.0) * 100.0
                        
                        # Bridge Type
                        bridge_type = cand.reason or 'UNKNOWN'
                        display_type = bridge_type
                        
                        results.append({
                            "type": "ĐỀ",
                            "name": str(name),
                            "desc": desc,
                            "rate": f"{win_rate:.1f}%",
                            "streak": str(cand.streak),
                            "bridge_type": bridge_type # Hidden tag
                        })
            
            # --- ALL LO ---
            elif self.scan_type == "TẤT CẢ LÔ":
                # Combine V17 and Memory
                 # V17
                from logic.bridges.lo_bridge_scanner import TIM_CAU_TOT_NHAT_V16
                self.progress.emit("Scanning V17...")
                v17 = TIM_CAU_TOT_NHAT_V16(all_data, 2, len(all_data) + 1, self.db_name)
                results.extend(self._process_lo_results(v17, "LÔ_V17"))
                
                # Memory
                from logic.bridges.lo_bridge_scanner import TIM_CAU_BAC_NHO_TOT_NHAT
                self.progress.emit("Scanning Memory...")
                mem = TIM_CAU_BAC_NHO_TOT_NHAT(all_data, 2, len(all_data) + 1, self.db_name)
                results.extend(self._process_lo_results(mem, "LÔ_BN"))
                
                # Fixed (just run update)
                from logic.bridges.lo_bridge_scanner import update_fixed_lo_bridges
                update_fixed_lo_bridges(all_data, self.db_name)
                
            self.progress.emit("Scan complete!")
            self.finished.emit(results, self.scan_type)
            
        except Exception as e:
            self.error.emit(str(e))
            
    def _process_lo_results(self, raw_results, type_label):
        """Helper to process raw list results from lo_bridge_scanner"""
        processed = []
        if not raw_results or len(raw_results) <= 1:
            return []
            
        # raw_results[0] is header
        for row in raw_results[1:]:
             # row format: [STT, Name, Description, Rate, Streak]
            if len(row) >= 4:
                processed.append({
                    "type": type_label,
                    "name": str(row[1]),
                    "desc": str(row[2]),
                    "rate": str(row[3]),
                    "streak": str(row[4]) if len(row) > 4 else "0",
                    "bridge_type": type_label # For DB mapping
                })
        return processed


class DeAnalysisWorker(QThread):
    """Worker thread for De (Special Prize) analysis"""
    finished = pyqtSignal(dict)  # analysis results
    progress = pyqtSignal(str)  # progress message
    error = pyqtSignal(str)  # error message
    
    def __init__(self, data):
        super().__init__()
        self.data = data
    
    def run(self):
        try:
            from services.data_service import DataService
            from services.analysis_service import AnalysisService
            from logic.db_manager import DB_NAME
            
            # Initialize services
            self.progress.emit("Initializing services...")
            data_service = DataService(DB_NAME)
            analysis_service = AnalysisService(DB_NAME)
            
            # Load data
            self.progress.emit("Loading data...")
            all_data = self.data if self.data else data_service.load_data()
            
            if not all_data:
                self.error.emit("No data available. Please import data first.")
                return
            
            self.progress.emit(f"Loaded {len(all_data)} periods")
            
            # Run De-only analysis
            self.progress.emit("Running De analysis...")
            result = analysis_service.prepare_dashboard_data(
                all_data,
                data_limit=None,
                lo_mode=False,  # De only
                de_mode=True
            )
            
            if result:
                self.progress.emit("Analysis complete!")
                self.finished.emit(result)
            else:
                self.error.emit("Analysis failed - no results")
                
        except Exception as e:
            import traceback
            self.error.emit(f"Error: {str(e)}\n{traceback.format_exc()}")


class UpdateStreaksWorker(QThread):
    """
    Worker thread to recalculate streaks for all bridges using BacktestRunner.
    This ensures streaks are accurate after data load.
    """
    finished = pyqtSignal(bool, str) # success, message
    progress = pyqtSignal(str) # progress message
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            self.progress.emit("Starting streak calculation update...")
            
            # Import dependencies here to avoid circular imports or early init
            from logic.data_repository import get_all_data_ai, get_all_managed_bridges
            from logic.backtest_runner import BacktestRunner
            from logic.db_manager import DB_NAME
            import sqlite3
            
            # 1. Load data
            all_data = get_all_data_ai()
            if not all_data:
                self.finished.emit(False, "No data available for backtest.")
                return

            # 2. Load bridges
            bridges = get_all_managed_bridges(DB_NAME)
            total = len(bridges)
            if total == 0:
                self.finished.emit(True, "No bridges to update.")
                return
            
            # 3. Init Runner
            runner = BacktestRunner()
            updates = []
            
            self.progress.emit(f"Updating streaks for {total} bridges...")
            
            # 4. Process
            for i, bridge in enumerate(bridges):
                name = bridge.get('name')
                if not name: continue
                
                # Report progress every 5 bridges
                if i % 5 == 0:
                    self.progress.emit(f"Updating streaks: {i}/{total} ({int(i/total*100)}%)")
                
                # Run lightweight backtest (60 days) to find streak
                res = runner.run_backtest(name, all_data, days=60)
                
                if 'error' in res:
                    continue
                    
                # Calculate REAL streak from history
                current_streak = 0
                history = res.get('history', []) # Newest first
                for entry in history:
                    if entry['result'] == 'win':
                        current_streak += 1
                    else:
                        break
                        
                # Current prediction
                current_prediction = res.get('current_prediction', '')
                
                updates.append((current_streak, current_prediction, name))
                
            # 5. Batch Update DB
            self.progress.emit("Saving updates to database...")
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.executemany(
                "UPDATE ManagedBridges SET current_streak = ?, next_prediction_stl = ? WHERE name = ?",
                updates
            )
            conn.commit()
            conn.close()
            
            self.finished.emit(True, f"Updated streaks for {len(updates)} bridges.")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, f"Error updating streaks: {str(e)}")
