namespace XsDas.Core.Interfaces;

/// <summary>
/// Service interface for backtesting bridge algorithms against historical data.
/// Evaluates prediction accuracy and performance metrics.
/// </summary>
public interface IBacktestingService
{
    /// <summary>
    /// Backtest a single bridge across historical lottery results
    /// </summary>
    /// <param name="bridgeName">Name of the bridge to test</param>
    /// <param name="startKy">Starting period (optional, null for all history)</param>
    /// <param name="endKy">Ending period (optional, null for latest)</param>
    /// <returns>Backtest results with win rate and metrics</returns>
    Task<BacktestResult> BacktestBridgeAsync(string bridgeName, string? startKy = null, string? endKy = null);

    /// <summary>
    /// Backtest all bridges and return sorted by performance
    /// </summary>
    /// <param name="minWinRate">Minimum win rate threshold (0-100)</param>
    /// <returns>List of backtest results sorted by win rate</returns>
    Task<List<BacktestResult>> BacktestAllBridgesAsync(double minWinRate = 0);

    /// <summary>
    /// Calculate K1N (real backtest) and K2N (simulated) rates for a bridge
    /// </summary>
    /// <param name="bridgeName">Name of the bridge</param>
    /// <param name="predictions">List of STL predictions</param>
    /// <param name="actualResults">List of actual lottery results</param>
    /// <returns>K1N and K2N rates</returns>
    Task<(double K1nRate, double K2nRate)> CalculateRatesAsync(
        string bridgeName, 
        List<string[]> predictions, 
        List<string[]> actualResults);
}

/// <summary>
/// Result of a backtest operation
/// </summary>
public class BacktestResult
{
    public string BridgeName { get; set; } = string.Empty;
    public int TotalTests { get; set; }
    public int Wins { get; set; }
    public int Losses { get; set; }
    public double WinRate { get; set; }
    public double K1nRateLo { get; set; }
    public double K1nRateDe { get; set; }
    public double K2nRateLo { get; set; }
    public double K2nRateDe { get; set; }
    public int CurrentStreak { get; set; }
    public int MaxWinStreak { get; set; }
    public int MaxLoseStreak { get; set; }
    public List<string> TestDetails { get; set; } = new();
}
