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
            ScanFixedBridge01,  // GĐB+5
            ScanFixedBridge02,  // G6.2+G7.3
            ScanFixedBridge03,  // Đuôi GĐB+G1
            ScanFixedBridge04,  // GĐB Sát Đuôi
            ScanFixedBridge05,  // Đầu G7.0+Đuôi G7.3
            ScanFixedBridge06,  // G7.1+G7.2
            ScanFixedBridge07,  // Moi1
            ScanFixedBridge08,  // Moi2
            ScanFixedBridge09,  // Moi3
            ScanFixedBridge10,  // Moi4
            ScanFixedBridge11,  // Moi5
            ScanFixedBridge12,  // Moi6
            ScanFixedBridge13,  // G7_3_P8
            ScanFixedBridge14,  // G1_P2
            ScanFixedBridge15,  // DE_P7
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
    /// Ported from: logic/bridges/bridges_classic.py::getCau2_VT1_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge02(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var g6Parts = result.Giai6?.Split(',') ?? Array.Empty<string>();
            var g7Parts = result.Giai7?.Split(',') ?? Array.Empty<string>();
            
            var a = g6Parts.Length > 2 ? g6Parts[2].Trim().TakeLast(1).FirstOrDefault() : '0';
            var b = g7Parts.Length > 3 ? g7Parts[3].Trim().TakeLast(1).FirstOrDefault() : '0';
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_02",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_02"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 02 (G6.2+G7.3)",
                Description = "Cầu Lô 02 (G6.2+G7.3)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 03: Đuôi GĐB+G1
    /// Ported from: logic/bridges/bridges_classic.py::getCau3_VT2_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge03(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var a = result.GiaiDacBiet?.Trim().TakeLast(1).FirstOrDefault() ?? '0';
            var b = result.Giai1?.Trim().TakeLast(1).FirstOrDefault() ?? '0';
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_03",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_03"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 03 (Đuôi GĐB+G1)",
                Description = "Cầu Lô 03 (Đuôi GĐB+G1)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 04: GĐB Sát Đuôi
    /// Ported from: logic/bridges/bridges_classic.py::getCau4_VT3_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge04(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var gdb = result.GiaiDacBiet?.Trim() ?? "00000";
            var a = gdb.Length >= 2 ? gdb[^2] : '0'; // Second to last digit
            var b = result.Giai1?.Trim().TakeLast(1).FirstOrDefault() ?? '0';
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_04",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_04"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 04 (GĐB Sát Đuôi)",
                Description = "Cầu Lô 04 (GĐB Sát Đuôi)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 05: Đầu G7.0+Đuôi G7.3
    /// Ported from: logic/bridges/bridges_classic.py::getCau5_TDB1_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge05(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var g7Parts = result.Giai7?.Split(',') ?? Array.Empty<string>();
            var a = g7Parts.Length > 0 ? g7Parts[0].Trim().Take(1).FirstOrDefault() : '0'; // First digit of G7[0]
            var b = g7Parts.Length > 3 ? g7Parts[3].Trim().TakeLast(1).FirstOrDefault() : '0'; // Last digit of G7[3]
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_05",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_05"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 05 (Đầu G7.0+Đuôi G7.3)",
                Description = "Cầu Lô 05 (Đầu G7.0+Đuôi G7.3)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 06: G7.1+G7.2
    /// Ported from: logic/bridges/bridges_classic.py::getCau6_VT5_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge06(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var g7Parts = result.Giai7?.Split(',') ?? Array.Empty<string>();
            var a = g7Parts.Length > 1 ? g7Parts[1].Trim().TakeLast(1).FirstOrDefault() : '0'; // Last digit of G7[1]
            var b = g7Parts.Length > 2 ? g7Parts[2].Trim().Take(1).FirstOrDefault() : '0'; // First digit of G7[2]
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_06",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_06"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 06 (G7.1+G7.2)",
                Description = "Cầu Lô 06 (G7.1+G7.2)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 07: Moi1 (G5.0 head + G7.0 head)
    /// Ported from: logic/bridges/bridges_classic.py::getCau7_Moi1_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge07(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var g5Parts = result.Giai5?.Split(',') ?? Array.Empty<string>();
            var g7Parts = result.Giai7?.Split(',') ?? Array.Empty<string>();
            var a = g5Parts.Length > 0 ? g5Parts[0].Trim().Take(1).FirstOrDefault() : '0';
            var b = g7Parts.Length > 0 ? g7Parts[0].Trim().Take(1).FirstOrDefault() : '0';
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_07",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_07"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 07 (Moi1)",
                Description = "Cầu Lô 07 (Moi1)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 08: Moi2 (G3.0 head + G4.0 head)
    /// Ported from: logic/bridges/bridges_classic.py::getCau8_Moi2_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge08(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var g3Parts = result.Giai3?.Split(',') ?? Array.Empty<string>();
            var g4Parts = result.Giai4?.Split(',') ?? Array.Empty<string>();
            var a = g3Parts.Length > 0 ? g3Parts[0].Trim().Take(1).FirstOrDefault() : '0';
            var b = g4Parts.Length > 0 ? g4Parts[0].Trim().Take(1).FirstOrDefault() : '0';
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_08",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_08"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 08 (Moi2)",
                Description = "Cầu Lô 08 (Moi2)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 09: Moi3 (GĐB head + G1 head)
    /// Ported from: logic/bridges/bridges_classic.py::getCau9_Moi3_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge09(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var a = result.GiaiDacBiet?.Trim().Take(1).FirstOrDefault() ?? '0';
            var b = result.Giai1?.Trim().Take(1).FirstOrDefault() ?? '0';
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_09",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_09"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 09 (Moi3)",
                Description = "Cầu Lô 09 (Moi3)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 10: Moi4 (G2.1 middle + G3.2 tail)
    /// Ported from: logic/bridges/bridges_classic.py::getCau10_Moi4_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge10(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var g2Parts = result.Giai2?.Split(',') ?? Array.Empty<string>();
            var g3Parts = result.Giai3?.Split(',') ?? Array.Empty<string>();
            var g2Val = g2Parts.Length > 1 ? g2Parts[1].Trim() : "00";
            var g3Val = g3Parts.Length > 2 ? g3Parts[2].Trim() : "00000";
            
            var a = g2Val.Length >= 2 ? g2Val[1] : '0'; // Middle digit (index 1)
            var b = g3Val.TakeLast(1).FirstOrDefault(); // Last digit
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_10",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_10"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 10 (Moi4)",
                Description = "Cầu Lô 10 (Moi4)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 11: Moi5 (GĐB middle + G3.1 tail)
    /// Ported from: logic/bridges/bridges_classic.py::getCau11_Moi5_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge11(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var gdb = result.GiaiDacBiet?.Trim() ?? "00";
            var g3Parts = result.Giai3?.Split(',') ?? Array.Empty<string>();
            var g3Val = g3Parts.Length > 1 ? g3Parts[1].Trim() : "00000";
            
            var a = gdb.Length >= 2 ? gdb[1] : '0'; // Middle digit (index 1)
            var b = g3Val.TakeLast(1).FirstOrDefault(); // Last digit
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_11",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_11"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 11 (Moi5)",
                Description = "Cầu Lô 11 (Moi5)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 12: Moi6 (GĐB tail + G3.2 middle)
    /// Ported from: logic/bridges/bridges_classic.py::getCau12_Moi6_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge12(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var gdb = result.GiaiDacBiet?.Trim() ?? "00000";
            var g3Parts = result.Giai3?.Split(',') ?? Array.Empty<string>();
            var g3Val = g3Parts.Length > 2 ? g3Parts[2].Trim() : "000";
            
            var a = gdb.TakeLast(1).FirstOrDefault(); // Last digit
            var b = g3Val.Length >= 3 ? g3Val[2] : '0'; // Middle digit (index 2)
            
            var stlPair = LotteryUtils.CreateStlWithShadow(int.Parse(a.ToString()), int.Parse(b.ToString()));
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_12",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_12"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 12 (Moi6)",
                Description = "Cầu Lô 12 (Moi6)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 13: G7_3_P8 (G7.2 + 8)
    /// Ported from: logic/bridges/bridges_classic.py::getCau13_G7_3_P8_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge13(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var g7Parts = result.Giai7?.Split(',') ?? Array.Empty<string>();
            var baseNum = g7Parts.Length > 2 ? g7Parts[2].Trim().PadLeft(2, '0') : "00";
            
            if (baseNum.Length >= 2)
            {
                var a = (int.Parse(baseNum[0].ToString()) + 8) % 10;
                var b = (int.Parse(baseNum[1].ToString()) + 8) % 10;
                
                var stlPair = LotteryUtils.CreateStlWithShadow(a, b);
                stl = string.Join(",", stlPair);
                
                var lotos = new HashSet<string>(result.GetAllLotos());
                var hit = stlPair.Any(s => lotos.Contains(s));
                results.Add(hit);
            }
            else
            {
                results.Add(false);
            }
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_13",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_13"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 13 (G7_3_P8)",
                Description = "Cầu Lô 13 (G7.3+8)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 14: G1_P2 (G1 + 2)
    /// Ported from: logic/bridges/bridges_classic.py::getCau14_G1_P2_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge14(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var g1 = result.Giai1?.Trim() ?? "00";
            var baseNum = g1.Length >= 2 ? g1.Substring(g1.Length - 2).PadLeft(2, '0') : "00";
            
            var a = (int.Parse(baseNum[0].ToString()) + 2) % 10;
            var b = (int.Parse(baseNum[1].ToString()) + 2) % 10;
            
            var stlPair = LotteryUtils.CreateStlWithShadow(a, b);
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_14",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_14"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 14 (G1_P2)",
                Description = "Cầu Lô 14 (G1+2)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
    }
    
    /// <summary>
    /// Scan for Fixed Bridge 15: DE_P7 (GĐB + 7)
    /// Ported from: logic/bridges/bridges_classic.py::getCau15_DE_P7_V30_V5
    /// </summary>
    private List<BridgeCandidate> ScanFixedBridge15(List<LotteryResult> data, int depth)
    {
        var candidates = new List<BridgeCandidate>();
        var recentData = data.Take(depth).Reverse().ToList();
        var results = new List<bool>();
        var stl = "N/A";
        
        foreach (var result in recentData)
        {
            var gdb = result.GiaiDacBiet?.Trim() ?? "00000";
            var baseNum = gdb.Length >= 2 ? gdb.Substring(gdb.Length - 2).PadLeft(2, '0') : "00";
            
            var a = (int.Parse(baseNum[0].ToString()) + 7) % 10;
            var b = (int.Parse(baseNum[1].ToString()) + 7) % 10;
            
            var stlPair = LotteryUtils.CreateStlWithShadow(a, b);
            stl = string.Join(",", stlPair);
            
            var lotos = new HashSet<string>(result.GetAllLotos());
            var hit = stlPair.Any(s => lotos.Contains(s));
            results.Add(hit);
        }
        
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        if (metrics.Streak >= _minStreak)
        {
            candidates.Add(new BridgeCandidate
            {
                Name = "LO_STL_FIXED_15",
                NormalizedName = LotteryUtils.NormalizeBridgeName("LO_STL_FIXED_15"),
                Type = "lo",
                Kind = "single",
                Stl = stl,
                Reason = "Fixed Bridge 15 (DE_P7)",
                Description = "Cầu Lô 15 (GĐB+7)",
                Streak = metrics.Streak,
                WinCount10 = metrics.Wins10,
                K1nLo = metrics.WinRate,
                K2nLo = metrics.WinRate
            });
        }
        
        return candidates;
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
