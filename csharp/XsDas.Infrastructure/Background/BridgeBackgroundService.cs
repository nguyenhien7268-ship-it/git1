using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using XsDas.Core.Interfaces;
using XsDas.Core.Utils;

namespace XsDas.Infrastructure.Background;

/// <summary>
/// Background service for automatic bridge management (auto-pruning)
/// Ported from: logic/bridges/bridge_manager_core.py::auto_manage_bridges
/// Implements IHostedService for background execution
/// </summary>
public class BridgeBackgroundService : BackgroundService
{
    private readonly ILogger<BridgeBackgroundService> _logger;
    private readonly IBridgeRepository _bridgeRepository;
    private readonly ILotteryResultRepository _resultRepository;
    private readonly IAnalysisService _analysisService;
    private readonly TimeSpan _checkInterval = TimeSpan.FromHours(6); // Check every 6 hours
    
    public BridgeBackgroundService(
        ILogger<BridgeBackgroundService> logger,
        IBridgeRepository bridgeRepository,
        ILotteryResultRepository resultRepository,
        IAnalysisService analysisService)
    {
        _logger = logger;
        _bridgeRepository = bridgeRepository;
        _resultRepository = resultRepository;
        _analysisService = analysisService;
    }
    
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Bridge Background Service starting...");
        
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await PerformAutoManagementAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in Bridge Background Service");
            }
            
            await Task.Delay(_checkInterval, stoppingToken);
        }
        
        _logger.LogInformation("Bridge Background Service stopping...");
    }
    
    /// <summary>
    /// Perform automatic bridge management
    /// Disables low-performing bridges based on threshold
    /// </summary>
    private async Task PerformAutoManagementAsync()
    {
        _logger.LogInformation("Starting automatic bridge management...");
        
        try
        {
            // Get all enabled bridges
            var enabledBridges = await _bridgeRepository.GetEnabledBridgesAsync();
            var bridgesList = enabledBridges.ToList();
            
            if (!bridgesList.Any())
            {
                _logger.LogInformation("No enabled bridges to manage");
                return;
            }
            
            // Get recent lottery results
            var recentResults = await _resultRepository.GetRecentResultsAsync(Constants.DefaultScanDepth);
            var resultsList = recentResults.ToList();
            
            if (resultsList.Count < Constants.DefaultScanDepth)
            {
                _logger.LogWarning("Insufficient lottery results for analysis");
                return;
            }
            
            var disabledCount = 0;
            
            // Analyze each bridge
            foreach (var bridge in bridgesList)
            {
                var metrics = await _analysisService.CalculatePerformanceMetricsAsync(
                    bridge, 
                    resultsList);
                
                // Update bridge metrics
                bridge.Streak = metrics.Streak;
                bridge.WinCount10 = metrics.Wins10;
                
                var primaryRate = bridge.GetPrimaryRate("k1n");
                
                // Disable if performance drops below threshold
                if (primaryRate < Constants.AutoPruneMinRate)
                {
                    _logger.LogInformation(
                        "Disabling bridge {BridgeName} - Rate: {Rate}% < Threshold: {Threshold}%",
                        bridge.Name, 
                        primaryRate, 
                        Constants.AutoPruneMinRate);
                    
                    bridge.IsEnabled = false;
                    await _bridgeRepository.UpdateAsync(bridge);
                    disabledCount++;
                }
            }
            
            _logger.LogInformation(
                "Auto-management completed. Disabled {DisabledCount} bridges out of {TotalCount}",
                disabledCount,
                bridgesList.Count);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during auto-management");
            throw;
        }
    }
    
    public override async Task StartAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Bridge Background Service is starting");
        await base.StartAsync(cancellationToken);
    }
    
    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Bridge Background Service is stopping");
        await base.StopAsync(cancellationToken);
    }
}
