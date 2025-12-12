using XsDas.Infrastructure.Services;

namespace XsDas.Core.Tests.Services;

/// <summary>
/// Unit tests for ScannerService - validates all 15 bridge algorithms
/// Tests match Python bridge outputs for verification
/// </summary>
public class ScannerServiceTests
{
    private readonly ScannerService _scanner;

    public ScannerServiceTests()
    {
        _scanner = new ScannerService();
    }

    #region Bridge 1: STL Plus 5 Tests

    [Fact]
    public void ScanCau1StlP5_WithValidGDB_ReturnsCorrectSTL()
    {
        // Arrange: GDB ending in 23 -> +5 = 78, 87 (permutations)
        var row = new object[] { null, null, "123", null, null, null, null, null, null, null };

        // Act
        var result = _scanner.ScanCau1StlP5(row);

        // Assert
        Assert.Equal(2, result.Length);
        Assert.Contains("78", result);
        Assert.Contains("87", result);
    }

    [Fact]
    public void ScanCau1StlP5_WithDuplicateDigits_ReturnsShadowPair()
    {
        // Arrange: GDB ending in 33 -> +5 = 88
        var row = new object[] { null, null, "133", null, null, null, null, null, null, null };

        // Act
        var result = _scanner.ScanCau1StlP5(row);

        // Assert
        Assert.Equal(2, result.Length);
        Assert.Equal("88", result[0]);
        Assert.Equal("33", result[1]); // Shadow pair
    }

    #endregion

    #region Bridge 3: VT2 Tests

    [Fact]
    public void ScanCau3Vt2_WithValidData_ReturnsCorrectPair()
    {
        // Arrange: GDB last digit 5, G1 last digit 7
        var row = new object[] { null, null, "125", "237", null, null, null, null, null, null };

        // Act
        var result = _scanner.ScanCau3Vt2(row);

        // Assert
        Assert.Equal(2, result.Length);
        Assert.Contains("57", result);
        Assert.Contains("75", result);
    }

    #endregion

    #region Bridge 7: Moi1 Tests

    [Fact]
    public void ScanCau7Moi1_WithValidData_ReturnsFirstDigits()
    {
        // Arrange: G5[0] first = 3, G7[0] first = 8
        var row = new object[] { null, null, null, null, null, null, null, "3456,1234", null, "8765,4321" };

        // Act
        var result = _scanner.ScanCau7Moi1(row);

        // Assert
        Assert.Equal(2, result.Length);
        Assert.Contains("38", result);
        Assert.Contains("83", result);
    }

    #endregion

    #region Bridge 13: G7-3 Plus 8 Tests

    [Fact]
    public void ScanCau13G7_3P8_WithValidData_AddsEightCorrectly()
    {
        // Arrange: G7[2] = 15 -> +8 = 93
        var row = new object[] { null, null, null, null, null, null, null, null, null, "111,222,15" };

        // Act
        var result = _scanner.ScanCau13G7_3P8(row);

        // Assert
        Assert.Equal(2, result.Length);
        Assert.Equal("93", result[0]);
        Assert.Equal("39", result[1]);
    }

    #endregion

    #region Bridge 15: DE Plus 7 Tests

    [Fact]
    public void ScanCau15DeP7_WithValidGDB_AddsSevenCorrectly()
    {
        // Arrange: GDB ending in 45 -> +7 = 12
        var row = new object[] { null, null, "12345", null, null, null, null, null, null, null };

        // Act
        var result = _scanner.ScanCau15DeP7(row);

        // Assert
        Assert.Equal(2, result.Length);
        Assert.Contains("12", result);
        Assert.Contains("21", result);
    }

    #endregion

    #region Error Handling Tests

    [Fact]
    public void ScanCau1StlP5_WithNullRow_ReturnsDefault()
    {
        // Arrange: null at position 2
        var row = new object[] { null, null, null, null, null, null, null, null, null, null };

        // Act
        var result = _scanner.ScanCau1StlP5(row);

        // Assert
        Assert.Equal(2, result.Length);
        // Default result for error case - should be "00" and "55" (shadow pair)
        Assert.Contains("00", result);
        Assert.Contains("55", result);
    }

    [Fact]
    public void ScanCau2Vt1_WithEmptyGPrizes_ReturnsDefault()
    {
        // Arrange: empty G6 and G7
        var row = new object[] { null, null, null, null, null, null, null, null, "", "" };

        // Act
        var result = _scanner.ScanCau2Vt1(row);

        // Assert
        Assert.Equal(2, result.Length);
        // Should handle gracefully
    }

    #endregion

    #region All Scanners Test

    [Fact]
    public void GetAllBridgeScanners_Returns15Scanners()
    {
        // Act
        var scanners = _scanner.GetAllBridgeScanners().ToList();

        // Assert
        Assert.Equal(15, scanners.Count);
        
        // Verify each scanner works with a test row
        var testRow = new object[] { null, null, "12345", "67", "11,22", "33,44,55", "66,77", "88,99", "00,11,22", "33,44,55,66" };
        
        foreach (var scanner in scanners)
        {
            var result = scanner(testRow);
            Assert.NotNull(result);
            Assert.Equal(2, result.Length);
        }
    }

    #endregion

    #region Integration Tests with Real-like Data

    [Fact]
    public void AllBridges_WithCompleteRow_ProduceValidResults()
    {
        // Arrange: Complete lottery row with all prizes
        var row = new object[]
        {
            12345, // MaSoKy
            "2023-01-01", // Ky
            "123456", // GDB
            "12345", // G1
            "1234,5678", // G2
            "111,222,333", // G3
            "444,555", // G4
            "666,777,888", // G5
            "999,000,111", // G6
            "222,333,444,555" // G7
        };

        // Act & Assert: All bridges should produce valid 2-digit pairs
        var allScanners = _scanner.GetAllBridgeScanners();
        
        foreach (var scanner in allScanners)
        {
            var result = scanner(row);
            
            Assert.NotNull(result);
            Assert.Equal(2, result.Length);
            
            // Each result should be 2 digits
            foreach (var lotto in result)
            {
                Assert.Equal(2, lotto.Length);
                Assert.True(lotto.All(char.IsDigit), $"Result {lotto} should be all digits");
            }
        }
    }

    #endregion
}
