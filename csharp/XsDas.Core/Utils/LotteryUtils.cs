using System.Text;
using System.Text.RegularExpressions;

namespace XsDas.Core.Utils;

/// <summary>
/// Core utility functions for lottery analytics.
/// Ported from Python logic/utils.py and logic/common_utils.py
/// </summary>
public static class LotteryUtils
{
    /// <summary>
    /// Shadow mapping dictionary (Bóng Dương V30)
    /// Maps each digit to its shadow counterpart
    /// </summary>
    private static readonly Dictionary<char, char> BongDuongV30 = new()
    {
        { '0', '5' }, { '1', '6' }, { '2', '7' }, { '3', '8' }, { '4', '9' },
        { '5', '0' }, { '6', '1' }, { '7', '2' }, { '8', '3' }, { '9', '4' }
    };

    /// <summary>
    /// Get shadow (bóng) of a digit using V30 mapping
    /// </summary>
    /// <param name="digit">Input digit character</param>
    /// <returns>Shadow digit character</returns>
    public static char GetBongDuong(char digit)
    {
        return BongDuongV30.TryGetValue(digit, out var shadow) ? shadow : digit;
    }

    /// <summary>
    /// Create STL (Soi Tránh Lô) pair with shadow mapping V30.
    /// Returns a pair of lottery numbers based on input digits.
    /// </summary>
    /// <param name="a">First digit</param>
    /// <param name="b">Second digit</param>
    /// <returns>Array of 2 lottery numbers (may include shadow pairs for duplicates)</returns>
    public static string[] TaoStlV30Bong(int a, int b)
    {
        var strA = a.ToString();
        var strB = b.ToString();

        if (strA == strB)
        {
            // For duplicate digits, return original and shadow pair
            var kep = $"{strA}{strB}".PadLeft(2, '0');
            var bongDigit = GetBongDuong(strA[0]);
            var bongKep = $"{bongDigit}{bongDigit}";
            return new[] { kep, bongKep };
        }
        else
        {
            // For different digits, return both permutations
            var lo1 = $"{strA}{strB}".PadLeft(2, '0');
            var lo2 = $"{strB}{strA}".PadLeft(2, '0');
            return new[] { lo1, lo2 };
        }
    }

    /// <summary>
    /// Extract all 27 lottery numbers from a DuLieu_AI row.
    /// Extracts last 2 digits from each prize column.
    /// </summary>
    /// <param name="row">Database row as array (MaSoKy, Col_A_Ky, GDB, G1-G7)</param>
    /// <returns>List of lottery numbers (2 digits each)</returns>
    public static List<string> GetAllLotoV30(object[] row)
    {
        var lotos = new List<string>();
        
        try
        {
            // row[0]=MaSoKy, row[1]=Col_A_Ky, row[2]=GDB
            if (row.Length > 2 && row[2] != null)
            {
                var gdb = row[2].ToString()?.Trim();
                if (!string.IsNullOrEmpty(gdb) && gdb.Length >= 2)
                {
                    lotos.Add(gdb[^2..].PadLeft(2, '0'));
                }
            }

            // row[3]=G1
            if (row.Length > 3 && row[3] != null)
            {
                var g1 = row[3].ToString()?.Trim();
                if (!string.IsNullOrEmpty(g1) && g1.Length >= 2)
                {
                    lotos.Add(g1[^2..].PadLeft(2, '0'));
                }
            }

            // G2-G7 (row[4] to row[9]) - may contain comma-separated values
            for (int i = 4; i < Math.Min(10, row.Length); i++)
            {
                if (row[i] == null) continue;
                
                var prizes = row[i].ToString()?.Split(',') ?? Array.Empty<string>();
                foreach (var prize in prizes)
                {
                    var trimmed = prize.Trim();
                    if (!string.IsNullOrEmpty(trimmed) && trimmed.Length >= 2)
                    {
                        lotos.Add(trimmed[^2..].PadLeft(2, '0'));
                    }
                }
            }
        }
        catch (Exception ex)
        {
            // Log error in production
            Console.WriteLine($"Error in GetAllLotoV30: {ex.Message}");
        }

        // Filter: only valid 2-digit numbers
        return lotos.Where(l => !string.IsNullOrEmpty(l) && 
                               l.Length == 2 && 
                               l.All(char.IsDigit))
                    .ToList();
    }

