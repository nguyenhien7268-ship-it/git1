using System.Collections.Generic;
using System.Threading.Tasks;
using XsDas.Core.Models;

namespace XsDas.Core.Interfaces;

/// <summary>
/// Interface for lottery analysis services
/// Ported from: logic/de_analytics.py and logic/dashboard_analytics.py
/// </summary>
public interface IAnalysisService
{
    /// <summary>
    /// Calculate number scores for DE (Đề) analysis
    /// Ported from: logic/de_analytics.py::calculate_number_scores
    /// </summary>
    Task<Dictionary<string, double>> CalculateNumberScoresAsync(
        IEnumerable<LotteryResult> results, 
        AnalysisConfig config);
    
    /// <summary>
    /// Perform tiered scoring analysis
    /// </summary>
    Task<TieredScoringResult> PerformTieredScoringAsync(
        IEnumerable<LotteryResult> results,
        IEnumerable<Bridge> bridges);
    
    /// <summary>
    /// Calculate bridge performance metrics
    /// </summary>
    Task<BridgePerformanceMetrics> CalculatePerformanceMetricsAsync(
        Bridge bridge,
        IEnumerable<LotteryResult> results);
}

/// <summary>
/// Configuration for analysis operations
/// </summary>
public class AnalysisConfig
{
    public int WindowSize { get; set; } = 30;
    public int MinConsecutive { get; set; } = 8;
    public double MinWinRate { get; set; } = 50.0;
}

/// <summary>
/// Result of tiered scoring analysis
/// </summary>
public class TieredScoringResult
{
    public Dictionary<string, double> Scores { get; set; } = new();
    public List<string> HotNumbers { get; set; } = new();
    public Dictionary<string, string> Reasons { get; set; } = new();
}

/// <summary>
/// Performance metrics for a bridge
/// </summary>
public class BridgePerformanceMetrics
{
    public int Streak { get; set; }
    public int TotalWins { get; set; }
    public double WinRate { get; set; }
    public int Wins10 { get; set; }
    public int TotalDays { get; set; }
}
