using System;

namespace XsDas.Core.Models;

/// <summary>
/// Represents a lottery bridge strategy (Cầu)
/// Ported from: logic/models.py::Candidate and database ManagedBridges table
/// </summary>
public class Bridge
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string NormalizedName { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    
    /// <summary>
    /// Bridge type: LO_SINGLE, LO_SET, DE_SINGLE, DE_SET, etc.
    /// </summary>
    public string Type { get; set; } = string.Empty;
    
    /// <summary>
    /// Bridge kind: 'single' or 'set'
    /// </summary>
    public string Kind { get; set; } = string.Empty;
    
    // Performance metrics
    public double K1nRateLo { get; set; }
    public double K1nRateDe { get; set; }
    public double K2nRateLo { get; set; }
    public double K2nRateDe { get; set; }
    
    /// <summary>
    /// STL (Soi Tránh Lô) - prediction string
    /// </summary>
    public string Stl { get; set; } = string.Empty;
    
    /// <summary>
    /// Detection reason/algorithm name
    /// </summary>
    public string Reason { get; set; } = string.Empty;
    
    public DateTime DetectedAt { get; set; }
    public DateTime CreatedAt { get; set; }
    
    // Position indices for V17 bridges
    public int? Pos1Idx { get; set; }
    public int? Pos2Idx { get; set; }
    
    // Status and performance
    public int Streak { get; set; }
    public int WinCount10 { get; set; }
    public bool IsEnabled { get; set; } = true;
    public bool RateMissing { get; set; }
    
    /// <summary>
    /// Get primary rate based on bridge type and policy
    /// Ported from: logic/models.py::Candidate::get_primary_rate
    /// </summary>
    public double GetPrimaryRate(string policyType = "k1n")
    {
        var isLoType = Type.Contains("LO");
        
        if (policyType.ToLower() == "k1n")
            return isLoType ? K1nRateLo : K1nRateDe;
        else
            return isLoType ? K2nRateLo : K2nRateDe;
    }
}
