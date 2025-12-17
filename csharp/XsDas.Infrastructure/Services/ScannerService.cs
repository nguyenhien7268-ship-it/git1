using System.Collections.Concurrent;
using XsDas.Core.Interfaces;
using XsDas.Core.Models;
using XsDas.Core.Utils;

namespace XsDas.Infrastructure.Services;

/// <summary>
/// Bridge scanner service with parallel processing
/// Ported from: logic/bridges/lo_bridge_scanner.py and de_bridge_scanner.py
/// Uses Parallel.ForEach for improved performance over Python's sequential processing
/// </summary>
public class ScannerService : IBridgeScanner
{
    private readonly IBridgeRepository _bridgeRepository;
    private readonly int _scanDepth = Constants.DefaultScanDepth;
    private readonly int _minStreak = Constants.MinStreakLo;
    
    public ScannerService(IBridgeRepository bridgeRepository)
    {
        _bridgeRepository = bridgeRepository;
    }
    
    /// <summary>
    /// Scan for bridge candidates without writing to database
    /// Returns candidates with K1N/K2N rates attached
    /// </summary>
    public async Task<ScanResult> ScanBridgesAsync(IEnumerable<LotteryResult> lotteryData)
    {
        var dataList = lotteryData.ToList();
        if (dataList.Count < _scanDepth)
        {
            return new ScanResult
            {
                Candidates = new List<BridgeCandidate>(),
                FoundTotal = 0,
                ExcludedExisting = 0,
                ScanDepth = dataList.Count,
                Metadata = new Dictionary<string, object>
                {
                    ["error"] = "Insufficient data for scanning"
                }
            };
        }
        
        // Get existing bridge names for duplicate detection
        var existingNames = (await _bridgeRepository.GetAllBridgeNamesAsync())
            .Select(LotteryUtils.NormalizeBridgeName)
            .ToHashSet();
        
        // Scan for different bridge types in parallel
        var candidates = new ConcurrentBag<BridgeCandidate>();
        
        // Parallel scan for fixed bridges
        await Task.Run(() =>
        {
            Parallel.ForEach(GetFixedBridgeScanners(), scanner =>
            {
                var foundCandidates = scanner(dataList, _scanDepth);
                foreach (var candidate in foundCandidates)
                {
                    candidates.Add(candidate);
                }
            });
        });
        
        // Scan for V17 shadow bridges (sequential for complex logic)
        var v17Candidates = ScanV17ShadowBridges(dataList);
        foreach (var candidate in v17Candidates)
        {
            candidates.Add(candidate);
        }
        
        // Filter out existing bridges
        var allCandidates = candidates.ToList();
        var filteredCandidates = allCandidates
            .Where(c => !existingNames.Contains(c.NormalizedName))
            .ToList();
        
        return new ScanResult
        {
            Candidates = filteredCandidates,
            FoundTotal = allCandidates.Count,
            ExcludedExisting = allCandidates.Count - filteredCandidates.Count,
            ScanDepth = _scanDepth,
            Metadata = new Dictionary<string, object>
            {
                ["scan_time"] = DateTime.Now,
                ["data_count"] = dataList.Count
            }
        };
    }
    
    /// <summary>
    /// Get list of fixed bridge scanner functions
    /// </summary>
    private List<Func<List<LotteryResult>, int, List<BridgeCandidate>>> GetFixedBridgeScanners()
    {
        return new List<Func<List<LotteryResult>, int, List<BridgeCandidate>>>
        {
            ScanFixedBridge01, // GĐB+5
            ScanFixedBridge02, // G6.2+G7.3
            ScanFixedBridge03, // Đuôi GĐB+G1
            // Add more fixed bridge scanners as needed
        };
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 01: GĐB+5
    /// Ported from: logic/bridges/bridges_classic.py::getCau1_STL_P5_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge01(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var gdb = result.GiaiDacBiet;
            if (string.IsNullOrEmpty(gdb) || gdb.Length < 2)
            {
                results.Add(false);
                continue;
            }
            
            // Get last 2 digits and add 5
            var last2 = gdb.Substring(gdb.Length - 2);
            if (!int.TryParse(last2, out var gdbNum))
            {
                results.Add(false);
                continue;
            }
            
            var predicted = (gdbNum + 5) % 100;
            stl = predicted.ToString("D2");
            
            // Check if prediction matches any loto in result
            var lotos = result.GetAllLotos();
            var hit = lotos.Contains(stl);
            results.Add(hit);
        }
        
        // Calculate performance
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_01",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_01"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 01 (GĐB+5)",
                Description = "Cầu Lô 01 (GĐB+5)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 02: G6.2+G7.3
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge02(List<LotteryResult> data, int depth)
    {
        // Implementation similar to ScanFixedBridge01
        // Ported from: logic/bridges/bridges_classic.py::getCau2_VT1_V30_V5
        return new List<BridgeCandidate>();
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 03: Đuôi GĐB+G1
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge03(List<LotteryResult> data, int depth)
    {
        // Implementation similar to ScanFixedBridge01
        // Ported from: logic/bridges/bridges_classic.py::getCau3_VT2_V30_V5
        return new List<BridgeCandidate>();
    }
    
    /// <summary>
    /// Scan for V17 Shadow bridges (Bóng Âm Dương)
    /// Ported from: logic/bridges/bridges_v16.py and update_fixed_lo_bridges
    /// </summary>
    private List<BridgeCandidate> ScanV17ShadowBridges(List<LotteryResult> data)
    {
        var candidates = new List<BridgeCandidate>();
        
        // V17 shadow bridge logic would be implemented here
        // This is complex logic involving position-based scanning
        // For now, returning empty list as placeholder
        
        return candidates;
    }
}
