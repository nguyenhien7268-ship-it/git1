"""
Tests for FeatureService - Week 3 Architecture Refactoring
"""

import pytest
from logic.feature_service import FeatureService


class TestFeatureServiceInit:
    """Tests for FeatureService initialization"""
    
    def test_init_with_no_dependencies(self):
        """Should create service with None dependencies"""
        service = FeatureService()
        
        assert service.loto_extractor is None
        assert service.stats_calculator is None
        assert service.gan_calculator is None
    
    def test_init_with_custom_dependencies(self):
        """Should create service with custom dependencies"""
        def mock_extractor(data):
            return ['01', '02']
        
        def mock_stats(data, days):
            return [('01', 5, 7)]
        
        def mock_gan(data, days):
            return [('01', 3)]
        
        service = FeatureService(
            loto_extractor=mock_extractor,
            stats_calculator=mock_stats,
            gan_calculator=mock_gan
        )
        
        assert service.loto_extractor == mock_extractor
        assert service.stats_calculator == mock_stats
        assert service.gan_calculator == mock_gan


class TestExtractLotoResults:
    """Tests for extract_loto_results method"""
    
    def test_extract_with_no_extractor(self):
        """Should return empty set when no extractor provided"""
        service = FeatureService()
        result = service.extract_loto_results([1, 2, 3])
        
        assert result == set()
    
    def test_extract_with_valid_extractor(self):
        """Should extract loto results using provided extractor"""
        def mock_extractor(data):
            return ['01', '02', '03']
        
        service = FeatureService(loto_extractor=mock_extractor)
        result = service.extract_loto_results('dummy_data')
        
        assert result == {'01', '02', '03'}
    
    def test_extract_handles_exceptions(self):
        """Should handle exceptions gracefully"""
        def faulty_extractor(data):
            raise ValueError("Test error")
        
        service = FeatureService(loto_extractor=faulty_extractor)
        result = service.extract_loto_results('data')
        
        assert result == set()


class TestCalculateLotoStats:
    """Tests for calculate_loto_stats method"""
    
    def test_calculate_with_no_calculator(self):
        """Should return empty dict when no calculator provided"""
        service = FeatureService()
        result = service.calculate_loto_stats([], 7)
        
        assert result == {}
    
    def test_calculate_with_valid_calculator(self):
        """Should calculate stats using provided calculator"""
        def mock_calculator(data, days):
            return [
                ('01', 5, 7),
                ('02', 3, 7),
                ('03', 1, 7)
            ]
        
        service = FeatureService(stats_calculator=mock_calculator)
        result = service.calculate_loto_stats('dummy_data', 7)
        
        assert result == {'01': 5, '02': 3, '03': 1}
    
    def test_calculate_handles_exceptions(self):
        """Should handle exceptions gracefully"""
        def faulty_calculator(data, days):
            raise ValueError("Test error")
        
        service = FeatureService(stats_calculator=faulty_calculator)
        result = service.calculate_loto_stats('data', 7)
        
        assert result == {}


class TestCalculateGanStats:
    """Tests for calculate_gan_stats method"""
    
    def test_calculate_with_no_calculator(self):
        """Should return empty dict when no calculator provided"""
        service = FeatureService()
        result = service.calculate_gan_stats([], 8)
        
        assert result == {}
    
    def test_calculate_with_valid_calculator(self):
        """Should calculate gan stats using provided calculator"""
        def mock_calculator(data, days):
            return [
                ('01', 3),
                ('02', 5),
                ('03', 0)
            ]
        
        service = FeatureService(gan_calculator=mock_calculator)
        result = service.calculate_gan_stats('dummy_data', 8)
        
        assert result == {'01': 3, '02': 5, '03': 0}
    
    def test_calculate_handles_exceptions(self):
        """Should handle exceptions gracefully"""
        def faulty_calculator(data, days):
            raise ValueError("Test error")
        
        service = FeatureService(gan_calculator=faulty_calculator)
        result = service.calculate_gan_stats('data', 8)
        
        assert result == {}


class TestExtractFeaturesForLoto:
    """Tests for extract_features_for_loto method"""
    
    def test_extract_basic_features(self):
        """Should extract all 9 features correctly"""
        def mock_extractor(data):
            return ['01', '05']  # Previous day results
        
        service = FeatureService(loto_extractor=mock_extractor)
        
        loto_stats = {'01': 5, '02': 3}
        gan_stats = {'01': 3, '02': 1}
        bridge_features = {
            'v5_count': 10,
            'v17_count': 5,
            'memory_count': 3,
            'q_avg_win_rate': 75.0,
            'q_min_k2n_risk': 2.0,
            'q_max_curr_streak': 4.0
        }
        
        features = service.extract_features_for_loto(
            loto='01',
            previous_data='dummy_data',
            bridge_features=bridge_features,
            loto_stats=loto_stats,
            gan_stats=gan_stats,
            stats_days=7,
            gan_max_days=8
        )
        
        assert len(features) == 9
        assert features[0] == pytest.approx(5/7)  # F1: hot frequency
        assert features[1] == pytest.approx(3/8)  # F2: gan frequency
        assert features[2] == 10  # F3: v5_count
        assert features[3] == 5   # F4: v17_count
        assert features[4] == 3   # F5: memory_count
        assert features[5] == 1   # F6: came yesterday (01 in previous)
        assert features[6] == pytest.approx(0.75)  # F7: avg win rate
        assert features[7] == pytest.approx(1.0/3.0)  # F8: risk feature
        assert features[8] == pytest.approx(0.04)  # F9: streak feature
    
    def test_extract_with_missing_bridge_features(self):
        """Should handle missing bridge features with defaults"""
        service = FeatureService(loto_extractor=lambda x: [])
        
        features = service.extract_features_for_loto(
            loto='99',
            previous_data='dummy',
            bridge_features={},  # Empty features
            loto_stats={},
            gan_stats={},
            stats_days=7,
            gan_max_days=8
        )
        
        assert len(features) == 9
        assert features[2] == 0  # v5_count default
        assert features[3] == 0  # v17_count default
        assert features[4] == 0  # memory_count default
        assert features[6] == 0.0  # q_avg_win_rate default
    
    def test_extract_handles_zero_days(self):
        """Should handle zero days without division error"""
        service = FeatureService(loto_extractor=lambda x: [])
        
        features = service.extract_features_for_loto(
            loto='01',
            previous_data='dummy',
            bridge_features={},
            loto_stats={'01': 5},
            gan_stats={'01': 3},
            stats_days=0,
            gan_max_days=0
        )
        
        assert features[0] == 0  # Should handle division by zero
        assert features[1] == 0  # Should handle division by zero


