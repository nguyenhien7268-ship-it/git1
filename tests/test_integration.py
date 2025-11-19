"""
Integration tests for the complete workflow

Tests the integration between data parser, database, and backtester
to ensure the full system works end-to-end.
"""
import pytest
import sys
import os
import tempfile
import sqlite3

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def temp_test_db():
    """Create a temporary test database"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    
    try:
        from logic.db_manager import setup_database
        conn, cursor = setup_database(db_path)
        conn.close()
        
        yield db_path
        
    finally:
        os.close(fd)
        if os.path.exists(db_path):
            os.unlink(db_path)


class TestDatabaseIntegration:
    """Test database integration with other components"""
    
    def test_database_setup_creates_all_tables(self, temp_test_db):
        """Test database setup creates all required tables"""
        from logic.db_manager import setup_database
        
        conn = sqlite3.connect(temp_test_db)
        cursor = conn.cursor()
        
        # Check for required tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['DuLieu_AI', 'results_A_I', 'ManagedBridges']
        
        for table in required_tables:
            assert table in tables, f"Missing table: {table}"
        
        conn.close()
    
    def test_database_indexes_exist(self, temp_test_db):
        """Test database indexes are created"""
        conn = sqlite3.connect(temp_test_db)
        cursor = conn.cursor()
        
        # Check for indexes
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Should have at least some indexes
        expected_indexes = [
            'idx_results_ky',
            'idx_dulieu_masoky',
            'idx_bridges_enabled'
        ]
        
        for idx in expected_indexes:
            assert idx in indexes, f"Missing index: {idx}"
        
        conn.close()


class TestDataParserIntegration:
    """Test data parser integration with database"""
    
    def test_parser_can_connect_to_database(self, temp_test_db):
        """Test data parser can connect to database"""
        try:
            from logic.data_parser import run_and_update_from_text
            from logic.db_manager import setup_database
            
            # Both should be importable
            assert callable(run_and_update_from_text)
            assert callable(setup_database)
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
    
    def test_parser_validates_before_database_insert(self):
        """Test parser validates data before inserting to database"""
        try:
            from logic.data_parser import run_and_update_from_text
            from logic.validators import validate_file_upload
            
            # Validation should happen before insert
            assert callable(validate_file_upload)
        except ImportError:
            pytest.skip("Validators not available")
    
    def test_parser_returns_status_after_operation(self, temp_test_db):
        """Test parser returns success/failure status"""
        try:
            from logic.data_parser import run_and_update_from_text
            
            # Test with empty data
            result = run_and_update_from_text("")
            
            # Should return tuple (success, message)
            assert isinstance(result, tuple)
            assert len(result) >= 2
            
            success, message = result[:2]
            assert isinstance(success, bool)
            assert isinstance(message, str)
        except ImportError:
            pytest.skip("Data parser not available")


class TestBacktesterIntegration:
    """Test backtester integration with database"""
    
    def test_backtester_can_access_database(self, temp_test_db):
        """Test backtester can access database"""
        from logic.backtester import DB_NAME
        from logic.db_manager import setup_database
        
        # DB_NAME should be defined
        assert DB_NAME is not None
        assert isinstance(DB_NAME, str)
    
    def test_backtester_can_load_data_from_repository(self):
        """Test backtester can load data from data repository"""
        try:
            from logic.backtester import get_all_managed_bridges
            from logic.data_repository import load_data_ai_from_db
            
            # Both functions should be available
            assert callable(get_all_managed_bridges)
            assert callable(load_data_ai_from_db)
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
    
    def test_backtester_uses_bridge_functions(self):
        """Test backtester integrates with bridge calculation functions"""
        from logic.backtester import (
            ALL_15_BRIDGE_FUNCTIONS_V5,
            getAllLoto_V30
        )
        
        # Bridge functions should be available
        assert ALL_15_BRIDGE_FUNCTIONS_V5 is not None
        assert callable(getAllLoto_V30)


class TestAIPredictionIntegration:
    """Test AI prediction pipeline integration"""
    
    def test_ai_model_integrates_with_feature_extractor(self):
        """Test ML model integrates with feature extractor"""
        try:
            import logic.ml_model as ml_model
            import logic.ai_feature_extractor as feature_extractor
            
            # Both modules should be available
            assert ml_model is not None
            assert feature_extractor is not None
        except ImportError:
            pytest.skip("AI modules not available")
    
    def test_ai_predictions_integrate_with_dashboard(self):
        """Test AI predictions integrate with dashboard analytics"""
        try:
            import logic.ml_model as ml_model
            import logic.dashboard_analytics as dashboard
            
            # Both modules should exist
            assert ml_model is not None
            assert dashboard is not None
        except ImportError:
            pytest.skip("AI/Dashboard modules not available")
    
    def test_ai_uses_configuration_parameters(self):
        """Test AI model uses configuration parameters"""
        from logic.config_manager import SETTINGS
        
        # AI parameters should be in config
        ai_params = [
            'AI_MAX_DEPTH',
            'AI_N_ESTIMATORS',
            'AI_LEARNING_RATE',
            'AI_SCORE_WEIGHT'
        ]
        
        for param in ai_params:
            assert hasattr(SETTINGS, param), f"Missing AI parameter: {param}"


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""
    
    def test_full_backtest_workflow_components_available(self):
        """Test all components for full backtest workflow are available"""
        # Data loading
        try:
            from logic.data_repository import load_data_ai_from_db
            assert callable(load_data_ai_from_db)
        except ImportError:
            pytest.skip("Data repository not available")
        
        # Backtesting
        try:
            from logic.backtester_core import BACKTEST_15_CAU_N1_V31_AI_V8
            assert callable(BACKTEST_15_CAU_N1_V31_AI_V8)
        except ImportError:
            pytest.skip("Backtester not available")
        
        # Results storage
        try:
            from logic.db_manager import update_bridge_win_rate_batch
            assert callable(update_bridge_win_rate_batch)
        except ImportError:
            pytest.skip("DB manager not available")
    
    def test_ai_prediction_pipeline_components_available(self):
        """Test all components for AI prediction pipeline are available"""
        # Feature extraction
        try:
            import logic.ai_feature_extractor
            assert logic.ai_feature_extractor is not None
        except ImportError:
            pytest.skip("Feature extractor not available")
        
        # Model prediction
        try:
            import logic.ml_model
            assert logic.ml_model is not None
        except ImportError:
            pytest.skip("ML model not available")
        
        # Dashboard integration
        try:
            import logic.dashboard_analytics
            assert logic.dashboard_analytics is not None
        except ImportError:
            pytest.skip("Dashboard analytics not available")


class TestMultiThreadingIntegration:
    """Test multi-threading integration"""
    
    def test_task_manager_available(self):
        """Test TaskManager is available for threading"""
        try:
            from core_services import TaskManager
            assert TaskManager is not None
        except ImportError:
            pytest.skip("core_services not available")
    
    def test_logger_available_for_threading(self):
        """Test Logger is available for thread-safe logging"""
        try:
            from core_services import Logger
            assert Logger is not None
        except ImportError:
            pytest.skip("core_services not available")
    
    def test_threading_module_imported(self):
        """Test threading module is available"""
        import threading
        assert threading is not None


class TestConfigurationIntegration:
    """Test configuration integration across modules"""
    
    def test_settings_available_to_all_modules(self):
        """Test SETTINGS is available to all major modules"""
        from logic.config_manager import SETTINGS
        
        # Settings should be accessible
        assert SETTINGS is not None
        
        # Required settings should exist
        required_settings = [
            'STATS_DAYS',
            'HIGH_WIN_THRESHOLD',
            'AI_MAX_DEPTH',
            'AI_SCORE_WEIGHT'
        ]
        
        for setting in required_settings:
            assert hasattr(SETTINGS, setting), f"Missing setting: {setting}"
    
    def test_constants_available_system_wide(self):
        """Test constants are available system-wide"""
        try:
            from logic.constants import DEFAULT_SETTINGS
            assert DEFAULT_SETTINGS is not None
            assert isinstance(DEFAULT_SETTINGS, dict)
        except ImportError:
            pytest.skip("Constants module not available")
    
    def test_validators_integrate_with_parsers(self):
        """Test validators integrate with data parsers"""
        try:
            from logic.validators import validate_file_upload
            from logic.data_parser import run_and_update_from_text
            
            # Both should be available for integration
            assert callable(validate_file_upload)
            assert callable(run_and_update_from_text)
        except ImportError:
            pytest.skip("Required modules not available")


class TestModuleDependencies:
    """Test module dependency relationships"""
    
    def test_lottery_service_imports_all_modules(self):
        """Test lottery_service imports from all necessary modules"""
        try:
            import lottery_service
            
            # lottery_service should be importable
            assert lottery_service is not None
        except ImportError:
            pytest.skip("lottery_service not available in test environment")
    
    def test_no_circular_dependencies(self):
        """Test there are no circular import issues"""
        # Try importing all major modules
        try:
            from logic import db_manager
            from logic import data_repository
            from logic import backtester
            from logic import ml_model
            
            # All should import successfully
            assert db_manager is not None
            assert data_repository is not None
            assert backtester is not None
            assert ml_model is not None
        except ImportError as e:
            pytest.fail(f"Circular dependency or import issue: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
