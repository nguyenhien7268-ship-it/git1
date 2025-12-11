using System;
using System.Collections.Generic;
using System.Linq;

namespace XsDas.Core.Utils;

/// <summary>
/// Core utility functions for lottery calculations
/// Ported from: logic/utils.py
/// </summary>
public static class LotteryUtils
{
    /// <summary>
    /// Bong Duong V30 mapping (Shadow mapping)
    /// Ported from: logic/utils.py::BONG_DUONG_V30
    /// </summary>
    private static readonly Dictionary<char, char> BongDuongV30 = new()
    {
        {'0', '5'}, {'1', '6'}, {'2', '7'}, {'3', '8'}, {'4', '9'},
        {'5', '0'}, {'6', '1'}, {'7', '2'}, {'8', '3'}, {'9', '4'}
    };
    
    /// <summary>
    /// Get the shadow digit (Bong Duong) of a digit
    /// Ported from: logic/utils.py::getBongDuong_V30
    /// </summary>
    public static char GetBongDuong(char digit)
    {
        return BongDuongV30.TryGetValue(digit, out var shadow) ? shadow : digit;
    }
    
    /// <summary>
    /// Create STL (Soi Tránh Lô) pair with shadow logic
    /// Ported from: logic/utils.py::taoSTL_V30_Bong
    /// </summary>
    public static List<string> CreateStlWithShadow(int a, int b)
    {
        var strA = a.ToString();
        var strB = b.ToString();
        
        if (strA == strB)
        {
            // Same digits (kep) - return pair and shadow pair
            var kep = $"{strA}{strB}".PadLeft(2, '0');
            var bongDigit = GetBongDuong(strA[0]);
            var bongKep = $"{bongDigit}{bongDigit}";
            return new List<string> { kep, bongKep };
        }
        else
        {
            // Different digits - return both permutations
            var lo1 = $"{strA}{strB}".PadLeft(2, '0');
            var lo2 = $"{strB}{strA}".PadLeft(2, '0');
            return new List<string> { lo1, lo2 };
        }
    }
    
    /// <summary>
    /// Check if STL pair hits in a loto set
    /// Ported from: logic/utils.py::checkHitSet_V30_K2N
    /// </summary>
    public static string CheckHitSet(List<string> stlPair, HashSet<string> lotoSet)
    {
        try
        {
            var hit1 = lotoSet.Contains(stlPair[0]);
            var hit2 = lotoSet.Contains(stlPair[1]);
            
            if (hit1 && hit2)
                return "✅ (Ăn 2)";
            if (hit1 || hit2)
                return "✅ (Ăn 1)";
            return "❌";
        }
        catch
        {
            return "Lỗi check";
        }
    }
    
    /// <summary>
    /// Normalize bridge name for duplicate checking
    /// Ported from: logic/common_utils.py::normalize_bridge_name
    /// </summary>
    public static string NormalizeBridgeName(string name)
    {
        var normalized = name.ToLower()
            // Remove spaces and common separators
            .Replace(" ", "")
            .Replace("_", "")
            .Replace("-", "")
            .Replace("[", "")
            .Replace("]", "")
            .Replace("(", "")
            .Replace(")", "")
            .Replace("+", "")
            // Normalize Vietnamese characters
            .Replace("à", "a").Replace("á", "a").Replace("ả", "a").Replace("ã", "a").Replace("ạ", "a")
            .Replace("ă", "a").Replace("ằ", "a").Replace("ắ", "a").Replace("ẳ", "a").Replace("ẵ", "a").Replace("ặ", "a")
            .Replace("â", "a").Replace("ầ", "a").Replace("ấ", "a").Replace("ẩ", "a").Replace("ẫ", "a").Replace("ậ", "a")
            .Replace("đ", "d")
            .Replace("è", "e").Replace("é", "e").Replace("ẻ", "e").Replace("ẽ", "e").Replace("ẹ", "e")
            .Replace("ê", "e").Replace("ề", "e").Replace("ế", "e").Replace("ể", "e").Replace("ễ", "e").Replace("ệ", "e")
            .Replace("ì", "i").Replace("í", "i").Replace("ỉ", "i").Replace("ĩ", "i").Replace("ị", "i")
            .Replace("ò", "o").Replace("ó", "o").Replace("ỏ", "o").Replace("õ", "o").Replace("ọ", "o")
            .Replace("ô", "o").Replace("ồ", "o").Replace("ố", "o").Replace("ổ", "o").Replace("ỗ", "o").Replace("ộ", "o")
            .Replace("ơ", "o").Replace("ờ", "o").Replace("ớ", "o").Replace("ở", "o").Replace("ỡ", "o").Replace("ợ", "o")
            .Replace("ù", "u").Replace("ú", "u").Replace("ủ", "u").Replace("ũ", "u").Replace("ụ", "u")
            .Replace("ư", "u").Replace("ừ", "u").Replace("ứ", "u").Replace("ử", "u").Replace("ữ", "u").Replace("ự", "u")
            .Replace("ỳ", "y").Replace("ý", "y").Replace("ỷ", "y").Replace("ỹ", "y").Replace("ỵ", "y")
            .Trim();
        
        return normalized;
    }
    
    /// <summary>
    /// Calculate strict performance metrics from result list
    /// Ported from: logic/common_utils.py::calculate_strict_performance
    /// </summary>
    public static PerformanceMetrics CalculateStrictPerformance(List<bool> resultsRecentToPast)
    {
        var streak = 0;
        var totalWins = 0;
        var isBroken = false;
        var totalDays = resultsRecentToPast.Count;
        
        foreach (var isWin in resultsRecentToPast)
        {
            if (isWin)
            {
                totalWins++;
                if (!isBroken)
                    streak++;
            }
            else
            {
                isBroken = true;
            }
        }
        
        // Calculate wins in last 10 days
        var wins10 = resultsRecentToPast.Take(10).Count(x => x);
        var winRate = totalDays > 0 ? (totalWins / (double)totalDays * 100.0) : 0.0;
        
        return new PerformanceMetrics
        {
            Streak = streak,
            TotalWins = totalWins,
            WinRate = winRate,
            Wins10 = wins10,
            TotalDays = totalDays
        };
    }
}

/// <summary>
/// Performance metrics structure
/// </summary>
public class PerformanceMetrics
{
    public int Streak { get; set; }
    public int TotalWins { get; set; }
    public double WinRate { get; set; }
    public int Wins10 { get; set; }
    public int TotalDays { get; set; }
}
