namespace XsDas.Core.Models;

/// <summary>
/// Represents a managed bridge strategy (ManagedBridges table)
/// </summary>
public class ManagedBridge
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public bool IsEnabled { get; set; } = true;
    public DateTime DateAdded { get; set; } = DateTime.Now;
    public string WinRateText { get; set; } = "N/A";
    public int CurrentStreak { get; set; } = 0;
    public string NextPredictionStl { get; set; } = "N/A";
    public int? Pos1Idx { get; set; }
    public int? Pos2Idx { get; set; }
    public int MaxLoseStreakK2n { get; set; } = 0;
    public int RecentWinCount10 { get; set; } = 0;
    public string SearchRateText { get; set; } = "0.00%";
    public int SearchPeriod { get; set; } = 0;
    public bool IsPinned { get; set; } = false;
    public string Type { get; set; } = "UNKNOWN";
    
    // K1N/K2N rate columns (V11.2)
    public double K1nRateLo { get; set; } = 0.0;
    public double K1nRateDe { get; set; } = 0.0;
    public double K2nRateLo { get; set; } = 0.0;
    public double K2nRateDe { get; set; } = 0.0;
    public bool IsPending { get; set; } = true;
    public DateTime? ImportedAt { get; set; }
}
