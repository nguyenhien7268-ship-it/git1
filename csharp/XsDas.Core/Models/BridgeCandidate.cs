using System;
using System.Collections.Generic;

namespace XsDas.Core.Models;

/// <summary>
/// Represents a bridge candidate detected by scanner (before DB storage)
/// Ported from: logic/models.py::Candidate
/// </summary>
public class BridgeCandidate
{
    public string Name { get; set; } = string.Empty;
    public string NormalizedName { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty; // 'lo' or 'de'
    public string Kind { get; set; } = string.Empty; // 'single' or 'set'
    
    // K1N rates (real backtest)
    public double K1nLo { get; set; }
    public double K1nDe { get; set; }
    
    // K2N rates (simulated/cache)
    public double K2nLo { get; set; }
    public double K2nDe { get; set; }
    
    // Bridge details
    public string Stl { get; set; } = "N/A";
    public string Reason { get; set; } = string.Empty;
    public DateTime DetectedAt { get; set; } = DateTime.Now;
    
    // Position indices
    public int? Pos1Idx { get; set; }
    public int? Pos2Idx { get; set; }
    
    // Optional fields
    public string Description { get; set; } = string.Empty;
    public int Streak { get; set; }
    public int WinCount10 { get; set; }
    public bool RateMissing { get; set; }
    public Dictionary<string, object> Metadata { get; set; } = new();
    
    /// <summary>
    /// Get primary rate based on bridge type and policy
    /// </summary>
    public double GetPrimaryRate(string policyType = "k1n")
    {
        if (policyType.ToLower() == "k1n")
            return Type == "lo" ? K1nLo : K1nDe;
        else
            return Type == "lo" ? K2nLo : K2nDe;
    }
    
    /// <summary>
    /// Convert candidate to Bridge entity for DB storage
    /// </summary>
    public Bridge ToBridge()
    {
        var typePrefix = Type.ToUpper();
        var typeSuffix = Kind == "set" ? "SET" : "SINGLE";
        
        return new Bridge
        {
            Name = Name,
            NormalizedName = NormalizedName,
            Description = Description,
            Type = $"{typePrefix}_{typeSuffix}",
            Kind = Kind,
            K1nRateLo = K1nLo,
            K1nRateDe = K1nDe,
            K2nRateLo = K2nLo,
            K2nRateDe = K2nDe,
            Stl = Stl,
            Reason = Reason,
            DetectedAt = DetectedAt,
            CreatedAt = DateTime.Now,
            Pos1Idx = Pos1Idx,
            Pos2Idx = Pos2Idx,
            Streak = Streak,
            WinCount10 = WinCount10,
            RateMissing = RateMissing,
            IsEnabled = true
        };
    }
}
