namespace XsDas.Core.Interfaces;

/// <summary>
/// Service interface for bridge scanning operations.
/// Provides methods to scan lottery data using various bridge algorithms.
/// </summary>
public interface IScannerService
{
    /// <summary>
    /// Scan using Bridge 1: STL Plus 5 algorithm
    /// </summary>
    string[] ScanCau1StlP5(object[] row);

    /// <summary>
    /// Scan using Bridge 2: VT1 algorithm
    /// </summary>
    string[] ScanCau2Vt1(object[] row);

    /// <summary>
    /// Scan using Bridge 3: VT2 algorithm
    /// </summary>
    string[] ScanCau3Vt2(object[] row);

    /// <summary>
    /// Scan using Bridge 4: VT3 algorithm
    /// </summary>
    string[] ScanCau4Vt3(object[] row);

    /// <summary>
    /// Scan using Bridge 5: TDB1 algorithm
    /// </summary>
    string[] ScanCau5Tdb1(object[] row);

    /// <summary>
    /// Scan using Bridge 6: VT5 algorithm
    /// </summary>
    string[] ScanCau6Vt5(object[] row);

    /// <summary>
    /// Scan using Bridge 7: Moi1 algorithm
    /// </summary>
    string[] ScanCau7Moi1(object[] row);

    /// <summary>
    /// Scan using Bridge 8: Moi2 algorithm
    /// </summary>
    string[] ScanCau8Moi2(object[] row);

    /// <summary>
    /// Scan using Bridge 9: Moi3 algorithm
    /// </summary>
    string[] ScanCau9Moi3(object[] row);

    /// <summary>
    /// Scan using Bridge 10: Moi4 algorithm
    /// </summary>
    string[] ScanCau10Moi4(object[] row);

    /// <summary>
    /// Scan using Bridge 11: Moi5 algorithm
    /// </summary>
    string[] ScanCau11Moi5(object[] row);

    /// <summary>
    /// Scan using Bridge 12: Moi6 algorithm
    /// </summary>
    string[] ScanCau12Moi6(object[] row);

    /// <summary>
    /// Scan using Bridge 13: G7-3 Plus 8 algorithm
    /// </summary>
    string[] ScanCau13G7_3P8(object[] row);

    /// <summary>
    /// Scan using Bridge 14: G1 Plus 2 algorithm
    /// </summary>
    string[] ScanCau14G1P2(object[] row);

    /// <summary>
    /// Scan using Bridge 15: DE Plus 7 algorithm
    /// </summary>
    string[] ScanCau15DeP7(object[] row);

    /// <summary>
    /// Get all bridge scanner methods
    /// </summary>
    IEnumerable<Func<object[], string[]>> GetAllBridgeScanners();
}
