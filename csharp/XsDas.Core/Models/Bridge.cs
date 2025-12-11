namespace XsDas.Core.Models;

/// <summary>
/// Represents a managed bridge (corresponds to ManagedBridges table)
/// Bridges are prediction patterns used for lottery analysis
/// </summary>
public class Bridge
{
    public int Id { get; set; }
    
    /// <summary>
    /// Bridge name/identifier (unique)
    /// </summary>
    public string Name { get; set; } = string.Empty;
    
    /// <summary>
    /// Bridge description
    /// </summary>
    public string? Description { get; set; }
    
    /// <summary>
    /// Whether the bridge is enabled for analysis
    /// </summary>
    public bool IsEnabled { get; set; } = true;
    
    /// <summary>
    /// Date when bridge was added
    /// </summary>
    public DateTime DateAdded { get; set; } = DateTime.Now;
    
    /// <summary>
    /// Win rate text display (e.g., "85.5%")
    /// </summary>
    public string WinRateText { get; set; } = "N/A";
    
    /// <summary>
    /// Current winning streak
    /// </summary>
    public int CurrentStreak { get; set; }
    
    /// <summary>
    /// Next prediction STL (Soi Tránh Lô)
    /// </summary>
    public string NextPredictionStl { get; set; } = "N/A";
    
    /// <summary>
    /// Position 1 index (for V17/Bong bridges)
    /// </summary>
    public int? Pos1Idx { get; set; }
    
    /// <summary>
    /// Position 2 index (for V17/Bong bridges)
    /// </summary>
    public int? Pos2Idx { get; set; }
    
    /// <summary>
    /// Maximum losing streak in K2N testing
    /// </summary>
    public int MaxLoseStreakK2n { get; set; }
    
    /// <summary>
    /// Win count in recent 10 periods
    /// </summary>
    public int RecentWinCount10 { get; set; }
    
    /// <summary>
    /// Search rate text (e.g., "90.0%")
    /// </summary>
    public string SearchRateText { get; set; } = "0.00%";
    
    /// <summary>
    /// Search period count
    /// </summary>
    public int SearchPeriod { get; set; }
    
    /// <summary>
    /// Whether the bridge is pinned (priority display)
    /// </summary>
    public bool IsPinned { get; set; }
    
    /// <summary>
    /// Bridge type (e.g., LO_V17, DE_DYN, DE_SET, etc.)
    /// </summary>
    public string Type { get; set; } = "UNKNOWN";
    
    /// <summary>
    /// K1N rate for LO bridges (real backtest rate)
    /// </summary>
    public double K1nRateLo { get; set; }
    
    /// <summary>
    /// K1N rate for DE bridges (real backtest rate)
    /// </summary>
    public double K1nRateDe { get; set; }
    
    /// <summary>
    /// K2N rate for LO bridges (simulated rate)
    /// </summary>
    public double K2nRateLo { get; set; }
    
    /// <summary>
    /// K2N rate for DE bridges (simulated rate)
    /// </summary>
    public double K2nRateDe { get; set; }
    
    /// <summary>
    /// Whether bridge is pending approval
    /// </summary>
    public bool IsPending { get; set; } = true;
    
    /// <summary>
    /// When bridge was imported
    /// </summary>
    public DateTime ImportedAt { get; set; } = DateTime.Now;
}
