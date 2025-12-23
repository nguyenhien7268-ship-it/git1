namespace XsDas.Infrastructure.Configuration;

/// <summary>
/// Configuration settings for background services.
/// Allows switching between production and testing intervals.
/// </summary>
public class BackgroundServiceConfig
{
    /// <summary>
    /// Interval for auto-pruning service cycles
    /// </summary>
    public TimeSpan AutoPruningInterval { get; set; } = TimeSpan.FromHours(24);

    /// <summary>
    /// Interval for backtesting service cycles
    /// </summary>
    public TimeSpan BacktestingInterval { get; set; } = TimeSpan.FromHours(48);

    /// <summary>
    /// Whether to use test mode with shorter intervals
    /// </summary>
    public bool TestMode { get; set; } = false;

    /// <summary>
    /// Gets the effective auto-pruning interval based on mode
    /// </summary>
    public TimeSpan GetAutoPruningInterval()
    {
        return TestMode ? TimeSpan.FromMinutes(5) : AutoPruningInterval;
    }

    /// <summary>
    /// Gets the effective backtesting interval based on mode
    /// </summary>
    public TimeSpan GetBacktestingInterval()
    {
        return TestMode ? TimeSpan.FromMinutes(10) : BacktestingInterval;
    }

    /// <summary>
    /// Production configuration (default)
    /// </summary>
    public static BackgroundServiceConfig Production => new()
    {
        AutoPruningInterval = TimeSpan.FromHours(24),
        BacktestingInterval = TimeSpan.FromHours(48),
        TestMode = false
    };

    /// <summary>
    /// Testing configuration (shorter intervals)
    /// </summary>
    public static BackgroundServiceConfig Testing => new()
    {
        AutoPruningInterval = TimeSpan.FromMinutes(5),
        BacktestingInterval = TimeSpan.FromMinutes(10),
        TestMode = true
    };

    /// <summary>
    /// Development configuration (moderate intervals)
    /// </summary>
    public static BackgroundServiceConfig Development => new()
    {
        AutoPruningInterval = TimeSpan.FromHours(1),
        BacktestingInterval = TimeSpan.FromHours(2),
        TestMode = false
    };
}
