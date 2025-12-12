namespace XsDas.Core.Models;

/// <summary>
/// Represents a lottery result record from results_A_I table.
/// Maps to Python's results_A_I table schema.
/// </summary>
public class LotteryResult
{
    public int Id { get; set; }
    
    /// <summary>
    /// Lottery period/draw identifier (Kỳ)
    /// </summary>
    public string Ky { get; set; } = string.Empty;
    
    /// <summary>
    /// Draw date
    /// </summary>
    public string Date { get; set; } = string.Empty;
    
    // Prize columns (Giải)
    public string? Gdb { get; set; }  // Giải Đặc Biệt
    public string? G1 { get; set; }   // Giải Nhất
    public string? G2 { get; set; }   // Giải Nhì
    public string? G3 { get; set; }   // Giải Ba
    public string? G4 { get; set; }   // Giải Tư
    public string? G5 { get; set; }   // Giải Năm
    public string? G6 { get; set; }   // Giải Sáu
    public string? G7 { get; set; }   // Giải Bảy
    
    // Lotto columns (27 columns: l0-l26)
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
