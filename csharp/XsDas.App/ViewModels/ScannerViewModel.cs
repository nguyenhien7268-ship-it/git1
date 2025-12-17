using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using XsDas.Core.Interfaces;
using XsDas.Core.Models;

namespace XsDas.App.ViewModels;

/// <summary>
/// ViewModel for bridge scanner
/// Ported from: ui/ui_bridge_scanner.py and ui/ui_de_bridge_scanner.py
/// </summary>
public partial class ScannerViewModel : ObservableObject
{
    private readonly IBridgeScanner _scanner;
    private readonly ILotteryResultRepository _resultRepository;
    private readonly IBridgeRepository _bridgeRepository;
    
    [ObservableProperty]
    private ObservableCollection<CandidateDisplayItem> _candidates = new();
    
    [ObservableProperty]
    private string _statusMessage = "Ready to scan";
    
    [ObservableProperty]
    private bool _isScanning;
    
    [ObservableProperty]
    private int _foundTotal;
    
    [ObservableProperty]
    private int _excludedCount;
    
    public ScannerViewModel(
        IBridgeScanner scanner,
        ILotteryResultRepository resultRepository,
        IBridgeRepository bridgeRepository)
    {
        _scanner = scanner;
        _resultRepository = resultRepository;
        _bridgeRepository = bridgeRepository;
    }
    
    [RelayCommand]
    private async Task ScanAsync()
    {
        try
        {
            IsScanning = true;
            StatusMessage = "Scanning for bridges...";
            Candidates.Clear();
            
            // Load lottery data
            var lotteryData = await _resultRepository.GetRecentResultsAsync(90);
            
            // Perform scan
            var result = await _scanner.ScanBridgesAsync(lotteryData);
            
            // Display results
            FoundTotal = result.FoundTotal;
            ExcludedCount = result.ExcludedExisting;
            
            foreach (var candidate in result.Candidates)
            {
                Candidates.Add(new CandidateDisplayItem(candidate));
            }
            
            StatusMessage = $"Found {result.Candidates.Count} new candidates " +
                          $"({result.ExcludedExisting} already exist)";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error: {ex.Message}";
        }
        finally
        {
            IsScanning = false;
        }
    }
    
    [RelayCommand]
    private async Task ImportSelectedAsync()
    {
        try
        {
            var selectedCandidates = Candidates
                .Where(c => c.IsSelected)
                .Select(c => c.Candidate)
                .ToList();
            
            if (!selectedCandidates.Any())
            {
                StatusMessage = "No candidates selected";
                return;
            }
            
            // Convert candidates to bridges and import
            var bridges = selectedCandidates.Select(c => c.ToBridge()).ToList();
            var importedCount = await _bridgeRepository.BulkAddAsync(bridges);
            
            StatusMessage = $"Imported {importedCount} bridges successfully";
            
            // Remove imported candidates from list
            foreach (var item in Candidates.Where(c => c.IsSelected).ToList())
            {
                Candidates.Remove(item);
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"Import error: {ex.Message}";
        }
    }
}

/// <summary>
/// Display item for bridge candidate
/// </summary>
public partial class CandidateDisplayItem : ObservableObject
{
    public BridgeCandidate Candidate { get; }
    
    [ObservableProperty]
    private bool _isSelected;
    
    public string Name => Candidate.Name;
    public string Description => Candidate.Description;
    public string Type => Candidate.Type.ToUpper();
    public int Streak => Candidate.Streak;
    public double Rate => Candidate.GetPrimaryRate("k1n");
    public string Stl => Candidate.Stl;
    
    public CandidateDisplayItem(BridgeCandidate candidate)
    {
        Candidate = candidate;
    }
}
