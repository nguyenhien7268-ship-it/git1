namespace XsDas.Core.Utils;

/// <summary>
/// Application-wide constants and default settings
/// Ported from: logic/constants.py and logic/config_manager.py::DEFAULT_SETTINGS
/// </summary>
public static class Constants
{
    // Analysis window sizes
    public const int DefaultStatsWindow = 7;
    public const int DefaultScanDepth = 30;
    public const int MemoryBridgeScanDepth = 90;
    
    // Performance thresholds
    public const double HighWinThreshold = 47.0;
    public const double AutoAddMinRate = 50.0;
    public const double AutoPruneMinRate = 40.0;
    
    // Confidence and filtering
    public const int FilterConfidenceThreshold = 5; // stars
    public const double FilterAiProbThreshold = 60.0; // percent
    
    // Bridge streak requirements
    public const int MinStreakLo = 3;
    public const int MinStreakBo = 1;
    public const int MinKillerStreak = 12;
    
    // Validation parameters
    public const int HistoryCheckLength = 10;
    public const int MinWinsRequired = 4;
    public const int ValidationLength = 15;
    public const int MinValidationWins = 2;
    
    // Rescue thresholds
    public const int RescueWins10 = 7;
    public const int MinWinsBo10 = 2;
    
    // Scoring weights (DE analysis)
    public const int BoUuTien1Score = 50;
    public const int BoUuTien2Score = 40;
    public const int ChamTiLeScore = 20;
    public const int ChamThongScore = 15;
    
    // Multipliers
    public const double DeKillerMultiplier = 3.0;
    public const double DeSetMultiplier = 2.0;
    public const double DeNormalMultiplier = 1.0;
    public const double DeMarketChamBonus = 2.0;
    public const double DeMarketBoBonus = 1.0;
    
    // Recent appearance bonuses (V7.6)
    public const double RecentBonus3Periods = 2.0;
    public const double RecentBonus7Periods = 1.0;
    public const double VoteWeight = 0.3;
    
    // Set (Bo) scoring bonuses (V10.3)
    public const double KepBonus = 2.0;
    public const double RecentSetBonus = 1.5;
    public const double TrendingBonus = 1.0;
    
    // Bridge types
    public const string BridgeTypeLo = "LO";
    public const string BridgeTypeDe = "DE";
    
    // Bridge kinds
    public const string BridgeKindSingle = "single";
    public const string BridgeKindSet = "set";
}

/// <summary>
/// Default application settings
/// </summary>
public class DefaultSettings
{
    public int StatsWindow { get; set; } = Constants.DefaultStatsWindow;
    public double HighWinThreshold { get; set; } = Constants.HighWinThreshold;
    public double AutoAddMinRate { get; set; } = Constants.AutoAddMinRate;
    public double AutoPruneMinRate { get; set; } = Constants.AutoPruneMinRate;
    public int FilterConfidenceThreshold { get; set; } = Constants.FilterConfidenceThreshold;
    public double FilterAiProbThreshold { get; set; } = Constants.FilterAiProbThreshold;
    public bool FilterEnabled { get; set; } = false;
    public int ChamThongMinConsecutive { get; set; } = 8;
}
