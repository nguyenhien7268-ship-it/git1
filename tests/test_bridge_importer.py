# tests/test_bridge_importer.py
"""
Unit tests for bridge_importer.py (V11.2 K1N-primary flow).

Tests:
- BridgeImporter policy decisions
- K1N-primary policy
- K2N fallback logic
- Preview mode
- Bulk import operations
"""

import pytest
from unittest.mock import Mock, patch

from logic.bridge_importer import BridgeImporter, create_importer_from_settings
from logic.models import Candidate, ImportConfig


@pytest.fixture
def sample_candidates():
    """Create sample bridge candidates for testing."""
    return [
        Candidate(
            name="High-K1N-Bridge",
            normalized_name="highk1nbridge",
            type="de",
            kind="single",
            k1n_de=95.0,
            k2n_de=88.0,
            description="High K1N DE bridge"
        ),
        Candidate(
            name="Low-K1N-Bridge",
            normalized_name="lowk1nbridge",
            type="de",
            kind="single",
            k1n_de=75.0,
            k2n_de=90.0,
            description="Low K1N, high K2N DE bridge"
        ),
        Candidate(
            name="Missing-K1N-Bridge",
            normalized_name="missingk1nbridge",
            type="lo",
            kind="single",
            k1n_lo=0.0,
            k2n_lo=88.0,
            rate_missing=True,
            description="Missing K1N LO bridge"
        ),
        Candidate(
            name="Good-LO-Bridge",
            normalized_name="goodlobridge",
            type="lo",
            kind="single",
            k1n_lo=90.0,
            k2n_lo=85.0,
            description="Good LO bridge"
        ),
    ]


