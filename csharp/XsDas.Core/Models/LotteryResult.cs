using System;

namespace XsDas.Core.Models;

/// <summary>
/// Represents a single lottery draw result
/// Ported from: logic/models.py and data structures in db_manager.py
/// </summary>
public class LotteryResult
{
    public int Id { get; set; }
    public string MaSoKy { get; set; } = string.Empty;
    public DateTime DrawDate { get; set; }
    
    // Prize columns (GĐB = Giải Đặc Biệt, G1-G7 = Giải 1-7)
    public string GiaiDacBiet { get; set; } = string.Empty;
    public string Giai1 { get; set; } = string.Empty;
    public string Giai2 { get; set; } = string.Empty;
    public string Giai3 { get; set; } = string.Empty;
    public string Giai4 { get; set; } = string.Empty;
    public string Giai5 { get; set; } = string.Empty;
    public string Giai6 { get; set; } = string.Empty;
    public string Giai7 { get; set; } = string.Empty;
    
    /// <summary>
    /// Extract all 27 loto numbers from this result (2-digit endings)
    /// Ported from: logic/utils.py::getAllLoto_V30
    /// </summary>
    public List<string> GetAllLotos()
    {
        var lotos = new List<string>();
        
        // Add GĐB
        if (!string.IsNullOrEmpty(GiaiDacBiet))
            lotos.Add(GetLast2Digits(GiaiDacBiet));
        
        // Add G1
        if (!string.IsNullOrEmpty(Giai1))
            lotos.Add(GetLast2Digits(Giai1));
        
        // Add G2-G7 (may have multiple numbers separated by comma)
        foreach (var prize in new[] { Giai2, Giai3, Giai4, Giai5, Giai6, Giai7 })
        {
            if (string.IsNullOrEmpty(prize)) continue;
            
            foreach (var number in prize.Split(','))
            {
                var trimmed = number.Trim();
                if (!string.IsNullOrEmpty(trimmed))
                    lotos.Add(GetLast2Digits(trimmed));
            }
        }
        
        return lotos.Where(l => l.Length == 2 && l.All(char.IsDigit)).ToList();
    }
    
    private static string GetLast2Digits(string number)
    {
        var cleaned = number.Trim();
        return cleaned.Length >= 2 
            ? cleaned.Substring(cleaned.Length - 2).PadLeft(2, '0')
            : cleaned.PadLeft(2, '0');
    }
}
