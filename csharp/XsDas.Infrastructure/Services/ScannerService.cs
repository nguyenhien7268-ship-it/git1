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
