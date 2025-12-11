namespace XsDas.Core.Utils;

/// <summary>
/// Core lottery utility functions ported from Python logic/utils.py
/// </summary>
public static class LotteryUtils
{
    /// <summary>
    /// Shadow mapping for Bóng Dương (V30 algorithm)
    /// Maps each digit to its complement (0→5, 1→6, 2→7, 3→8, 4→9, and reverse)
    /// </summary>
    private static readonly Dictionary<char, char> BongDuongV30 = new()
    {
        ['0'] = '5', ['1'] = '6', ['2'] = '7', ['3'] = '8', ['4'] = '9',
        ['5'] = '0', ['6'] = '1', ['7'] = '2', ['8'] = '3', ['9'] = '4'
    };

    /// <summary>
    /// Gets the shadow (Bóng Dương) digit for a given digit
    /// </summary>
    /// <param name="digit">Input digit character</param>
    /// <returns>Shadow digit character</returns>
    public static char GetBongDuong(char digit)
    {
        return BongDuongV30.TryGetValue(digit, out var shadow) ? shadow : digit;
    }

    /// <summary>
    /// Creates STL (Straight/Touch/Lo) pair from two digits with shadow logic
    /// If digits are same (e.g., 3,3), returns [33, 88] (original + shadow)
    /// If different (e.g., 3,5), returns [35, 53] (both permutations)
    /// </summary>
    /// <param name="a">First digit</param>
    /// <param name="b">Second digit</param>
    /// <returns>List of 2-digit lottery numbers</returns>
    public static List<string> TaoStlV30Bong(int a, int b)
    {
        var strA = a.ToString();
        var strB = b.ToString();

        if (strA == strB)
        {
            // Kép (double): create original and shadow pair
            var kep = $"{strA}{strB}".PadLeft(2, '0');
            var bongDigit = GetBongDuong(strA[0]);
            var bongKep = $"{bongDigit}{bongDigit}";
            return new List<string> { kep, bongKep };
        }
        else
        {
            // Regular: create both permutations
            var lo1 = $"{strA}{strB}".PadLeft(2, '0');
            var lo2 = $"{strB}{strA}".PadLeft(2, '0');
            return new List<string> { lo1, lo2 };
        }
    }

    /// <summary>
    /// Extracts all 27 loto numbers from a lottery result row
    /// Processes GDB (1), G1 (1), and G2-G7 (multiple numbers each)
    /// </summary>
    /// <param name="gdb">Giải Đặc Biệt</param>
    /// <param name="g1">Giải Nhất</param>
    /// <param name="g2">Giải Nhì (comma-separated)</param>
    /// <param name="g3">Giải Ba (comma-separated)</param>
    /// <param name="g4">Giải Tư (comma-separated)</param>
    /// <param name="g5">Giải Năm (comma-separated)</param>
    /// <param name="g6">Giải Sáu (comma-separated)</param>
    /// <param name="g7">Giải Bảy (comma-separated)</param>
    /// <returns>List of all 2-digit loto numbers</returns>
    public static List<string> GetAllLotoV30(
        string? gdb, string? g1, string? g2, string? g3,
        string? g4, string? g5, string? g6, string? g7)
    {
        var lotos = new List<string>();

        try
        {
            // Add GDB (last 2 digits)
            if (!string.IsNullOrEmpty(gdb))
            {
                var last2 = new string(gdb.Trim().TakeLast(2).ToArray());
                lotos.Add(last2.PadLeft(2, '0'));
            }

            // Add G1 (last 2 digits)
            if (!string.IsNullOrEmpty(g1))
            {
                var last2 = new string(g1.Trim().TakeLast(2).ToArray());
                lotos.Add(last2.PadLeft(2, '0'));
            }

            // Process G2-G7 (comma-separated values)
            var prizes = new[] { g2, g3, g4, g5, g6, g7 };
            foreach (var prize in prizes)
            {
                if (!string.IsNullOrEmpty(prize))
                {
                    foreach (var num in prize.Split(','))
                    {
                        var trimmed = num.Trim();
                        if (trimmed.Length >= 2)
                        {
                            var last2 = new string(trimmed.TakeLast(2).ToArray()).PadLeft(2, '0');
                            lotos.Add(last2);
                        }
                    }
                }
            }
        }
        catch
        {
            // Silently handle errors
        }

        // Filter valid 2-digit numbers
        return lotos.Where(l => l.Length == 2 && l.All(char.IsDigit)).ToList();
    }

