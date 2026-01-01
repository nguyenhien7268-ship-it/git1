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
