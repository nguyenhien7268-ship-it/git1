using Xunit;
using XsDas.Core.Utils;

namespace XsDas.Core.Tests.Utils;

/// <summary>
/// Unit tests for LotteryUtils class
/// Validates core lottery utility functions ported from Python
/// </summary>
public class LotteryUtilsTests
{
    [Theory]
    [InlineData('0', '5')]
    [InlineData('1', '6')]
    [InlineData('2', '7')]
    [InlineData('3', '8')]
    [InlineData('4', '9')]
    [InlineData('5', '0')]
    [InlineData('6', '1')]
    [InlineData('7', '2')]
    [InlineData('8', '3')]
    [InlineData('9', '4')]
    public void GetBongDuong_ReturnsCorrectShadow(char input, char expected)
    {
        // Act
        var result = LotteryUtils.GetBongDuong(input);

        // Assert
        Assert.Equal(expected, result);
    }

    [Fact]
    public void CreateStlBongPair_WithSameDigits_ReturnsDoubleAndShadow()
    {
        // Arrange
        char a = '3';
        char b = '3';

        // Act
        var result = LotteryUtils.CreateStlBongPair(a, b);

        // Assert
        Assert.Equal(2, result.Count);
        Assert.Equal("33", result[0]); // Original double
        Assert.Equal("88", result[1]); // Shadow of 3 is 8
    }

    [Fact]
    public void CreateStlBongPair_WithDifferentDigits_ReturnsBothPermutations()
    {
        // Arrange
        char a = '2';
        char b = '5';

        // Act
        var result = LotteryUtils.CreateStlBongPair(a, b);

        // Assert
        Assert.Equal(2, result.Count);
        Assert.Equal("25", result[0]);
        Assert.Equal("52", result[1]);
    }

    [Fact]
    public void CheckHitStlPair_WithBothHits_ReturnsWin2()
    {
        // Arrange
        var stlPair = new List<string> { "12", "34" };
        var lotoSet = new HashSet<string> { "12", "34", "56" };

        // Act
        var result = LotteryUtils.CheckHitStlPair(stlPair, lotoSet);

        // Assert
        Assert.Equal("✅ (Ăn 2)", result);
    }

    [Fact]
    public void CheckHitStlPair_WithOneHit_ReturnsWin1()
    {
        // Arrange
        var stlPair = new List<string> { "12", "34" };
        var lotoSet = new HashSet<string> { "12", "56" };

        // Act
        var result = LotteryUtils.CheckHitStlPair(stlPair, lotoSet);

        // Assert
        Assert.Equal("✅ (Ăn 1)", result);
    }

    [Fact]
    public void CheckHitStlPair_WithNoHits_ReturnsLoss()
    {
        // Arrange
        var stlPair = new List<string> { "12", "34" };
        var lotoSet = new HashSet<string> { "56", "78" };

        // Act
        var result = LotteryUtils.CheckHitStlPair(stlPair, lotoSet);

        // Assert
        Assert.Equal("❌", result);
    }

    [Theory]
    [InlineData("Cầu Bạc Nhớ", "cau bac nho")]
    [InlineData("Đề Động", "de dong")]
    [InlineData("CẦU V17", "cau v17")]
    [InlineData("Bóng Âm Dương", "bong am duong")]
    public void NormalizeVietnamese_RemovesDiacriticsAndLowercase(string input, string expected)
    {
        // Act
        var result = LotteryUtils.NormalizeVietnamese(input);

        // Assert
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("12", true)]
    [InlineData("00", true)]
    [InlineData("99", true)]
    [InlineData("1", false)]
    [InlineData("123", false)]
    [InlineData("ab", false)]
    [InlineData("", false)]
    [InlineData(null, false)]
    public void IsValidLoto_ValidatesCorrectly(string? loto, bool expected)
    {
        // Act
        var result = LotteryUtils.IsValidLoto(loto);

        // Assert
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(85.5, "85.50%")]
    [InlineData(100.0, "100.00%")]
    [InlineData(0.0, "0.00%")]
    [InlineData(50.123, "50.12%")]
    public void FormatWinRate_FormatsCorrectly(double rate, string expected)
    {
        // Act
        var result = LotteryUtils.FormatWinRate(rate);

        // Assert
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("85.50%", 85.5)]
    [InlineData("100%", 100.0)]
    [InlineData("0.00%", 0.0)]
    [InlineData("50.123", 50.123)]
    [InlineData("", 0.0)]
    [InlineData(null, 0.0)]
    public void ParseWinRate_ParsesCorrectly(string? rateText, double expected)
    {
        // Act
        var result = LotteryUtils.ParseWinRate(rateText);

        // Assert
        Assert.Equal(expected, result, precision: 2);
    }

    [Fact]
    public void GetAllLotos_ExtractsLotosFromRow()
    {
        // Arrange - simulate database row
        object?[] row = new object?[]
        {
            1, // MaSoKy
            "123456", // Ky
            "12345", // GDB (will extract "45")
            "67890", // G1 (will extract "90")
            "111,222,333", // G2 (will extract "11", "22", "33")
            "444,555", // G3 (will extract "44", "55")
            "666", // G4 (will extract "66")
            "777", // G5 (will extract "77")
            "888", // G6 (will extract "88")
            "999" // G7 (will extract "99")
        };

        // Act
        var result = LotteryUtils.GetAllLotos(row);

        // Assert
        Assert.NotEmpty(result);
        Assert.Contains("45", result); // GDB
        Assert.Contains("90", result); // G1
        Assert.Contains("11", result); // G2[0]
        Assert.Contains("22", result); // G2[1]
        Assert.Contains("33", result); // G2[2]
        Assert.All(result, loto => Assert.True(LotteryUtils.IsValidLoto(loto)));
    }
}
