# logic/bridge_importer.py
"""
Bridge Importer / Orchestrator for K1N-primary detection flow.

Handles importing bridge candidates with policy-based filtering and bulk DB operations.
"""

import time
from typing import List, Dict, Optional, Callable, Any

try:
    from logic.models import Candidate, ImportConfig, ScanResult
    from logic.db_manager import bulk_upsert_managed_bridges, get_all_managed_bridge_names, DB_NAME
    from logic.common_utils import normalize_bridge_name
    from logic.constants import DEFAULT_SETTINGS
except ImportError as e:
    print(f"[ERROR] Import failed in bridge_importer: {e}")
    raise


class BridgeImporter:
    """
    Service for importing bridge candidates with K1N-primary policy.
    
    Features:
    - Policy-based filtering (K1N-primary, K2N-primary, combined)
    - Preview mode (no DB writes)
    - Auto-import with pending/enabled states
    - Progress callback for UI integration
    - Atomic bulk operations
    
    Example:
        >>> config = ImportConfig(policy_type='k1n_primary', threshold_k1n_de=90.0)
        >>> importer = BridgeImporter(config)
        >>> result = importer.import_candidates(candidates)
        >>> print(f"Imported: {result['imported']}, Rejected: {result['rejected']}")
    """
    
    def __init__(
        self, 
        config: Optional[ImportConfig] = None,
        db_name: str = DB_NAME
    ):
        """
        Initialize bridge importer.
        
        Args:
            config: Import configuration (uses defaults if None)
            db_name: Database file path
        """
        self.config = config or self._create_default_config()
        self.db_name = db_name
        self.existing_names: Optional[set] = None
    
    def _create_default_config(self) -> ImportConfig:
        """Create default config from constants."""
        return ImportConfig(
            policy_type=DEFAULT_SETTINGS.get("POLICY_TYPE", "k1n_primary"),
            threshold_k1n_lo=DEFAULT_SETTINGS.get("THRESHOLD_K1N_LO", 85.0),
            threshold_k1n_de=DEFAULT_SETTINGS.get("THRESHOLD_K1N_DE", 90.0),
            threshold_k2n_lo=DEFAULT_SETTINGS.get("THRESHOLD_K2N_LO", 80.0),
            threshold_k2n_de=DEFAULT_SETTINGS.get("THRESHOLD_K2N_DE", 85.0),
            fallback_to_k2n=DEFAULT_SETTINGS.get("FALLBACK_TO_K2N", True),
            default_is_enabled=DEFAULT_SETTINGS.get("AUTO_IMPORT_DEFAULT_ENABLE", False),
            default_is_pending=DEFAULT_SETTINGS.get("AUTO_IMPORT_DEFAULT_PENDING", True),
        )
    
    def refresh_existing_names(self):
        """Load existing bridge names from database."""
        print("[INFO] Loading existing bridge names...")
        self.existing_names = get_all_managed_bridge_names(self.db_name)
        print(f"[INFO] Loaded {len(self.existing_names)} existing bridge names")
    
    def filter_candidates(
        self, 
        candidates: List[Candidate],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, List[Candidate]]:
        """
        Filter candidates based on policy and thresholds.
        
        Args:
            candidates: List of bridge candidates
            progress_callback: Optional callback(message, current, total)
            
        Returns:
            Dict with keys:
                - 'accepted': Candidates that pass policy
                - 'rejected': Candidates that fail policy
                - 'duplicates': Candidates already in DB
        """
        if self.existing_names is None:
            self.refresh_existing_names()
        
        result = {
            'accepted': [],
            'rejected': [],
            'duplicates': []
        }
        
        total = len(candidates)
        for idx, candidate in enumerate(candidates):
            if progress_callback:
                progress_callback(f"Filtering candidate {idx+1}/{total}", idx+1, total)
            
            # Check for duplicates
            if candidate.normalized_name in self.existing_names:
                result['duplicates'].append(candidate)
                continue
            
            # Apply policy
            if self.config.meets_threshold(candidate):
                result['accepted'].append(candidate)
                print(f"[INFO] ✓ Accepted: {candidate.name} (K1N={candidate.get_primary_rate('k1n'):.1f}%)")
            else:
                result['rejected'].append(candidate)
                print(f"[INFO] ✗ Rejected: {candidate.name} (K1N={candidate.get_primary_rate('k1n'):.1f}% < threshold)")
        
        print(f"[INFO] Filter result: {len(result['accepted'])} accepted, "
              f"{len(result['rejected'])} rejected, {len(result['duplicates'])} duplicates")
        
        return result
    
    def import_candidates(
        self,
        candidates: List[Candidate],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        preview_only: bool = False
    ) -> Dict[str, Any]:
        """
        Import bridge candidates to database.
        
        Args:
            candidates: List of bridge candidates to import
            progress_callback: Optional callback for progress updates
            preview_only: If True, skip DB write (preview mode)
            
        Returns:
            Dict with import statistics and results:
                - 'imported': Number successfully imported
                - 'rejected': Number rejected by policy
                - 'duplicates': Number already in DB
                - 'errors': Number with errors
                - 'accepted_list': List of accepted candidates
                - 'rejected_list': List of rejected candidates
                - 'duplicate_list': List of duplicate candidates
        """
        start_time = time.time()
        
        print(f"[INFO] Starting import of {len(candidates)} candidates...")
        print(f"[INFO] Policy: {self.config.policy_type}, Preview: {preview_only}")
        
        # Filter candidates
        filter_result = self.filter_candidates(candidates, progress_callback)
        
        accepted = filter_result['accepted']
        rejected = filter_result['rejected']
        duplicates = filter_result['duplicates']
        
        # Prepare import result
        result = {
            'imported': 0,
            'rejected': len(rejected),
            'duplicates': len(duplicates),
            'errors': 0,
            'accepted_list': accepted,
            'rejected_list': rejected,
            'duplicate_list': duplicates,
            'duration': 0.0
        }
        
        # Preview mode - skip DB write
        if preview_only or self.config.preview_only:
            print(f"[INFO] Preview mode - skipping DB write")
            result['duration'] = time.time() - start_time
            return result
        
        # Prepare bridges for bulk upsert
        bridges_to_import = []
        for candidate in accepted:
            bridge_dict = candidate.to_dict()
            
            # Apply config defaults
            if self.config.auto_approve:
                bridge_dict['is_pending'] = 0
                bridge_dict['is_enabled'] = 1
            else:
                bridge_dict['is_pending'] = 1 if self.config.default_is_pending else 0
                bridge_dict['is_enabled'] = 1 if self.config.default_is_enabled else 0
            
            bridges_to_import.append(bridge_dict)
        
        # Bulk import to DB
        if bridges_to_import:
            print(f"[INFO] Bulk importing {len(bridges_to_import)} bridges...")
            
            try:
                db_stats = bulk_upsert_managed_bridges(
                    bridges_to_import,
                    db_name=self.db_name,
                    transactional=True
                )
                
                result['imported'] = db_stats['added'] + db_stats['updated']
                result['errors'] = db_stats['errors']
                
                print(f"[INFO] Import complete: {result['imported']} imported, {result['errors']} errors")
                
            except Exception as e:
                print(f"[ERROR] Bulk import failed: {e}")
                result['errors'] = len(bridges_to_import)
        
        result['duration'] = time.time() - start_time
        return result
    
    def preview_import(
        self,
        candidates: List[Candidate],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Preview import without writing to database.
        
        Args:
            candidates: List of bridge candidates
            progress_callback: Optional callback for progress updates
            
        Returns:
            Preview result dictionary (same as import_candidates but no DB write)
        """
        return self.import_candidates(candidates, progress_callback, preview_only=True)
    
    def get_import_summary(self, result: Dict[str, Any]) -> str:
        """
        Get human-readable import summary.
        
        Args:
            result: Import result dictionary
            
        Returns:
            Summary string
        """
        summary_lines = [
            f"Import Summary:",
            f"  ✓ Imported: {result['imported']}",
            f"  ✗ Rejected: {result['rejected']} (below threshold)",
            f"  ⊜ Duplicates: {result['duplicates']} (already in DB)",
            f"  ⚠ Errors: {result['errors']}",
            f"  ⏱ Duration: {result['duration']:.2f}s"
        ]
        return "\n".join(summary_lines)


def create_importer_from_settings(settings_dict: Optional[Dict[str, Any]] = None) -> BridgeImporter:
    """
    Factory function to create importer from settings dictionary.
    
    Args:
        settings_dict: Settings dictionary (uses DEFAULT_SETTINGS if None)
        
    Returns:
        Configured BridgeImporter instance
    """
    if settings_dict is None:
        settings_dict = DEFAULT_SETTINGS
    
    config = ImportConfig(
        policy_type=settings_dict.get("POLICY_TYPE", "k1n_primary"),
        threshold_k1n_lo=settings_dict.get("THRESHOLD_K1N_LO", 85.0),
        threshold_k1n_de=settings_dict.get("THRESHOLD_K1N_DE", 90.0),
        threshold_k2n_lo=settings_dict.get("THRESHOLD_K2N_LO", 80.0),
        threshold_k2n_de=settings_dict.get("THRESHOLD_K2N_DE", 85.0),
        fallback_to_k2n=settings_dict.get("FALLBACK_TO_K2N", True),
        default_is_enabled=settings_dict.get("AUTO_IMPORT_DEFAULT_ENABLE", False),
        default_is_pending=settings_dict.get("AUTO_IMPORT_DEFAULT_PENDING", True),
    )
    
    return BridgeImporter(config)