    /// <summary>
    /// Checks if an STL pair hits in the lottery result set (K2N mode)
    /// Returns hit status: "✅ (Ăn 2)" for both, "✅ (Ăn 1)" for one, "❌" for none
    /// </summary>
    /// <param name="stlPair">STL pair to check (2 numbers)</param>
    /// <param name="lotoSet">Set of lottery numbers from the draw</param>
    /// <returns>Hit status string</returns>
    public static string CheckHitSetV30K2N(List<string> stlPair, HashSet<string> lotoSet)
    {
        try
        {
            if (stlPair.Count != 2)
                return "Lỗi check";

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
    /// Normalizes Vietnamese text to ASCII (removes diacritics)
    /// </summary>
    /// <param name="text">Vietnamese text</param>
    /// <returns>Normalized ASCII text</returns>
    public static string NormalizeVietnamese(string text)
    {
        if (string.IsNullOrEmpty(text))
            return string.Empty;

        var vietnameseMap = new Dictionary<char, char>
        {
            ['à'] = 'a', ['á'] = 'a', ['ả'] = 'a', ['ã'] = 'a', ['ạ'] = 'a',
            ['ă'] = 'a', ['ằ'] = 'a', ['ắ'] = 'a', ['ẳ'] = 'a', ['ẵ'] = 'a', ['ặ'] = 'a',
            ['â'] = 'a', ['ầ'] = 'a', ['ấ'] = 'a', ['ẩ'] = 'a', ['ẫ'] = 'a', ['ậ'] = 'a',
            ['đ'] = 'd',
            ['è'] = 'e', ['é'] = 'e', ['ẻ'] = 'e', ['ẽ'] = 'e', ['ẹ'] = 'e',
            ['ê'] = 'e', ['ề'] = 'e', ['ế'] = 'e', ['ể'] = 'e', ['ễ'] = 'e', ['ệ'] = 'e',
            ['ì'] = 'i', ['í'] = 'i', ['ỉ'] = 'i', ['ĩ'] = 'i', ['ị'] = 'i',
            ['ò'] = 'o', ['ó'] = 'o', ['ỏ'] = 'o', ['õ'] = 'o', ['ọ'] = 'o',
            ['ô'] = 'o', ['ồ'] = 'o', ['ố'] = 'o', ['ổ'] = 'o', ['ỗ'] = 'o', ['ộ'] = 'o',
            ['ơ'] = 'o', ['ờ'] = 'o', ['ớ'] = 'o', ['ở'] = 'o', ['ỡ'] = 'o', ['ợ'] = 'o',
            ['ù'] = 'u', ['ú'] = 'u', ['ủ'] = 'u', ['ũ'] = 'u', ['ụ'] = 'u',
            ['ư'] = 'u', ['ừ'] = 'u', ['ứ'] = 'u', ['ử'] = 'u', ['ữ'] = 'u', ['ự'] = 'u',
            ['ỳ'] = 'y', ['ý'] = 'y', ['ỷ'] = 'y', ['ỹ'] = 'y', ['ỵ'] = 'y',
        };

        var result = new char[text.Length];
        for (int i = 0; i < text.Length; i++)
        {
            var lowerChar = char.ToLower(text[i]);
            result[i] = vietnameseMap.TryGetValue(lowerChar, out var normalized) 
                ? normalized 
                : lowerChar;
        }

        return new string(result);
    }

    /// <summary>
    /// Formats win rate as percentage string
    /// </summary>
    /// <param name="wins">Number of wins</param>
    /// <param name="total">Total attempts</param>
    /// <returns>Formatted percentage (e.g., "85.50%")</returns>
    public static string FormatWinRate(int wins, int total)
    {
        if (total == 0)
            return "0.00%";
        
        var rate = (double)wins / total * 100.0;
        return $"{rate:F2}%";
    }

    /// <summary>
    /// Validates if a string is a valid 2-digit loto number (00-99)
    /// </summary>
    /// <param name="loto">Loto number string</param>
    /// <returns>True if valid</returns>
    public static bool IsValidLoto(string? loto)
    {
        return !string.IsNullOrEmpty(loto) 
            && loto.Length == 2 
            && loto.All(char.IsDigit);
    }

    /// <summary>
    /// Validates if a string is a valid Ky (period) identifier
    /// </summary>
    /// <param name="ky">Ky identifier</param>
    /// <returns>True if valid</returns>
    public static bool IsValidKy(string? ky)
    {
        return !string.IsNullOrEmpty(ky) 
            && ky.All(char.IsDigit)
            && ky.Length >= 4;
    }
}
