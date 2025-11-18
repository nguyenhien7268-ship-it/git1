"""
Feature Service - Week 3 Architecture Refactoring
Decouples feature extraction logic from ml_model.py

This service provides a clean interface for extracting features
without direct dependencies on bridges and dashboard modules.
"""

from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict


class FeatureService:
    """
    Service layer for feature extraction and processing.
    
    Implements dependency injection pattern to decouple ml_model
    from direct bridge and dashboard dependencies.
    """
    
    def __init__(self, 
                 loto_extractor=None,
                 stats_calculator=None,
                 gan_calculator=None):
        """
        Initialize FeatureService with injectable dependencies.
        
        Args:
            loto_extractor: Function to extract loto numbers from data
            stats_calculator: Function to calculate loto statistics
            gan_calculator: Function to calculate gan statistics
        """
        self.loto_extractor = loto_extractor
        self.stats_calculator = stats_calculator
        self.gan_calculator = gan_calculator
    
    def extract_loto_results(self, data: Any) -> set:
        """
        Extract loto results from data using injected extractor.
        
        Args:
            data: Raw lottery data
            
        Returns:
            Set of loto numbers
        """
        if self.loto_extractor is None:
            return set()
        
        try:
            return set(self.loto_extractor(data))
        except Exception as e:
            print(f"Error extracting loto: {e}")
            return set()
    
    def calculate_loto_stats(self, 
                            all_data: List[Any], 
                            days: int) -> Dict[str, float]:
        """
        Calculate loto statistics for given days.
        
        Args:
            all_data: Historical lottery data
            days: Number of days to analyze
            
        Returns:
            Dictionary mapping loto -> hit frequency
        """
        if self.stats_calculator is None:
            return {}
        
        try:
            stats_list = self.stats_calculator(all_data, days)
            # Convert list of tuples to map
            # Format: [(loto, hit_count, day_count), ...]
            return {loto: hit_count for loto, hit_count, day_count in stats_list}
        except Exception as e:
            print(f"Error calculating loto stats: {e}")
            return {}
    
    def calculate_gan_stats(self, 
                           all_data: List[Any], 
                           max_days: int) -> Dict[str, int]:
        """
        Calculate gan (streak) statistics.
        
        Args:
            all_data: Historical lottery data
            max_days: Maximum days for gan calculation
            
        Returns:
            Dictionary mapping loto -> gan days
        """
        if self.gan_calculator is None:
            return {}
        
        try:
            gan_list = self.gan_calculator(all_data, max_days)
            # Convert list of tuples to map
            # Format: [(loto, days), ...]
            return {loto: days for loto, days in gan_list}
        except Exception as e:
            print(f"Error calculating gan stats: {e}")
            return {}
    
    def extract_features_for_loto(self,
                                  loto: str,
                                  previous_data: Any,
                                  bridge_features: Dict[str, Any],
                                  loto_stats: Dict[str, float],
                                  gan_stats: Dict[str, int],
                                  stats_days: int = 7,
                                  gan_max_days: int = 8) -> List[float]:
        """
        Extract all features for a single loto number.
        
        This is the core feature extraction method that combines
        all feature sources into a single feature vector.
        
        Args:
            loto: Loto number to extract features for
            previous_data: Data from previous period
            bridge_features: Features from bridge predictions
            loto_stats: Loto hot statistics
            gan_stats: Gan statistics
            stats_days: Number of days for stats calculation
            gan_max_days: Maximum days for gan calculation
            
        Returns:
            List of feature values
        """
        features = []
        
        # F1: Tần suất Lô tô Hot (Hit frequency in last N days)
        hot_freq = loto_stats.get(loto, 0) / stats_days if stats_days > 0 else 0
        features.append(hot_freq)
        
        # F2: Tần suất Lô tô Gan (Gan days)
        gan_freq = gan_stats.get(loto, 0) / gan_max_days if gan_max_days > 0 else 0
        features.append(gan_freq)
        
        # F3: Số vote Cầu Cổ Điển (Bridges V5)
        features.append(bridge_features.get('v5_count', 0))
        
        # F4: Số vote Cầu V17/Shadow
        features.append(bridge_features.get('v17_count', 0))
        
        # F5: Số vote Cầu Bạc Nhớ (Memory)
        features.append(bridge_features.get('memory_count', 0))
        
        # F6: Về ngày hôm trước (Came yesterday)
        previous_loto_set = self.extract_loto_results(previous_data)
        loto_came_yesterday = 1 if loto in previous_loto_set else 0
        features.append(loto_came_yesterday)
        
        # F7: Q-Feature - Tỷ lệ thắng trung bình (Average win rate)
        avg_win_rate = bridge_features.get('q_avg_win_rate', 0.0) / 100.0
        features.append(avg_win_rate)
        
        # F8: Q-Feature - Rủi ro K2N tối thiểu (Minimum K2N risk)
        min_k2n_risk = bridge_features.get('q_min_k2n_risk', 999.0)
        risk_feature = 1.0 / (min_k2n_risk + 1.0)
        features.append(risk_feature)
        
        # F9: Q-Feature - Chuỗi Thắng/Thua hiện tại (Current streak)
        max_curr_streak = bridge_features.get('q_max_curr_streak', -999.0)
        streak_feature = max_curr_streak / 100.0
        features.append(streak_feature)
        
        return features
    
    def prepare_features_for_period(self,
                                    all_data: List[Any],
                                    period_index: int,
                                    bridge_predictions: Dict[str, Dict[str, Any]],
                                    all_lotos: List[str],
                                    stats_days: int = 7,
                                    gan_max_days: int = 8) -> Tuple[List[List[float]], List[int]]:
        """
        Prepare features for a specific time period.
        
        This method extracts features for all lotos in a given period
        and returns both features (X) and labels (y).
        
        Args:
            all_data: Complete historical data
            period_index: Index of the period to extract features for
            bridge_predictions: Bridge predictions for the period
            all_lotos: List of all possible loto numbers
            stats_days: Number of days for statistics
            gan_max_days: Maximum days for gan calculation
            
        Returns:
            Tuple of (features_list, labels_list)
        """
        if period_index < 1 or period_index >= len(all_data):
            return [], []
        
        current_data = all_data[period_index]
        previous_data = all_data[period_index - 1]
        current_ky = str(current_data[0])
        
        # Calculate current period loto results (labels)
        current_loto_results = self.extract_loto_results(current_data)
        
        # Calculate statistics from historical data (up to period_index - 1)
        historical_data = all_data[:period_index]
        loto_stats = self.calculate_loto_stats(historical_data, stats_days)
        gan_stats = self.calculate_gan_stats(historical_data, gan_max_days)
        
        # Get bridge predictions for this period
        period_bridge_predictions = bridge_predictions.get(current_ky, {})
        
        # Extract features for each loto
        features_list = []
        labels_list = []
        
        for loto in all_lotos:
            loto_bridge_features = period_bridge_predictions.get(loto, {})
            
            features = self.extract_features_for_loto(
                loto=loto,
                previous_data=previous_data,
                bridge_features=loto_bridge_features,
                loto_stats=loto_stats,
                gan_stats=gan_stats,
                stats_days=stats_days,
                gan_max_days=gan_max_days
            )
            
            label = 1 if loto in current_loto_results else 0
            
            features_list.append(features)
            labels_list.append(label)
        
        return features_list, labels_list
    
    @staticmethod
    def create_default_service():
        """
        Factory method to create FeatureService with default dependencies.
        
        This method attempts to import and inject default implementations.
        Falls back to None if imports fail.
        
        Returns:
            FeatureService instance with default dependencies
        """
        loto_extractor = None
        stats_calculator = None
        gan_calculator = None
        
        try:
            # Try relative imports first
            from .bridges.bridges_classic import getAllLoto_V30
            from .dashboard_analytics import get_loto_stats_last_n_days, get_loto_gan_stats
            
            loto_extractor = getAllLoto_V30
            stats_calculator = get_loto_stats_last_n_days
            gan_calculator = get_loto_gan_stats
        except ImportError:
            try:
                # Try absolute imports as fallback
                from logic.bridges.bridges_classic import getAllLoto_V30
                from logic.dashboard_analytics import get_loto_stats_last_n_days, get_loto_gan_stats
                
                loto_extractor = getAllLoto_V30
                stats_calculator = get_loto_stats_last_n_days
                gan_calculator = get_loto_gan_stats
            except ImportError:
                print("Warning: Could not import default dependencies for FeatureService")
        
        return FeatureService(
            loto_extractor=loto_extractor,
            stats_calculator=stats_calculator,
            gan_calculator=gan_calculator
        )
