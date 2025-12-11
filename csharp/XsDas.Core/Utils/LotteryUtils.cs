using System.Text;
using System.Globalization;

namespace XsDas.Core.Utils;

/// <summary>
/// Core utility functions for lottery analysis
/// Ported from Python logic/utils.py
/// </summary>
public static class LotteryUtils
{
    // Shadow mapping (Bóng Dương V30) - maps each digit to its shadow
    private static readonly Dictionary<char, char> BongDuongV30 = new()
    {
        { '0', '5' }, { '1', '6' }, { '2', '7' }, { '3', '8' }, { '4', '9' },
        { '5', '0' }, { '6', '1' }, { '7', '2' }, { '8', '3' }, { '9', '4' }
    };

    /// <summary>
    /// Get shadow digit for a given digit (Bóng Dương mapping)
    /// </summary>
    /// <param name="digit">Input digit character</param>
    /// <returns>Shadow digit character</returns>
    public static char GetBongDuong(char digit)
    {
        return BongDuongV30.TryGetValue(digit, out var shadow) ? shadow : digit;
    }

    /// <summary>
    /// Create STL pair with shadow (Bóng) logic
    /// If a == b (double digit): returns [aa, bb] where b is shadow of a
    /// If a != b: returns [ab, ba] (both permutations)
    /// </summary>
    /// <param name="a">First digit</param>
    /// <param name="b">Second digit</param>
    /// <returns>List of two STL predictions</returns>
    public static List<string> CreateStlBongPair(char a, char b)
    {
        if (a == b)
        {
            // Double digit case: create pair with shadow
            var kep = $"{a}{b}";
            var shadowDigit = GetBongDuong(a);
            var shadowKep = $"{shadowDigit}{shadowDigit}";
            return new List<string> { kep, shadowKep };
        }
        else
        {
            // Different digits: create both permutations
            var lo1 = $"{a}{b}";
            var lo2 = $"{b}{a}";
            return new List<string> { lo1, lo2 };
        }
    }

    /// <summary>
    /// Create STL pair with shadow logic (string overload)
    /// </summary>
    public static List<string> CreateStlBongPair(string a, string b)
    {
        if (string.IsNullOrEmpty(a) || string.IsNullOrEmpty(b))
            return new List<string>();
        
        return CreateStlBongPair(a[0], b[0]);
    }

    /// <summary>
    /// Extract all loto numbers from a lottery result row
    /// Extracts last 2 digits from each prize and returns 27 lotos
    /// </summary>
    /// <param name="row">Database row with prizes (GDB, G1, G2-G7)</param>
    /// <returns>List of 2-digit loto numbers</returns>
    public static List<string> GetAllLotos(object?[] row)
    {
        var lotos = new List<string>();
        
        try
        {
            // row[0] = MaSoKy (ID), row[1] = Ky
            // row[2] = GDB, row[3] = G1, row[4-9] = G2-G7
            
            // GDB - Giải Đặc Biệt (row[2])
            if (row.Length > 2 && row[2] != null)
            {
                lotos.Add(ExtractLast2Digits(row[2].ToString() ?? "0"));
            }
            
            // G1 - Giải Nhất (row[3])
            if (row.Length > 3 && row[3] != null)
            {
                lotos.Add(ExtractLast2Digits(row[3].ToString() ?? "0"));
            }
            
            // G2-G7 (row[4] to row[9]) - may contain comma-separated values
            for (int i = 4; i < 10 && i < row.Length; i++)
            {
                if (row[i] != null)
                {
                    var prizeStr = row[i].ToString() ?? "";
                    var prizes = prizeStr.Split(',');
                    
                    foreach (var prize in prizes)
                    {
                        var loto = ExtractLast2Digits(prize.Trim());
                        if (!string.IsNullOrEmpty(loto))
                        {
                            lotos.Add(loto);
                        }
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error in GetAllLotos: {ex.Message}");
        }
        
        // Filter: only return valid 2-digit numbers
        return lotos
            .Where(l => l.Length == 2 && l.All(char.IsDigit))
            .ToList();
    }

    /// <summary>
    /// Extract last 2 digits from a string and pad with leading zero if needed
    /// </summary>
    private static string ExtractLast2Digits(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
            return "00";
        
        var cleaned = value.Trim();
        if (cleaned.Length >= 2)
        {
            return cleaned.Substring(cleaned.Length - 2);
        }
        
        return cleaned.PadLeft(2, '0');
    }

    /// <summary>
    /// Check if an STL pair hits in a set of lotos (K2N checking)
    /// Returns hit status string
    /// </summary>
    /// <param name="stlPair">Pair of STL predictions [a, b]</param>
    /// <param name="lotoSet">Set of drawn loto numbers</param>
    /// <returns>Hit status: "✅ (Ăn 2)", "✅ (Ăn 1)", or "❌"</returns>
    public static string CheckHitStlPair(List<string> stlPair, HashSet<string> lotoSet)
    {
        try
        {
            if (stlPair.Count < 2)
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
    /// Normalize Vietnamese text - remove diacritics and convert to lowercase
    /// Used for bridge name comparison and duplicate detection
    /// </summary>
    public static string NormalizeVietnamese(string text)
    {
        if (string.IsNullOrWhiteSpace(text))
            return string.Empty;
        
        // Normalize to FormD (decomposed form - separates base characters from diacritics)
        var normalizedString = text.Normalize(NormalizationForm.FormD);
        var stringBuilder = new StringBuilder();
        
        foreach (var c in normalizedString)
        {
            var unicodeCategory = CharUnicodeInfo.GetUnicodeCategory(c);
            // Skip combining marks (diacritics)
            if (unicodeCategory != UnicodeCategory.NonSpacingMark)
            {
                stringBuilder.Append(c);
            }
        }
        
        // Additional Vietnamese-specific replacements
        var result = stringBuilder.ToString()
            .Replace("đ", "d")
            .Replace("Đ", "D");
        
        return result.Normalize(NormalizationForm.FormC).ToLowerInvariant();
    }

    /// <summary>
    /// Check if a loto is valid (2 digits, all numeric)
    /// </summary>
    public static bool IsValidLoto(string? loto)
    {
        return !string.IsNullOrWhiteSpace(loto) 
               && loto.Length == 2 
               && loto.All(char.IsDigit);
    }

    /// <summary>
    /// Check if a Ky (period) identifier is valid
    /// </summary>
    public static bool IsValidKy(string? ky)
    {
        return !string.IsNullOrWhiteSpace(ky);
    }

    /// <summary>
    /// Format win rate as percentage string
    /// </summary>
    public static string FormatWinRate(double rate)
    {
        return $"{rate:F2}%";
    }

    /// <summary>
    /// Parse win rate from percentage string (e.g., "85.5%" -> 85.5)
    /// </summary>
    public static double ParseWinRate(string rateText)
    {
        if (string.IsNullOrWhiteSpace(rateText))
            return 0.0;
        
        var cleaned = rateText.Replace("%", "").Trim();
        if (double.TryParse(cleaned, out var rate))
            return rate;
        
        return 0.0;
    }
}
