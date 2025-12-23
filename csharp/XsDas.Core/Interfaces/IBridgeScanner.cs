using System.Collections.Generic;
using System.Threading.Tasks;
using XsDas.Core.Models;

namespace XsDas.Core.Interfaces;

/// <summary>
/// Interface for bridge scanning services
/// Ported from: logic/bridges/lo_bridge_scanner.py and de_bridge_scanner.py
/// </summary>
public interface IBridgeScanner
{
    /// <summary>
    /// Scan for bridge candidates without writing to database
    /// Returns candidates with K1N/K2N rates attached
    /// </summary>
    Task<ScanResult> ScanBridgesAsync(IEnumerable<LotteryResult> lotteryData);
}

/// <summary>
/// Result of a bridge scan operation
/// Ported from: logic/models.py scan metadata
/// </summary>
public class ScanResult
{
    public List<BridgeCandidate> Candidates { get; set; } = new();
    public int FoundTotal { get; set; }
    public int ExcludedExisting { get; set; }
    public int ScanDepth { get; set; }
    public Dictionary<string, object> Metadata { get; set; } = new();
}