    /// <summary>
    /// Check if STL pair hits in the lottery number set (K2N version).
    /// Returns hit status with Vietnamese emoji indicators.
    /// </summary>
    /// <param name="stlPair">STL pair (array of 2 numbers)</param>
    /// <param name="lotoSet">Set of lottery numbers to check against</param>
    /// <returns>Hit status string: "✅ (Ăn 2)", "✅ (Ăn 1)", or "❌"</returns>
    public static string CheckHitSetV30K2N(string[] stlPair, HashSet<string> lotoSet)
    {
        try
        {
            if (stlPair.Length < 2)
                return "❌";

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
    /// Normalize Vietnamese text to ASCII (remove diacritics and special characters).
    /// Used for bridge name comparison and duplicate detection.
    /// </summary>
    /// <param name="text">Vietnamese text to normalize</param>
    /// <returns>Normalized ASCII text (lowercase, no special chars)</returns>
    public static string NormalizeVietnamese(string text)
    {
        if (string.IsNullOrEmpty(text))
            return string.Empty;

        // Vietnamese character mappings
        var replacements = new Dictionary<string, string>
        {
            // Lowercase vowels with diacritics
            { "à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ", "a" },
            { "è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ", "e" },
            { "ì|í|ị|ỉ|ĩ", "i" },
            { "ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ", "o" },
            { "ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ", "u" },
            { "ỳ|ý|ỵ|ỷ|ỹ", "y" },
            { "đ", "d" },
            // Uppercase vowels with diacritics
            { "À|Á|Ạ|Ả|Ã|Â|Ầ|Ấ|Ậ|Ẩ|Ẫ|Ă|Ằ|Ắ|Ặ|Ẳ|Ẵ", "A" },
            { "È|É|Ẹ|Ẻ|Ẽ|Ê|Ề|Ế|Ệ|Ể|Ễ", "E" },
            { "Ì|Í|Ị|Ỉ|Ĩ", "I" },
            { "Ò|Ó|Ọ|Ỏ|Õ|Ô|Ồ|Ố|Ộ|Ổ|Ỗ|Ơ|Ờ|Ớ|Ợ|Ở|Ỡ", "O" },
            { "Ù|Ú|Ụ|Ủ|Ũ|Ư|Ừ|Ứ|Ự|Ử|Ữ", "U" },
            { "Ỳ|Ý|Ỵ|Ỷ|Ỹ", "Y" },
            { "Đ", "D" }
        };

        var normalized = text;
        foreach (var (pattern, replacement) in replacements)
        {
            normalized = Regex.Replace(normalized, pattern, replacement);
        }

        // Convert to lowercase and remove non-alphanumeric characters
        normalized = normalized.ToLowerInvariant();
        normalized = Regex.Replace(normalized, @"[^a-z0-9]", "");

        return normalized;
    }

    /// <summary>
    /// Format win rate as percentage string.
    /// </summary>
    /// <param name="rate">Win rate (0-100)</param>
    /// <returns>Formatted percentage (e.g., "85.5%")</returns>
    public static string FormatWinRate(double rate)
    {
        if (rate < 0 || rate > 100)
            return "N/A";
        
        return $"{rate:F1}%";
    }

    /// <summary>
    /// Validate if a string is a valid 2-digit lottery number.
    /// </summary>
    /// <param name="loto">Lottery number string</param>
    /// <returns>True if valid (00-99), false otherwise</returns>
    public static bool IsValidLoto(string loto)
    {
        if (string.IsNullOrEmpty(loto) || loto.Length != 2)
            return false;

        return loto.All(char.IsDigit) && 
               int.TryParse(loto, out var num) && 
               num >= 0 && num <= 99;
    }

    /// <summary>
    /// Validate if a period/draw identifier is valid.
    /// </summary>
    /// <param name="ky">Period identifier</param>
    /// <returns>True if valid (non-empty, alphanumeric), false otherwise</returns>
    public static bool IsValidKy(string ky)
    {
        if (string.IsNullOrWhiteSpace(ky))
            return false;

        // Must contain at least one digit
        return ky.Any(char.IsDigit) && ky.Length >= 3;
    }
}
