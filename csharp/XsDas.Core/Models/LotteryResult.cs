namespace XsDas.Core.Models;

/// <summary>
/// Represents a lottery drawing result (results_A_I table)
/// </summary>
public class LotteryResult
{
    public int Id { get; set; }
    public string Ky { get; set; } = string.Empty;
    public string? Date { get; set; }
    
    // Prize columns (Giải Đặc Biệt through Giải 7)
    public string? Gdb { get; set; }
    public string? G1 { get; set; }
    public string? G2 { get; set; }
    public string? G3 { get; set; }
    public string? G4 { get; set; }
    public string? G5 { get; set; }
    public string? G6 { get; set; }
    public string? G7 { get; set; }
    
    // Loto columns (L0-L26, 27 columns for all 2-digit numbers)
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
}
