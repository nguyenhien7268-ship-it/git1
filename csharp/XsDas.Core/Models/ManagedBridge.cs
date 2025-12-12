namespace XsDas.Core.Models;

/// <summary>
/// Represents a managed bridge record from ManagedBridges table.
/// Maps to Python's ManagedBridges table schema with K1N/K2N rate support.
/// </summary>
public class ManagedBridge
{
    public int Id { get; set; }
    
    /// <summary>
    /// Bridge name (unique identifier)
    /// </summary>
    public string Name { get; set; } = string.Empty;
    
    /// <summary>
    /// Bridge description
    /// </summary>
    public string? Description { get; set; }
    
    /// <summary>
    /// Whether the bridge is currently enabled
    /// </summary>
    public bool IsEnabled { get; set; } = true;
    
    /// <summary>
    /// Date when bridge was added to management
    /// </summary>
    public string DateAdded { get; set; } = string.Empty;
    
    /// <summary>
    /// Win rate text (formatted percentage)
    /// </summary>
    public string WinRateText { get; set; } = "N/A";
    
    /// <summary>
    /// Current winning/losing streak
    /// </summary>
    public int CurrentStreak { get; set; } = 0;
    
    /// <summary>
    /// Next prediction STL (Soi Tránh Lô)
    /// </summary>
    public string NextPredictionStl { get; set; } = "N/A";
    
    /// <summary>
    /// Position 1 index (for V17 bridges)
    /// </summary>
    public int? Pos1Idx { get; set; }
    
    /// <summary>
    /// Position 2 index (for V17 bridges)
    /// </summary>
    public int? Pos2Idx { get; set; }
    
    /// <summary>
    /// Maximum losing streak in K2N simulation
    /// </summary>
    public int MaxLoseStreakK2n { get; set; } = 0;
    
    /// <summary>
    /// Recent win count in last 10 periods
    /// </summary>
    public int RecentWinCount10 { get; set; } = 0;
    
    /// <summary>
    /// Search rate text (K2N rate formatted)
    /// </summary>
    public string SearchRateText { get; set; } = "0.00%";
    
    /// <summary>
    /// Search period for K2N simulation
    /// </summary>
    public int SearchPeriod { get; set; } = 0;
    
    /// <summary>
    /// Whether the bridge is pinned
    /// </summary>
    public bool IsPinned { get; set; } = false;
    
    /// <summary>
    /// Bridge type (e.g., DE_DYN, DE_SET, LO_SINGLE)
    /// </summary>
    public string Type { get; set; } = "UNKNOWN";
    
    // K1N rates (real backtest) - V11.2
    /// <summary>
    /// K1N (real) win rate for LO (Loto) bridges (0-100)
    /// </summary>
    public double K1nRateLo { get; set; } = 0.0;
    
    /// <summary>
    /// K1N (real) win rate for DE (Đề) bridges (0-100)
    /// </summary>
    public double K1nRateDe { get; set; } = 0.0;
    
    // K2N rates (simulated/cache) - V11.2
    /// <summary>
    /// K2N (simulated) win rate for LO bridges (0-100)
    /// </summary>
    public double K2nRateLo { get; set; } = 0.0;
    
    /// <summary>
    /// K2N (simulated) win rate for DE bridges (0-100)
    /// </summary>
    public double K2nRateDe { get; set; } = 0.0;
    
    /// <summary>
    /// Whether the bridge is pending approval
    /// </summary>
    public bool IsPending { get; set; } = true;
    
    /// <summary>
    /// Timestamp when bridge was imported
    /// </summary>
    public string? ImportedAt { get; set; }
}
