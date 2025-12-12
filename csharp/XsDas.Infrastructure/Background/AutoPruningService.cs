using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using XsDas.Core.Interfaces;
using XsDas.Core.Models;

namespace XsDas.Infrastructure.Background;

/// <summary>
/// Background service for automatic pruning of weak/outdated bridges.
/// Implements IHostedService to run as a background task.
/// </summary>
public class AutoPruningService : BackgroundService
{
    private readonly ILogger<AutoPruningService> _logger;
    private readonly IRepository<ManagedBridge> _bridgeRepository;
    private readonly TimeSpan _pruningInterval;

    public AutoPruningService(
        ILogger<AutoPruningService> logger,
        IRepository<ManagedBridge> bridgeRepository)
    {
        _logger = logger;
        _bridgeRepository = bridgeRepository;
        _pruningInterval = TimeSpan.FromHours(24); // Run once per day
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Auto-Pruning Service started");

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await Task.Delay(_pruningInterval, stoppingToken);
                
                if (!stoppingToken.IsCancellationRequested)
                {
                    await PerformPruningAsync();
                }
            }
            catch (OperationCanceledException)
            {
                _logger.LogInformation("Auto-Pruning Service is stopping");
                break;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in Auto-Pruning Service");
                // Continue running despite errors
            }
        }

        _logger.LogInformation("Auto-Pruning Service stopped");
    }

    private async Task PerformPruningAsync()
    {
        _logger.LogInformation("Starting bridge pruning cycle");

        try
        {
            // Get all enabled bridges
            var bridges = await _bridgeRepository.FindAsync(b => b.IsEnabled);
            var bridgesList = bridges.ToList();

            // Validate data before pruning to prevent anomalies
            if (!bridgesList.Any())
            {
                _logger.LogWarning("No bridges found in database, skipping pruning cycle");
                return;
            }

            int disabledCount = 0;
            int deletedCount = 0;

            foreach (var bridge in bridgesList)
            {
                // Validate bridge data before processing
                if (!ValidateBridgeData(bridge))
                {
                    continue; // Skip invalid bridges
                }

                try
                {
                    // Pruning criteria:
                    // 1. Disable bridges with K1N rate < 70%
                    // 2. Delete bridges with K1N rate < 50% that have been disabled for > 7 days

                    var primaryRate = Math.Max(bridge.K1nRateLo, bridge.K1nRateDe);

                    if (primaryRate < 70 && bridge.IsEnabled)
                    {
                        bridge.IsEnabled = false;
                        await _bridgeRepository.UpdateAsync(bridge);
                        disabledCount++;
                        _logger.LogInformation(
                            "Disabled weak bridge: {Name} (Rate: {Rate}%)",
                            bridge.Name, primaryRate);
                    }
                    else if (primaryRate < 50 && !bridge.IsEnabled)
                    {
                        // Check if disabled for more than 7 days
                        if (DateTime.TryParse(bridge.DateAdded, out var addedDate))
                        {
                            var daysSinceAdded = (DateTime.Now - addedDate).TotalDays;
                            if (daysSinceAdded > 7)
                            {
                                await _bridgeRepository.DeleteAsync(bridge);
                                deletedCount++;
                                _logger.LogInformation(
                                    "Deleted very weak bridge: {Name} (Rate: {Rate}%)",
                                    bridge.Name, primaryRate);
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error processing bridge: {Name}", bridge.Name);
                    // Continue with other bridges even if one fails
                }
            }

            _logger.LogInformation(
                "Pruning cycle complete: {Disabled} disabled, {Deleted} deleted",
                disabledCount, deletedCount);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during bridge pruning");
        }
    }

    /// <summary>
    /// Validates bridge data to prevent anomalies
    /// </summary>
    private bool ValidateBridgeData(ManagedBridge bridge)
    {
        // Check if rates are within valid range (0-100)
        if (bridge.K1nRateLo < 0 || bridge.K1nRateLo > 100 ||
            bridge.K1nRateDe < 0 || bridge.K1nRateDe > 100)
        {
            _logger.LogWarning(
                "Invalid rate data for bridge {Name}: K1N Lo={K1nLo}, De={K1nDe}",
                bridge.Name, bridge.K1nRateLo, bridge.K1nRateDe);
            return false;
        }

        // Check if bridge has a valid name
        if (string.IsNullOrWhiteSpace(bridge.Name))
        {
            _logger.LogWarning("Bridge has no name, ID: {Id}", bridge.Id);
            return false;
        }

        return true;
    }

    public override async Task StopAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Auto-Pruning Service is stopping");
        await base.StopAsync(stoppingToken);
    }
}
