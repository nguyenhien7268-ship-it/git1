using System.Collections.ObjectModel;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using XsDas.Core.Interfaces;
using XsDas.Core.Models;

namespace XsDas.App.ViewModels;

/// <summary>
/// ViewModel for the main dashboard
/// Ported from: ui/ui_dashboard.py and ui/ui_de_dashboard.py
/// Uses CommunityToolkit.Mvvm for MVVM pattern implementation
/// </summary>
public partial class DashboardViewModel : ObservableObject
{
    private readonly IBridgeRepository _bridgeRepository;
    private readonly ILotteryResultRepository _resultRepository;
    private readonly IAnalysisService _analysisService;
    
    [ObservableProperty]
    private ObservableCollection<BridgeDisplayItem> _bridges = new();
    
    [ObservableProperty]
    private ObservableCollection<NumberScoreItem> _numberScores = new();
    
    [ObservableProperty]
    private string _statusMessage = "Ready";
    
    [ObservableProperty]
    private bool _isLoading;
    
    public DashboardViewModel(
        IBridgeRepository bridgeRepository,
        ILotteryResultRepository resultRepository,
        IAnalysisService analysisService)
    {
        _bridgeRepository = bridgeRepository;
        _resultRepository = resultRepository;
        _analysisService = analysisService;
    }
    
    [RelayCommand]
    private async Task LoadDataAsync()
    {
        try
        {
            IsLoading = true;
            StatusMessage = "Loading data...";
            
            // Load enabled bridges
            var bridges = await _bridgeRepository.GetEnabledBridgesAsync();
            Bridges = new ObservableCollection<BridgeDisplayItem>(
                bridges.Select(b => new BridgeDisplayItem(b)));
            
            // Load recent results
            var results = await _resultRepository.GetRecentResultsAsync(30);
            
            // Calculate number scores
            var config = new AnalysisConfig();
            var scores = await _analysisService.CalculateNumberScoresAsync(results, config);
            
            NumberScores = new ObservableCollection<NumberScoreItem>(
                scores.Select(kvp => new NumberScoreItem 
                { 
                    Number = kvp.Key, 
                    Score = kvp.Value 
                })
                .OrderByDescending(item => item.Score));
            
            StatusMessage = $"Loaded {Bridges.Count} bridges and {NumberScores.Count} scores";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }
    
    [RelayCommand]
    private async Task RefreshAsync()
    {
        await LoadDataAsync();
    }
}

/// <summary>
/// Display item for bridge in UI
/// </summary>
public class BridgeDisplayItem
{
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string Stl { get; set; } = string.Empty;
    public int Streak { get; set; }
    public double WinRate { get; set; }
    public bool IsEnabled { get; set; }
    
    public BridgeDisplayItem() { }
    
    public BridgeDisplayItem(Bridge bridge)
    {
        Name = bridge.Name;
        Description = bridge.Description;
        Type = bridge.Type;
        Stl = bridge.Stl;
        Streak = bridge.Streak;
        WinRate = bridge.GetPrimaryRate("k1n");
        IsEnabled = bridge.IsEnabled;
    }
}

/// <summary>
/// Display item for number score
/// </summary>
public class NumberScoreItem
{
    public string Number { get; set; } = string.Empty;
    public double Score { get; set; }
    public bool IsHot => Score >= 5.0;
}
