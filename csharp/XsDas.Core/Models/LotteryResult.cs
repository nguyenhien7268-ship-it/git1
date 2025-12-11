namespace XsDas.Core.Models;

/// <summary>
/// Represents a lottery result entry (corresponds to results_A_I and DuLieu_AI tables)
/// </summary>
public class LotteryResult
{
    public int Id { get; set; }
    
    /// <summary>
    /// Kỳ quay số (lottery period identifier)
    /// </summary>
    public string Ky { get; set; } = string.Empty;
    
    /// <summary>
    /// Ngày quay (draw date)
    /// </summary>
    public string Date { get; set; } = string.Empty;
    
    // Prize columns (Giải - GDB, G1-G7)
    public string? Gdb { get; set; }
    public string? G1 { get; set; }
    public string? G2 { get; set; }
    public string? G3 { get; set; }
    public string? G4 { get; set; }
    public string? G5 { get; set; }
    public string? G6 { get; set; }
    public string? G7 { get; set; }
    
    // Loto columns (L0-L26) - 27 numbers extracted from prizes
    public string? L0 { get; set; }
    public string? L1 { get; set; }
    public string? L2 { get; set; }
    public string? L3 { get; set; }
    public string? L4 { get; set; }
    public string? L5 { get; set; }
    public string? L6 { get; set; }
    public string? L7 { get; set; }
    public string? L8 { get; set; }
    public string? L9 { get; set; }
    public string? L10 { get; set; }
    public string? L11 { get; set; }
    public string? L12 { get; set; }
    public string? L13 { get; set; }
    public string? L14 { get; set; }
    public string? L15 { get; set; }
    public string? L16 { get; set; }
    public string? L17 { get; set; }
    public string? L18 { get; set; }
    public string? L19 { get; set; }
    public string? L20 { get; set; }
    public string? L21 { get; set; }
    public string? L22 { get; set; }
    public string? L23 { get; set; }
    public string? L24 { get; set; }
    public string? L25 { get; set; }
    public string? L26 { get; set; }
    
    /// <summary>
    /// Get all loto numbers as a list (filters null/empty values)
    /// </summary>
    public List<string> GetAllLotos()
    {
        var lotos = new List<string?> 
        { 
            L0, L1, L2, L3, L4, L5, L6, L7, L8, L9,
            L10, L11, L12, L13, L14, L15, L16, L17, L18, L19,
            L20, L21, L22, L23, L24, L25, L26
        };
        
        return lotos
            .Where(l => !string.IsNullOrWhiteSpace(l) && l.Length == 2)
            .Select(l => l!)
            .ToList();
    }
}
