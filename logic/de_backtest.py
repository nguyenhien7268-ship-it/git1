#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
De Bridge Backtest Module
Provides backtest functionality for De (Special Prize) bridges
"""

def get_bridge_backtest(bridge_name, all_data, days=30):
    """
    Get backtest results for a De bridge
    
    Args:
        bridge_name: Name of the bridge (e.g., "DE_DYN_G1.0_G3.6.2_K1")
        all_data: Historical data (list of rows)
        days: Number of days to backtest (default 30)
    
    Returns:
        dict: {
            'history': List of {date, predicted, actual, result (win/loss)},
            'win_rate': Percentage of wins,
            'total_wins': Number of wins,
            'total_tests': Total tests,
            'avg_streak': Average streak length
        }
    """
    try:
        from logic.data_repository import get_managed_bridges_with_prediction
        from logic.db_manager import DB_NAME
        
        # Get all bridges to find the specific one
        all_bridges = get_managed_bridges_with_prediction(DB_NAME, current_data=all_data, only_enabled=False)
        
        # Find the bridge
        target_bridge = None
        for b in all_bridges:
            if b.get('name') == bridge_name:
                target_bridge = b
                break
        
        if not target_bridge:
            return {
                'history': [],
                'win_rate': 0,
                'total_wins': 0,
                'total_tests': 0,
                'avg_streak': 0,
                'error': f'Bridge "{bridge_name}" not found'
            }
        
        # Get last N days of data
        if len(all_data) < days:
            days = len(all_data)
        
        recent_data = all_data[-days:]
        
        # Backtest logic
        history = []
        wins = 0
        current_streak = 0
        streaks = []
        
        for i, row in enumerate(recent_data):
            try:
                # Extract date and actual De result
                date_str = str(row[1]) if len(row) > 1 else "N/A"
                actual_de = str(row[2]) if len(row) > 2 else ""
                
                # Get last 2 digits of De
                if actual_de and len(actual_de) >= 2:
                    actual_de = actual_de[-2:]
                else:
                    actual_de = "??"
                
                # Get prediction from bridge
                # Use 'next_prediction_stl' field which contains the prediction
                predicted = target_bridge.get('next_prediction_stl', '--')
                
                # Parse prediction - can be single number or comma-separated list
                predicted_numbers = []
                if predicted and predicted != '--':
                    if isinstance(predicted, str):
                        # Split by comma and clean
                        predicted_numbers = [p.strip() for p in predicted.split(',')]
                    else:
                        predicted_numbers = [str(predicted)]
                
                # Check if win - ANY digit in actual De should match ANY predicted number
                is_win = False
                if predicted_numbers and actual_de != "??":
                    # Check if any digit in actual_de matches any predicted number
                    for digit in actual_de:
                        if digit in predicted_numbers:
                            is_win = True
                            break
                
                # For display, show all predictions
                pred_display = ','.join(predicted_numbers) if predicted_numbers else '--'

                
                if is_win:
                    wins += 1
                    current_streak += 1
                else:
                    if current_streak > 0:
                        streaks.append(current_streak)
                    current_streak = 0
                
                history.append({
                    'date': date_str,
                    'predicted': pred_display,
                    'actual': actual_de,
                    'result': 'win' if is_win else 'loss'
                })

                
            except Exception as e:
                print(f"Error processing row {i}: {e}")
                continue
        
        # Final streak
        if current_streak > 0:
            streaks.append(current_streak)
        
        # Calculate stats
        total_tests = len(history)
        win_rate = (wins / total_tests * 100) if total_tests > 0 else 0
        avg_streak = (sum(streaks) / len(streaks)) if streaks else 0
        
        return {
            'history': history,
            'win_rate': win_rate,
            'total_wins': wins,
            'total_tests': total_tests,
            'avg_streak': avg_streak
        }
        
    except Exception as e:
        return {
            'history': [],
            'win_rate': 0,
            'total_wins': 0,
            'total_tests': 0,
            'avg_streak': 0,
            'error': str(e)
        }
