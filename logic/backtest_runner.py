#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtest Runner Module
Iterates through historical periods to simulate bridge performance.
"""

from logic.bridge_executor import BridgeExecutor

class BacktestRunner:
    def __init__(self):
        self.executor = BridgeExecutor()
    
    def run_backtest(self, bridge_name, all_data, days=30, progress_callback=None):
        """
        Run backtest for a bridge over last N days.
        
        Args:
            bridge_name: Name of bridge to backtest
            all_data: List of all historical data rows
            days: Number of days to backtest
            progress_callback: Optional callable(current, total)
            
        Returns:
            dict with stats and detailed history
        """
        if not all_data or len(all_data) < days + 1:
            return {
                'error': f'Not enough data. Need at least {days+1} days.'
            }
            
        # We need data BEFORE the test period to calculate prediction
        # Test period starts at: len - days
        start_idx = len(all_data) - days
        if start_idx < 1: start_idx = 1 # Need at least 1 day prior
        
        history = []
        wins = 0
        streaks = []
        current_streak = 0
        
        total_steps = days
        
        for i in range(days):
            # Index of the day we are testing (the day result happened)
            test_idx = start_idx + i
            if test_idx >= len(all_data): break
            
            # Update progress
            if progress_callback:
                progress_callback(i + 1, total_steps)
                
            # Data used for prediction: All data UP TO test_idx (exclusive)
            # simulation: We stand at (test_idx - 1) and predict (test_idx)
            historical_data = all_data[:test_idx]
            
            # Execute bridge to get prediction for test_idx
            prediction = self.executor.execute(bridge_name, historical_data)
            
            # Get actual result of test_idx
            # row format: [Masoky, Date, GDB, G1...]
            # GDB is usually index 2. De is last 2 digits of GDB.
            actual_row = all_data[test_idx]
            date = actual_row[1]
            gdb = str(actual_row[2])
            
            actual_de = gdb[-2:] if len(gdb) >= 2 else "??"
            
            # Parse prediction
            predicted_numbers = []
            if prediction:
                predicted_numbers = [p.strip() for p in prediction.split(',')]
            
            # Check win (Any digit match logic)
            is_win = False
            if predicted_numbers and actual_de != "??":
                for digit in actual_de:
                    if digit in predicted_numbers:
                        is_win = True
                        break
            
            # Update stats
            if is_win:
                wins += 1
                current_streak += 1
            else:
                if current_streak > 0:
                    streaks.append(current_streak)
                current_streak = 0
            
            # Record history
            history.append({
                'date': str(date),
                'predicted': prediction if prediction else '--',
                'actual': actual_de,
                'result': 'win' if is_win else 'loss'
            })
            
        # Final streak check
        if current_streak > 0:
            streaks.append(current_streak)
            
        # Calculate real current streak from history (newest first)
        real_current_streak = 0
        reversed_history = list(reversed(history)) # Newest first
        if reversed_history:
            for entry in reversed_history:
                if entry['result'] == 'win':
                    real_current_streak += 1
                else:
                    break
            
        total_tests = len(history)
        win_rate = (wins / total_tests * 100) if total_tests > 0 else 0
        avg_streak = (sum(streaks) / len(streaks)) if streaks else 0
        
        return {
            'history': reversed_history, # Return newest first
            'win_rate': round(win_rate, 1),
            'total_wins': wins,
            'total_tests': total_tests,
            'avg_streak': round(avg_streak, 1),
            'real_current_streak': real_current_streak, # Expose correct streak
            'bridge_name': bridge_name,
            # Current prediction (for next unknown period)
            'current_prediction': self.executor.execute(bridge_name, all_data)
        }
