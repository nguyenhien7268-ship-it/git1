using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using XsDas.Core.Interfaces;

namespace XsDas.Infrastructure.Background;

/// <summary>
/// Background service for periodic backtesting of bridges.
/// Runs backtests and updates bridge performance metrics.
/// </summary>
public class BacktestingBackgroundService : BackgroundService
{
    private readonly ILogger<BacktestingBackgroundService> _logger;
    private readonly IBacktestingService _backtestingService;
    private readonly TimeSpan _backtestInterval;

    public BacktestingBackgroundService(
        ILogger<BacktestingBackgroundService> logger,
        IBacktestingService backtestingService)
    {
        _logger = logger;
        _backtestingService = backtestingService;
        _backtestInterval = TimeSpan.FromHours(48); // Run every 2 days
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Backtesting Background Service started");

        // Initial delay before first run (1 minute)
        await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await PerformBacktestingAsync();
                
                // Wait for next cycle
                await Task.Delay(_backtestInterval, stoppingToken);
            }
            catch (OperationCanceledException)
            {
                _logger.LogInformation("Backtesting Background Service is stopping");
                break;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in Backtesting Background Service");
                // Continue running despite errors
                await Task.Delay(TimeSpan.FromMinutes(10), stoppingToken);
            }
        }

        _logger.LogInformation("Backtesting Background Service stopped");
    }

    private async Task PerformBacktestingAsync()
    {
        _logger.LogInformation("Starting backtest cycle");

        try
        {
            // Backtest all bridges with minimum 60% win rate threshold
            var results = await _backtestingService.BacktestAllBridgesAsync(minWinRate: 60);

            _logger.LogInformation(
                "Backtest cycle complete: {Count} bridges with ≥60% win rate",
                results.Count);

            // Log top performers
            foreach (var result in results.Take(5))
            {
                _logger.LogInformation(
                    "Bridge: {Name} | Win Rate: {WinRate:F2}% | Tests: {Total} | Streak: {Streak}",
                    result.BridgeName,
                    result.WinRate,
                    result.TotalTests,
                    result.MaxWinStreak);
            }

            // Log poor performers
            var poorPerformers = results.Where(r => r.WinRate < 70).ToList();
            if (poorPerformers.Any())
            {
                _logger.LogWarning(
                    "Found {Count} bridges with win rate < 70%, may need review",
                    poorPerformers.Count);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during backtesting cycle");
        }
    }

    public override async Task StopAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Backtesting Background Service is stopping");
        await base.StopAsync(stoppingToken);
    }
}
