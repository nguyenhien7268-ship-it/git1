using XsDas.Core.Models;
using XsDas.Core.Utils;
using XsDas.Infrastructure.Data;

namespace XsDas.Infrastructure.Services;

/// <summary>
/// Scanner service for detecting lottery bridge patterns
/// Ported from Python logic/bridges/bridges_classic.py and lo_bridge_scanner.py
/// </summary>
public class ScannerService
{
    private readonly LotteryDbContext _context;

    public ScannerService(LotteryDbContext context)
    {
        _context = context;
    }

    /// <summary>
    /// Scan for Cau 1 - STL P5 V30 pattern
    /// Uses GDB (Giải Đặc Biệt) last 2 digits, adds 5 to each, applies shadow
    /// </summary>
    public List<string> ScanCau1StlP5(LotteryResult result)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(result.Gdb))
                return new List<string> { "00", "55" };

            var gdb = result.Gdb.Trim();
            if (gdb.Length < 2)
                return new List<string> { "00", "55" };

            var de = gdb.Substring(gdb.Length - 2);
            var a = int.Parse(de[0].ToString());
            var b = int.Parse(de[1].ToString());

            var x = (a + 5) % 10;
            var y = (b + 5) % 10;

            return LotteryUtils.CreateStlBongPair(x.ToString()[0], y.ToString()[0]);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 2 - VT1 V30 pattern
    /// Uses G6[2] and G7[3] positions
    /// </summary>
    public List<string> ScanCau2Vt1(LotteryResult result)
    {
        try
        {
            var g6Parts = result.G6?.Split(',') ?? Array.Empty<string>();
            var g7Parts = result.G7?.Split(',') ?? Array.Empty<string>();

            var a = g6Parts.Length > 2 
                ? g6Parts[2].Trim().Substring(g6Parts[2].Trim().Length - 1) 
                : "0";
            var b = g7Parts.Length > 3 
                ? g7Parts[3].Trim().Substring(g7Parts[3].Trim().Length - 1) 
                : "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 3 - VT2 V30 pattern
    /// Uses last digit of GDB and G1
    /// </summary>
    public List<string> ScanCau3Vt2(LotteryResult result)
    {
        try
        {
            var a = result.Gdb?.Trim().Substring(result.Gdb.Trim().Length - 1) ?? "0";
            var b = result.G1?.Trim().Substring(result.G1.Trim().Length - 1) ?? "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 4 - G2_1 + G3_1 pattern
    /// Uses first prize from G2 and G3
    /// </summary>
    public List<string> ScanCau4G2G3(LotteryResult result)
    {
        try
        {
            var g2Parts = result.G2?.Split(',') ?? Array.Empty<string>();
            var g3Parts = result.G3?.Split(',') ?? Array.Empty<string>();

            var a = g2Parts.Length > 0 
                ? g2Parts[0].Trim().Substring(g2Parts[0].Trim().Length - 1) 
                : "0";
            var b = g3Parts.Length > 0 
                ? g3Parts[0].Trim().Substring(g3Parts[0].Trim().Length - 1) 
                : "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 5 - TDB1 pattern
    /// Uses G7[0] first char and G7[3] last char
    /// </summary>
    public List<string> ScanCau5Tdb1(LotteryResult result)
    {
        try
        {
            var g7Parts = result.G7?.Split(',') ?? Array.Empty<string>();
            var a = g7Parts.Length > 0 
                ? g7Parts[0].Trim().Substring(0, 1) 
                : "0";
            var b = g7Parts.Length > 3 
                ? g7Parts[3].Trim().Substring(g7Parts[3].Trim().Length - 1) 
                : "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 6 - VT5 pattern
    /// Uses G7[1] last char and G7[2] first char
    /// </summary>
    public List<string> ScanCau6Vt5(LotteryResult result)
    {
        try
        {
            var g7Parts = result.G7?.Split(',') ?? Array.Empty<string>();
            var a = g7Parts.Length > 1 
                ? g7Parts[1].Trim().Substring(g7Parts[1].Trim().Length - 1) 
                : "0";
            var b = g7Parts.Length > 2 
                ? g7Parts[2].Trim().Substring(0, 1) 
                : "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 7 - Moi1 pattern
    /// Uses G5[0] first char and G7[0] first char
    /// </summary>
    public List<string> ScanCau7Moi1(LotteryResult result)
    {
        try
        {
            var g5Parts = result.G5?.Split(',') ?? Array.Empty<string>();
            var g7Parts = result.G7?.Split(',') ?? Array.Empty<string>();
            
            var a = g5Parts.Length > 0 
                ? g5Parts[0].Trim().Substring(0, 1) 
                : "0";
            var b = g7Parts.Length > 0 
                ? g7Parts[0].Trim().Substring(0, 1) 
                : "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 8 - Moi2 pattern
    /// Uses G3[0] first char and G4[0] first char
    /// </summary>
    public List<string> ScanCau8Moi2(LotteryResult result)
    {
        try
        {
            var g3Parts = result.G3?.Split(',') ?? Array.Empty<string>();
            var g4Parts = result.G4?.Split(',') ?? Array.Empty<string>();
            
            var a = g3Parts.Length > 0 
                ? g3Parts[0].Trim().Substring(0, 1) 
                : "0";
            var b = g4Parts.Length > 0 
                ? g4Parts[0].Trim().Substring(0, 1) 
                : "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 9 - Moi3 pattern
    /// Uses GDB first char and G1 first char
    /// </summary>
    public List<string> ScanCau9Moi3(LotteryResult result)
    {
        try
        {
            var a = result.Gdb?.Trim().Substring(0, 1) ?? "0";
            var b = result.G1?.Trim().Substring(0, 1) ?? "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 10 - Moi4 pattern
    /// Uses G2[1] position 1 and G3[2] last char
    /// </summary>
    public List<string> ScanCau10Moi4(LotteryResult result)
    {
        try
        {
            var g2Parts = result.G2?.Split(',') ?? Array.Empty<string>();
            var g3Parts = result.G3?.Split(',') ?? Array.Empty<string>();
            
            var a = g2Parts.Length > 1 && g2Parts[1].Trim().Length > 1
                ? g2Parts[1].Trim().Substring(1, 1) 
                : "0";
            var b = g3Parts.Length > 2 
                ? g3Parts[2].Trim().Substring(g3Parts[2].Trim().Length - 1) 
                : "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 11 - Moi5 pattern
    /// Uses GDB position 1 and G3[1] last char
    /// </summary>
    public List<string> ScanCau11Moi5(LotteryResult result)
    {
        try
        {
            var gdb = result.Gdb?.Trim() ?? "00";
            var g3Parts = result.G3?.Split(',') ?? Array.Empty<string>();
            
            var a = gdb.Length > 1 ? gdb.Substring(1, 1) : "0";
            var b = g3Parts.Length > 1 
                ? g3Parts[1].Trim().Substring(g3Parts[1].Trim().Length - 1) 
                : "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 12 - Moi6 pattern
    /// Uses GDB last char and G3[2] position 2
    /// </summary>
    public List<string> ScanCau12Moi6(LotteryResult result)
    {
        try
        {
            var gdb = result.Gdb?.Trim() ?? "00000";
            var g3Parts = result.G3?.Split(',') ?? Array.Empty<string>();
            
            var a = gdb.Substring(gdb.Length - 1);
            var b = g3Parts.Length > 2 && g3Parts[2].Trim().Length > 2
                ? g3Parts[2].Trim().Substring(2, 1) 
                : "0";

            return LotteryUtils.CreateStlBongPair(a, b);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 13 - G7_3_P8 pattern
    /// Uses G7[2] last 2 digits, adds 8 to each
    /// </summary>
    public List<string> ScanCau13G7P8(LotteryResult result)
    {
        try
        {
            var g7Parts = result.G7?.Split(',') ?? Array.Empty<string>();
            var baseNum = g7Parts.Length > 2 
                ? g7Parts[2].Trim().PadLeft(2, '0').Substring(g7Parts[2].Trim().Length >= 2 ? g7Parts[2].Trim().Length - 2 : 0, 2)
                : "00";

            var a = int.Parse(baseNum[0].ToString());
            var b = int.Parse(baseNum[1].ToString());
            var x = (a + 8) % 10;
            var y = (b + 8) % 10;

            return LotteryUtils.CreateStlBongPair(x.ToString()[0], y.ToString()[0]);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 14 - G1_P2 pattern
    /// Uses G1 last 2 digits, adds 2 to each
    /// </summary>
    public List<string> ScanCau14G1P2(LotteryResult result)
    {
        try
        {
            var g1 = result.G1?.Trim() ?? "00";
            var baseNum = g1.Substring(g1.Length >= 2 ? g1.Length - 2 : 0).PadLeft(2, '0');

            var a = int.Parse(baseNum[0].ToString());
            var b = int.Parse(baseNum[1].ToString());
            var x = (a + 2) % 10;
            var y = (b + 2) % 10;

            return LotteryUtils.CreateStlBongPair(x.ToString()[0], y.ToString()[0]);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Scan for Cau 15 - DE_P7 pattern
    /// Uses GDB last 2 digits, adds 7 to each
    /// </summary>
    public List<string> ScanCau15DeP7(LotteryResult result)
    {
        try
        {
            var gdb = result.Gdb?.Trim() ?? "00000";
            var baseNum = gdb.Substring(gdb.Length >= 2 ? gdb.Length - 2 : 0).PadLeft(2, '0');

            var a = int.Parse(baseNum[0].ToString());
            var b = int.Parse(baseNum[1].ToString());
            var x = (a + 7) % 10;
            var y = (b + 7) % 10;

            return LotteryUtils.CreateStlBongPair(x.ToString()[0], y.ToString()[0]);
        }
        catch
        {
            return new List<string> { "00", "55" };
        }
    }

    /// <summary>
    /// Get all 15 bridge scanning functions
    /// </summary>
    public List<Func<LotteryResult, List<string>>> GetAllBridgeScanners()
    {
        return new List<Func<LotteryResult, List<string>>>
        {
            ScanCau1StlP5,
            ScanCau2Vt1,
            ScanCau3Vt2,
            ScanCau4G2G3,
            ScanCau5Tdb1,
            ScanCau6Vt5,
            ScanCau7Moi1,
            ScanCau8Moi2,
            ScanCau9Moi3,
            ScanCau10Moi4,
            ScanCau11Moi5,
            ScanCau12Moi6,
            ScanCau13G7P8,
            ScanCau14G1P2,
            ScanCau15DeP7
        };
    }

    /// <summary>
    /// Backtest a bridge pattern against historical results
    /// Returns win rate and other statistics
    /// </summary>
    public async Task<BacktestResult> BacktestBridge(
        Func<LotteryResult, List<string>> scanFunction,
        int lookbackPeriods = 30)
    {
        var results = _context.LotteryResults
            .OrderByDescending(r => r.Id)
            .Take(lookbackPeriods + 1)
            .ToList();

        if (results.Count < 2)
            return new BacktestResult { WinRate = 0, TotalPeriods = 0 };

        int wins = 0;
        int total = 0;
        int currentStreak = 0;

        for (int i = 0; i < results.Count - 1; i++)
        {
            var currentResult = results[i];
            var nextResult = results[i + 1];

            var prediction = scanFunction(currentResult);
            var nextLotos = nextResult.GetAllLotos();
            var lotoSet = new HashSet<string>(nextLotos);

            var hit = prediction.Any(p => lotoSet.Contains(p));
            
            if (hit)
            {
                wins++;
                currentStreak++;
            }
            else
            {
                currentStreak = 0;
            }

            total++;
        }

        return new BacktestResult
        {
            WinRate = total > 0 ? (double)wins / total * 100 : 0,
            TotalPeriods = total,
            Wins = wins,
            CurrentStreak = currentStreak
        };
    }
}

/// <summary>
/// Result of a backtest operation
/// </summary>
public class BacktestResult
{
    public double WinRate { get; set; }
    public int TotalPeriods { get; set; }
    public int Wins { get; set; }
    public int CurrentStreak { get; set; }
}
