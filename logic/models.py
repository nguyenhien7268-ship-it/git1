# logic/models.py
"""
Data models for K1N-primary detection flow.

Defines dataclasses for bridge candidates, scan results, and import configurations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Candidate:
    """
    Represents a bridge candidate detected by scanner.
    
    Used by scanners to return detected bridges without writing to DB.
    Contains both K1N and K2N rates for policy-based filtering.
    
    Attributes:
        name: Bridge name/identifier
        normalized_name: Normalized name for duplicate checking (lowercase, no special chars)
        type: Bridge type ('lo' or 'de')
        kind: Bridge kind ('single' for individual bridges, 'set' for grouped bridges)
        k1n_lo: K1N (real) rate for LO bridges (0-100)
        k1n_de: K1N (real) rate for DE bridges (0-100)
        k2n_lo: K2N (simulated) rate for LO bridges (0-100)
        k2n_de: K2N (simulated) rate for DE bridges (0-100)
        stl: Soi Tránh Lô prediction string
        reason: Detection reason/algorithm name
        detected_at: Timestamp of detection
        pos1_idx: Position 1 index (for V17 bridges)
        pos2_idx: Position 2 index (for V17 bridges)
        description: Bridge description
        streak: Current winning streak
        win_count_10: Wins in last 10 periods
        rate_missing: Whether rates are missing from cache
        metadata: Additional bridge-specific metadata
    """
    
    # Required fields
    name: str
    normalized_name: str
    type: str  # 'lo' or 'de'
    kind: str  # 'single' or 'set'
    
    # K1N rates (real backtest)
    k1n_lo: float = 0.0
    k1n_de: float = 0.0
    
    # K2N rates (simulated/cache)
    k2n_lo: float = 0.0
    k2n_de: float = 0.0
    
    # Bridge details
    stl: str = "N/A"
    reason: str = ""
    detected_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Position indices
    pos1_idx: Optional[int] = None
    pos2_idx: Optional[int] = None
    
    # Optional fields
    description: str = ""
    streak: int = 0
    win_count_10: int = 0
    rate_missing: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_primary_rate(self, policy_type: str = "k1n") -> float:
        """
        Get primary rate based on bridge type and policy.
        
        Args:
            policy_type: 'k1n' or 'k2n'
            
        Returns:
            Rate value (0-100)
        """
        if policy_type == "k1n":
            return self.k1n_lo if self.type == "lo" else self.k1n_de
        else:
            return self.k2n_lo if self.type == "lo" else self.k2n_de
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert candidate to dictionary for DB operations."""
        return {
            'name': self.name,
            'description': self.description,
            'type': f"{self.type.upper()}_{'SET' if self.kind == 'set' else 'SINGLE'}",
            'k1n_rate_lo': self.k1n_lo,
            'k1n_rate_de': self.k1n_de,
            'k2n_rate_lo': self.k2n_lo,
            'k2n_rate_de': self.k2n_de,
            'pos1_idx': self.pos1_idx,
            'pos2_idx': self.pos2_idx,
            'win_rate_text': f"{self.get_primary_rate('k1n'):.1f}%",
            'search_rate_text': f"{self.get_primary_rate('k2n'):.1f}%",
            'current_streak': self.streak,
            'next_prediction_stl': self.stl,
            'recent_win_count_10': self.win_count_10,
            'is_pending': 1,  # Default to pending
            'is_enabled': 0,  # Default to disabled
        }


@dataclass
class ScanResult:
    """
    Result of a bridge scanning operation.
    
    Attributes:
        candidates: List of detected bridge candidates
        total_scanned: Total number of bridges scanned
        excluded_count: Number of bridges excluded (duplicates)
        scan_duration: Scan duration in seconds
        metadata: Additional scan metadata (algorithm params, etc.)
    """
    candidates: List[Candidate] = field(default_factory=list)
    total_scanned: int = 0
    excluded_count: int = 0
    scan_duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def summary(self) -> str:
        """Get human-readable scan summary."""
        return (
            f"Scan completed in {self.scan_duration:.2f}s: "
            f"{len(self.candidates)} candidates found, "
            f"{self.excluded_count} excluded (duplicates)"
        )


@dataclass
class ImportConfig:
    """
    Configuration for bridge import operations.
    
    Attributes:
        policy_type: Import policy ('k1n_primary', 'k2n_primary', 'combined')
        threshold_k1n_lo: K1N threshold for LO bridges
        threshold_k1n_de: K1N threshold for DE bridges
        threshold_k2n_lo: K2N threshold for LO bridges
        threshold_k2n_de: K2N threshold for DE bridges
        fallback_to_k2n: Whether to fallback to K2N if K1N missing
        default_is_enabled: Default enabled state for imported bridges
        default_is_pending: Default pending state for imported bridges
        preview_only: If True, don't write to DB (preview mode)
        auto_approve: If True, set is_pending=0 and is_enabled=1
    """
    policy_type: str = "k1n_primary"
    threshold_k1n_lo: float = 85.0
    threshold_k1n_de: float = 90.0
    threshold_k2n_lo: float = 80.0
    threshold_k2n_de: float = 85.0
    fallback_to_k2n: bool = True
    default_is_enabled: bool = False
    default_is_pending: bool = True
    preview_only: bool = False
    auto_approve: bool = False
    
    def meets_threshold(self, candidate: Candidate) -> bool:
        """
        Check if candidate meets import threshold.
        
        Args:
            candidate: Bridge candidate to check
            
        Returns:
            True if candidate meets threshold
        """
        if self.policy_type == "k1n_primary":
            # Check K1N first
            k1n_rate = candidate.get_primary_rate("k1n")
            threshold = self.threshold_k1n_lo if candidate.type == "lo" else self.threshold_k1n_de
            
            if k1n_rate >= threshold:
                return True
            
            # Fallback to K2N if enabled and K1N is zero/missing
            if self.fallback_to_k2n and k1n_rate == 0.0:
                k2n_rate = candidate.get_primary_rate("k2n")
                threshold_k2n = self.threshold_k2n_lo if candidate.type == "lo" else self.threshold_k2n_de
                return k2n_rate >= threshold_k2n
            
            return False
        
        elif self.policy_type == "k2n_primary":
            k2n_rate = candidate.get_primary_rate("k2n")
            threshold = self.threshold_k2n_lo if candidate.type == "lo" else self.threshold_k2n_de
            return k2n_rate >= threshold
        
        elif self.policy_type == "combined":
            # Both K1N and K2N must meet threshold
            k1n_rate = candidate.get_primary_rate("k1n")
            k2n_rate = candidate.get_primary_rate("k2n")
            threshold_k1n = self.threshold_k1n_lo if candidate.type == "lo" else self.threshold_k1n_de
            threshold_k2n = self.threshold_k2n_lo if candidate.type == "lo" else self.threshold_k2n_de
            return k1n_rate >= threshold_k1n and k2n_rate >= threshold_k2n
        
        return False