class TestPrepareFeaturesForPeriod:
    """Tests for prepare_features_for_period method"""
    
    def test_prepare_with_valid_data(self):
        """Should prepare features for all lotos in period"""
        def mock_extractor(data):
            if data == ['period_1']:
                return ['01', '02']
            return []
        
        def mock_stats(data, days):
            return [('01', 5, 7), ('02', 3, 7)]
        
        def mock_gan(data, days):
            return [('01', 3), ('02', 1)]
        
        service = FeatureService(
            loto_extractor=mock_extractor,
            stats_calculator=mock_stats,
            gan_calculator=mock_gan
        )
        
        all_data = [
            ['period_0'],
            ['period_1']
        ]
        
        bridge_predictions = {
            'period_1': {
                '01': {'v5_count': 10, 'v17_count': 5, 'memory_count': 3},
                '02': {'v5_count': 8, 'v17_count': 4, 'memory_count': 2}
            }
        }
        
        features_list, labels_list = service.prepare_features_for_period(
            all_data=all_data,
            period_index=1,
            bridge_predictions=bridge_predictions,
            all_lotos=['01', '02'],
            stats_days=7,
            gan_max_days=8
        )
        
        assert len(features_list) == 2  # 2 lotos
        assert len(labels_list) == 2
        assert all(len(f) == 9 for f in features_list)  # 9 features each
        assert labels_list == [1, 1]  # Both 01 and 02 in results
    
    def test_prepare_with_invalid_period_index(self):
        """Should return empty lists for invalid period index"""
        service = FeatureService()
        
        features, labels = service.prepare_features_for_period(
            all_data=[['data1'], ['data2']],
            period_index=0,  # Invalid: need at least 1
            bridge_predictions={},
            all_lotos=['01'],
            stats_days=7,
            gan_max_days=8
        )
        
        assert features == []
        assert labels == []
    
    def test_prepare_with_out_of_bounds_index(self):
        """Should return empty lists for out of bounds index"""
        service = FeatureService()
        
        features, labels = service.prepare_features_for_period(
            all_data=[['data1'], ['data2']],
            period_index=10,  # Out of bounds
            bridge_predictions={},
            all_lotos=['01'],
            stats_days=7,
            gan_max_days=8
        )
        
        assert features == []
        assert labels == []


class TestCreateDefaultService:
    """Tests for create_default_service factory method"""
    
    def test_create_default_service(self):
        """Should create service with dependencies (or None if import fails)"""
        service = FeatureService.create_default_service()
        
        assert isinstance(service, FeatureService)
        # Dependencies may be None or functions depending on import success
        # Just verify the service is created properly


class TestFeatureServiceIntegration:
    """Integration tests for FeatureService"""
    
    def test_full_feature_extraction_pipeline(self):
        """Should extract features through full pipeline"""
        def mock_extractor(data):
            # Simulate extracting lotos from data
            if data == ['ky2', 10, 20, 30]:
                return ['01', '05', '10']
            elif data == ['ky1', 5, 15, 25]:
                return ['01', '02']
            return []
        
        def mock_stats(data, days):
            return [('01', 2, days), ('05', 1, days)]
        
        def mock_gan(data, days):
            return [('01', 3), ('05', 5)]
        
        service = FeatureService(
            loto_extractor=mock_extractor,
            stats_calculator=mock_stats,
            gan_calculator=mock_gan
        )
        
        # Simulate 2 periods of data
        all_data = [
            ['ky1', 5, 15, 25],
            ['ky2', 10, 20, 30]
        ]
        
        bridge_predictions = {
            'ky2': {
                '01': {
                    'v5_count': 15,
                    'v17_count': 8,
                    'memory_count': 5,
                    'q_avg_win_rate': 80.0,
                    'q_min_k2n_risk': 1.5,
                    'q_max_curr_streak': 6.0
                }
            }
        }
        
        features_list, labels_list = service.prepare_features_for_period(
            all_data=all_data,
            period_index=1,
            bridge_predictions=bridge_predictions,
            all_lotos=['01'],
            stats_days=7,
            gan_max_days=8
        )
        
        assert len(features_list) == 1
        assert len(features_list[0]) == 9
        assert labels_list[0] == 1  # '01' is in ky2 results