class TestImportConfig:
    """Test ImportConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ImportConfig()
        
        assert config.policy_type == "k1n_primary"
        assert config.threshold_k1n_lo == 85.0
        assert config.threshold_k1n_de == 90.0
        assert config.fallback_to_k2n is True
        assert config.default_is_enabled is False
        assert config.default_is_pending is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ImportConfig(
            policy_type="k2n_primary",
            threshold_k2n_de=95.0,
            fallback_to_k2n=False
        )
        
        assert config.policy_type == "k2n_primary"
        assert config.threshold_k2n_de == 95.0
        assert config.fallback_to_k2n is False
    
    def test_meets_threshold_k1n_primary(self):
        """Test K1N-primary policy threshold check."""
        config = ImportConfig(
            policy_type="k1n_primary",
            threshold_k1n_de=90.0,
            threshold_k1n_lo=85.0
        )
        
        # DE bridge above threshold
        candidate_de = Candidate(
            name="DE-Bridge",
            normalized_name="debridge",
            type="de",
            kind="single",
            k1n_de=92.0,
            k2n_de=85.0
        )
        assert config.meets_threshold(candidate_de) is True
        
        # DE bridge below threshold
        candidate_de_low = Candidate(
            name="DE-Bridge-Low",
            normalized_name="debridgelow",
            type="de",
            kind="single",
            k1n_de=85.0,
            k2n_de=95.0
        )
        assert config.meets_threshold(candidate_de_low) is False
        
        # LO bridge above threshold
        candidate_lo = Candidate(
            name="LO-Bridge",
            normalized_name="lobridge",
            type="lo",
            kind="single",
            k1n_lo=88.0,
            k2n_lo=80.0
        )
        assert config.meets_threshold(candidate_lo) is True
    
    def test_meets_threshold_with_fallback(self):
        """Test K1N-primary with K2N fallback."""
        config = ImportConfig(
            policy_type="k1n_primary",
            threshold_k1n_de=90.0,
            threshold_k2n_de=85.0,
            fallback_to_k2n=True
        )
        
        # K1N missing, K2N above threshold -> accept
        candidate = Candidate(
            name="Missing-K1N",
            normalized_name="missingk1n",
            type="de",
            kind="single",
            k1n_de=0.0,
            k2n_de=88.0
        )
        assert config.meets_threshold(candidate) is True
        
        # K1N missing, K2N below threshold -> reject
        candidate_low = Candidate(
            name="Missing-K1N-Low",
            normalized_name="missingk1nlow",
            type="de",
            kind="single",
            k1n_de=0.0,
            k2n_de=80.0
        )
        assert config.meets_threshold(candidate_low) is False
    
    def test_meets_threshold_no_fallback(self):
        """Test K1N-primary without K2N fallback."""
        config = ImportConfig(
            policy_type="k1n_primary",
            threshold_k1n_de=90.0,
            threshold_k2n_de=85.0,
            fallback_to_k2n=False
        )
        
        # K1N missing -> reject even if K2N is high
        candidate = Candidate(
            name="Missing-K1N",
            normalized_name="missingk1n",
            type="de",
            kind="single",
            k1n_de=0.0,
            k2n_de=95.0
        )
        assert config.meets_threshold(candidate) is False
    
    def test_meets_threshold_k2n_primary(self):
        """Test K2N-primary policy."""
        config = ImportConfig(
            policy_type="k2n_primary",
            threshold_k2n_de=85.0
        )
        
        # K2N above threshold
        candidate = Candidate(
            name="High-K2N",
            normalized_name="highk2n",
            type="de",
            kind="single",
            k1n_de=70.0,
            k2n_de=90.0
        )
        assert config.meets_threshold(candidate) is True
        
        # K2N below threshold
        candidate_low = Candidate(
            name="Low-K2N",
            normalized_name="lowk2n",
            type="de",
            kind="single",
            k1n_de=95.0,
            k2n_de=80.0
        )
        assert config.meets_threshold(candidate_low) is False
    
    def test_meets_threshold_combined_policy(self):
        """Test combined policy (both K1N and K2N must pass)."""
        config = ImportConfig(
            policy_type="combined",
            threshold_k1n_de=85.0,
            threshold_k2n_de=85.0
        )
        
        # Both above threshold -> accept
        candidate_both = Candidate(
            name="Both-High",
            normalized_name="bothhigh",
            type="de",
            kind="single",
            k1n_de=90.0,
            k2n_de=88.0
        )
        assert config.meets_threshold(candidate_both) is True
        
        # K1N high, K2N low -> reject
        candidate_k1n = Candidate(
            name="K1N-Only",
            normalized_name="k1nonly",
            type="de",
            kind="single",
            k1n_de=92.0,
            k2n_de=80.0
        )
        assert config.meets_threshold(candidate_k1n) is False
        
        # K1N low, K2N high -> reject
        candidate_k2n = Candidate(
            name="K2N-Only",
            normalized_name="k2nonly",
            type="de",
            kind="single",
            k1n_de=80.0,
            k2n_de=90.0
        )
        assert config.meets_threshold(candidate_k2n) is False


class TestBridgeImporter:
    """Test BridgeImporter class."""
    
    @patch('logic.bridge_importer.get_all_managed_bridge_names')
    def test_filter_candidates_accepts_high_k1n(self, mock_get_names, sample_candidates, temp_db):
        """Test filter accepts candidates with high K1N."""
        conn, cursor, db_path = temp_db
        mock_get_names.return_value = set()
        
        config = ImportConfig(
            policy_type="k1n_primary",
            threshold_k1n_de=90.0
        )
        importer = BridgeImporter(config, db_name=db_path)
        
        # Filter only high K1N candidates
        result = importer.filter_candidates([sample_candidates[0]])
        
        assert len(result['accepted']) == 1
        assert len(result['rejected']) == 0
        assert result['accepted'][0].name == "High-K1N-Bridge"
    
    @patch('logic.bridge_importer.get_all_managed_bridge_names')
    def test_filter_candidates_rejects_low_k1n(self, mock_get_names, sample_candidates, temp_db):
        """Test filter rejects candidates with low K1N."""
        conn, cursor, db_path = temp_db
        mock_get_names.return_value = set()
        
        config = ImportConfig(
            policy_type="k1n_primary",
            threshold_k1n_de=90.0
        )
        importer = BridgeImporter(config, db_name=db_path)
        
        # Filter low K1N candidate
        result = importer.filter_candidates([sample_candidates[1]])
        
        assert len(result['accepted']) == 0
        assert len(result['rejected']) == 1
        assert result['rejected'][0].name == "Low-K1N-Bridge"
    
    @patch('logic.bridge_importer.get_all_managed_bridge_names')
    def test_filter_candidates_fallback_to_k2n(self, mock_get_names, sample_candidates, temp_db):
        """Test filter falls back to K2N when K1N missing."""
        conn, cursor, db_path = temp_db
        mock_get_names.return_value = set()
        
        config = ImportConfig(
            policy_type="k1n_primary",
            threshold_k1n_lo=85.0,
            threshold_k2n_lo=85.0,
            fallback_to_k2n=True
        )
        importer = BridgeImporter(config, db_name=db_path)
        
        # Filter candidate with missing K1N but good K2N
        result = importer.filter_candidates([sample_candidates[2]])
        
        assert len(result['accepted']) == 1
        assert result['accepted'][0].name == "Missing-K1N-Bridge"
    
    @patch('logic.bridge_importer.get_all_managed_bridge_names')
    def test_filter_candidates_excludes_duplicates(self, mock_get_names, sample_candidates, temp_db):
        """Test filter excludes candidates already in DB."""
        conn, cursor, db_path = temp_db
        
        # Mock existing names
        mock_get_names.return_value = {"highk1nbridge"}  # Already exists
        
        config = ImportConfig(policy_type="k1n_primary", threshold_k1n_de=90.0)
        importer = BridgeImporter(config, db_name=db_path)
        
        result = importer.filter_candidates([sample_candidates[0]])
        
        assert len(result['duplicates']) == 1
        assert len(result['accepted']) == 0
        assert result['duplicates'][0].name == "High-K1N-Bridge"
    
    @patch('logic.bridge_importer.get_all_managed_bridge_names')
    @patch('logic.bridge_importer.bulk_upsert_managed_bridges')
    def test_import_candidates_preview_mode(self, mock_bulk_upsert, mock_get_names, sample_candidates, temp_db):
        """Test import in preview mode doesn't write to DB."""
        conn, cursor, db_path = temp_db
        mock_get_names.return_value = set()
        mock_bulk_upsert.return_value = {'added': 0, 'updated': 0, 'errors': 0}
        
        config = ImportConfig(
            policy_type="k1n_primary",
            threshold_k1n_de=90.0,
            threshold_k1n_lo=85.0
        )
        importer = BridgeImporter(config, db_name=db_path)
        
        result = importer.import_candidates(sample_candidates, preview_only=True)
        
        # Should not call bulk_upsert in preview mode
        mock_bulk_upsert.assert_not_called()
        assert result['imported'] == 0
        assert len(result['accepted_list']) > 0  # But should still filter
    
    @patch('logic.bridge_importer.get_all_managed_bridge_names')
    @patch('logic.bridge_importer.bulk_upsert_managed_bridges')
    def test_import_candidates_normal_mode(self, mock_bulk_upsert, mock_get_names, sample_candidates, temp_db):
        """Test import in normal mode writes to DB."""
        conn, cursor, db_path = temp_db
        mock_get_names.return_value = set()
        mock_bulk_upsert.return_value = {'added': 2, 'updated': 0, 'errors': 0, 'skipped': 0}
        
        config = ImportConfig(
            policy_type="k1n_primary",
            threshold_k1n_de=90.0,
            threshold_k1n_lo=85.0
        )
        importer = BridgeImporter(config, db_name=db_path)
        
        result = importer.import_candidates(sample_candidates, preview_only=False)
        
        # Should call bulk_upsert in normal mode
        mock_bulk_upsert.assert_called_once()
        assert result['imported'] == 2
    
    @patch('logic.bridge_importer.get_all_managed_bridge_names')
    def test_import_sets_default_states(self, mock_get_names, sample_candidates, temp_db):
        """Test import applies default enabled/pending states."""
        conn, cursor, db_path = temp_db
        mock_get_names.return_value = set()
        
        config = ImportConfig(
            policy_type="k1n_primary",
            threshold_k1n_de=85.0,
            default_is_enabled=False,
            default_is_pending=True
        )
        importer = BridgeImporter(config, db_name=db_path)
        
        # Get one accepted candidate
        high_k1n = sample_candidates[0]
        result = importer.preview_import([high_k1n])
        
        assert len(result['accepted_list']) == 1
        bridge_dict = result['accepted_list'][0].to_dict()
        assert bridge_dict['is_enabled'] == 0
        assert bridge_dict['is_pending'] == 1
    
    @patch('logic.bridge_importer.get_all_managed_bridge_names')
    @patch('logic.bridge_importer.bulk_upsert_managed_bridges')
    def test_import_auto_approve(self, mock_bulk_upsert, mock_get_names, sample_candidates, temp_db):
        """Test auto-approve mode."""
        conn, cursor, db_path = temp_db
        mock_get_names.return_value = set()
        mock_bulk_upsert.return_value = {'added': 1, 'updated': 0, 'errors': 0, 'skipped': 0}
        
        config = ImportConfig(
            policy_type="k1n_primary",
            threshold_k1n_de=85.0,
            auto_approve=True
        )
        importer = BridgeImporter(config, db_name=db_path)
        
        high_k1n = sample_candidates[0]
        # Must use normal import (not preview) to apply transformations
        result = importer.import_candidates([high_k1n], preview_only=False)
        
        # Check that bulk_upsert was called with correct flags
        call_args = mock_bulk_upsert.call_args
        bridges_arg = call_args[0][0]  # First positional arg
        assert len(bridges_arg) == 1
        assert bridges_arg[0]['is_enabled'] == 1
        assert bridges_arg[0]['is_pending'] == 0
    
    def test_get_import_summary(self, temp_db):
        """Test import summary generation."""
        conn, cursor, db_path = temp_db
        
        config = ImportConfig()
        importer = BridgeImporter(config, db_name=db_path)
        
        result = {
            'imported': 5,
            'rejected': 2,
            'duplicates': 1,
            'errors': 0,
            'duration': 1.23
        }
        
        summary = importer.get_import_summary(result)
        
        assert "Imported: 5" in summary
        assert "Rejected: 2" in summary
        assert "Duplicates: 1" in summary
        assert "Duration: 1.23s" in summary


class TestFactoryFunctions:
    """Test factory functions."""
    
    def test_create_importer_from_settings_default(self):
        """Test factory creates importer with default settings."""
        importer = create_importer_from_settings()
        
        assert importer.config.policy_type == "k1n_primary"
        assert importer.config.threshold_k1n_lo == 85.0
        assert importer.config.threshold_k1n_de == 90.0
    
    def test_create_importer_from_settings_custom(self):
        """Test factory creates importer with custom settings."""
        settings = {
            "POLICY_TYPE": "k2n_primary",
            "THRESHOLD_K2N_LO": 88.0,
            "THRESHOLD_K2N_DE": 92.0,
            "FALLBACK_TO_K2N": False
        }
        
        importer = create_importer_from_settings(settings)
        
        assert importer.config.policy_type == "k2n_primary"
        assert importer.config.threshold_k2n_lo == 88.0
        assert importer.config.threshold_k2n_de == 92.0
        assert importer.config.fallback_to_k2n is False
