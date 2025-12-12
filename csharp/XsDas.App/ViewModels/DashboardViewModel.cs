using System.Collections.ObjectModel;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using XsDas.Core.Interfaces;
using XsDas.Core.Models;

namespace XsDas.App.ViewModels;

/// <summary>
/// ViewModel for the main dashboard displaying lottery results and bridges
/// </summary>
public partial class DashboardViewModel : ObservableObject
{
    private readonly IRepository<LotteryResult> _resultsRepository;
    private readonly IRepository<ManagedBridge> _bridgesRepository;
    private readonly IScannerService _scannerService;
    private readonly IBacktestingService _backtestingService;

    [ObservableProperty]
    private ObservableCollection<LotteryResult> _lotteryResults = new();

    [ObservableProperty]
    private ObservableCollection<ManagedBridge> _bridges = new();

    [ObservableProperty]
    private LotteryResult? _selectedResult;

    [ObservableProperty]
    private ManagedBridge? _selectedBridge;

    [ObservableProperty]
    private string _statusMessage = "Ready";

    [ObservableProperty]
    private bool _isLoading;

    public DashboardViewModel(
        IRepository<LotteryResult> resultsRepository,
        IRepository<ManagedBridge> bridgesRepository,
        IScannerService scannerService,
        IBacktestingService backtestingService)
    {
        _resultsRepository = resultsRepository;
        _bridgesRepository = bridgesRepository;
        _scannerService = scannerService;
        _backtestingService = backtestingService;
    }

    [RelayCommand]
    private async Task LoadDataAsync()
    {
        try
        {
            IsLoading = true;
            StatusMessage = "Loading data...";

            // Load lottery results (last 100 results)
            var results = await _resultsRepository.GetAllAsync();
            LotteryResults = new ObservableCollection<LotteryResult>(
                results.OrderByDescending(r => r.Ky).Take(100));

            // Load bridges (only enabled ones)
            var bridges = await _bridgesRepository.FindAsync(b => b.IsEnabled);
            Bridges = new ObservableCollection<ManagedBridge>(
                bridges.OrderByDescending(b => b.K1nRateLo));

            StatusMessage = $"Loaded {LotteryResults.Count} results and {Bridges.Count} bridges";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error loading data: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    private async Task RefreshBridgesAsync()
    {
        try
        {
            IsLoading = true;
            StatusMessage = "Refreshing bridges...";

            var bridges = await _bridgesRepository.FindAsync(b => b.IsEnabled);
            Bridges = new ObservableCollection<ManagedBridge>(
                bridges.OrderByDescending(b => b.K1nRateLo));

            StatusMessage = $"Refreshed {Bridges.Count} bridges";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error refreshing: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    private async Task ScanNewBridgesAsync()
    {
        try
        {
            IsLoading = true;
            StatusMessage = "Scanning for new bridges...";

            // Get all scanner functions
            var scanners = _scannerService.GetAllBridgeScanners().ToList();
            StatusMessage = $"Found {scanners.Count} scanners";

            // This is a placeholder - in real implementation, you would:
            // 1. Get the latest result
            // 2. Run all scanners
            // 3. Compare predictions with next result
            // 4. Add successful bridges to database

            StatusMessage = "Scan complete";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error scanning: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    private async Task BacktestSelectedBridgeAsync()
    {
        if (SelectedBridge == null)
        {
            StatusMessage = "Please select a bridge to backtest";
            return;
        }

        try
        {
            IsLoading = true;
            StatusMessage = $"Backtesting {SelectedBridge.Name}...";

            var result = await _backtestingService.BacktestBridgeAsync(SelectedBridge.Name);

            StatusMessage = $"Backtest complete: {result.Wins}/{result.TotalTests} wins ({result.WinRate:F2}%)";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error backtesting: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    private void ViewBridgeDetails()
    {
        if (SelectedBridge == null)
        {
            StatusMessage = "Please select a bridge to view details";
            return;
        }

        StatusMessage = $"Viewing details for: {SelectedBridge.Name} " +
                       $"(K1N: {SelectedBridge.K1nRateLo:F2}% Lo, {SelectedBridge.K1nRateDe:F2}% De)";
    }
}
