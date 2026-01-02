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
