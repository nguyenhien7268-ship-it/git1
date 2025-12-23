namespace XsDas.Core.Models;

/// <summary>
/// Represents AI data record from DuLieu_AI table.
/// Maps to Python's DuLieu_AI table schema.
/// </summary>
public class DuLieuAi
{
    /// <summary>
    /// Period identifier (Mã Số Kỳ)
    /// </summary>
    public int MaSoKy { get; set; }
    
    /// <summary>
    /// Column A - Period/Draw (Kỳ)
    /// </summary>
    public string? ColAKy { get; set; }
    
    /// <summary>
    /// Column B - Giải Đặc Biệt (Special Prize)
    /// </summary>
    public string? ColBGdb { get; set; }
    
    /// <summary>
    /// Column C - Giải Nhất (First Prize)
    /// </summary>
    public string? ColCG1 { get; set; }
    
    /// <summary>
    /// Column D - Giải Nhì (Second Prize)
    /// </summary>
    public string? ColDG2 { get; set; }
    
    /// <summary>
    /// Column E - Giải Ba (Third Prize)
    /// </summary>
    public string? ColEG3 { get; set; }
    
    /// <summary>
    /// Column F - Giải Tư (Fourth Prize)
    /// </summary>
    public string? ColFG4 { get; set; }
    
    /// <summary>
    /// Column G - Giải Năm (Fifth Prize)
    /// </summary>
    public string? ColGG5 { get; set; }
    
    /// <summary>
    /// Column H - Giải Sáu (Sixth Prize)
    /// </summary>
    public string? ColHG6 { get; set; }
    
    /// <summary>
    /// Column I - Giải Bảy (Seventh Prize)
    /// </summary>
    public string? ColIG7 { get; set; }
}
