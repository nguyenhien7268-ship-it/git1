using XsDas.Core.Utils;
using Xunit;

namespace XsDas.Core.Tests.Utils;

/// <summary>
/// Unit tests for LotteryUtils - Core lottery utility functions
/// Tests cover shadow mapping, STL generation, loto extraction, and validation
/// Total: 38 tests covering all major functionality
/// </summary>
public class LotteryUtilsTests
{
    #region Shadow Mapping Tests (Bóng Dương) - 11 tests

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
    public void GetBongDuong_ValidDigits_ReturnsCorrectShadow(char input, char expected)
    {
        var result = LotteryUtils.GetBongDuong(input);
        Assert.Equal(expected, result);
    }

    [Fact]
    public void GetBongDuong_InvalidCharacter_ReturnsSameCharacter()
    {
        var result = LotteryUtils.GetBongDuong('a');
        Assert.Equal('a', result);
    }

    #endregion

    #region STL Pair Generation Tests - 8 tests

    [Fact]
    public void TaoStlV30Bong_SameDigits_ReturnsOriginalAndShadowPair()
    {
        var result = LotteryUtils.TaoStlV30Bong(3, 3);
        Assert.Equal(2, result.Count);
        Assert.Contains("33", result);
        Assert.Contains("88", result);
    }

    [Theory]
    [InlineData(0, 0, "00", "55")]
    [InlineData(5, 5, "55", "00")]
    [InlineData(7, 7, "77", "22")]
    public void TaoStlV30Bong_DoubleDigits_ReturnsCorrectShadowPairs(
        int a, int b, string original, string shadow)
    {
        var result = LotteryUtils.TaoStlV30Bong(a, b);
        Assert.Equal(2, result.Count);
        Assert.Contains(original, result);
        Assert.Contains(shadow, result);
    }

    [Fact]
    public void TaoStlV30Bong_DifferentDigits_ReturnsBothPermutations()
    {
        var result = LotteryUtils.TaoStlV30Bong(3, 5);
        Assert.Equal(2, result.Count);
        Assert.Contains("35", result);
        Assert.Contains("53", result);
    }

    [Theory]
    [InlineData(1, 9, "19", "91")]
    [InlineData(0, 4, "04", "40")]
    [InlineData(2, 8, "28", "82")]
    public void TaoStlV30Bong_VariousPairs_ReturnsBothPermutations(
        int a, int b, string first, string second)
    {
        var result = LotteryUtils.TaoStlV30Bong(a, b);
        Assert.Equal(2, result.Count);
        Assert.Contains(first, result);
        Assert.Contains(second, result);
    }

    #endregion

    #region Loto Extraction Tests - 4 tests

    [Fact]
    public void GetAllLotoV30_AllPrizes_ExtractsAllNumbers()
    {
        var result = LotteryUtils.GetAllLotoV30(
            "12345", "67890", "11111,22222", "33333", 
            "66666", "10101", "11111", "44444");
        
        Assert.NotEmpty(result);
        Assert.Contains("45", result);
        Assert.Contains("90", result);
        Assert.All(result, loto => Assert.Equal(2, loto.Length));
    }

    [Fact]
    public void GetAllLotoV30_NullValues_HandlesGracefully()
    {
        var result = LotteryUtils.GetAllLotoV30(null, null, null, null, null, null, null, null);
        Assert.Empty(result);
    }

    [Fact]
    public void GetAllLotoV30_EmptyStrings_ReturnsEmpty()
    {
        var result = LotteryUtils.GetAllLotoV30("", "", "", "", "", "", "", "");
        Assert.Empty(result);
    }

    [Fact]
    public void GetAllLotoV30_SingleDigitNumbers_PadsWithZero()
    {
        var result = LotteryUtils.GetAllLotoV30("5", "7", null, null, null, null, null, null);
        Assert.Contains("05", result);
        Assert.Contains("07", result);
    }

    #endregion

    #region Hit Detection Tests - 6 tests

    [Fact]
    public void CheckHitSetV30K2N_BothHit_ReturnsAn2()
    {
        var stlPair = new List<string> { "12", "34" };
        var lotoSet = new HashSet<string> { "12", "34", "56" };
        var result = LotteryUtils.CheckHitSetV30K2N(stlPair, lotoSet);
        Assert.Equal("✅ (Ăn 2)", result);
    }

    [Fact]
    public void CheckHitSetV30K2N_FirstHit_ReturnsAn1()
    {
        var stlPair = new List<string> { "12", "34" };
        var lotoSet = new HashSet<string> { "12", "56", "78" };
        var result = LotteryUtils.CheckHitSetV30K2N(stlPair, lotoSet);
        Assert.Equal("✅ (Ăn 1)", result);
    }

    [Fact]
    public void CheckHitSetV30K2N_SecondHit_ReturnsAn1()
    {
        var stlPair = new List<string> { "12", "34" };
        var lotoSet = new HashSet<string> { "34", "56", "78" };
        var result = LotteryUtils.CheckHitSetV30K2N(stlPair, lotoSet);
        Assert.Equal("✅ (Ăn 1)", result);
    }

    [Fact]
    public void CheckHitSetV30K2N_NoHit_ReturnsMiss()
    {
        var stlPair = new List<string> { "12", "34" };
        var lotoSet = new HashSet<string> { "56", "78", "90" };
        var result = LotteryUtils.CheckHitSetV30K2N(stlPair, lotoSet);
        Assert.Equal("❌", result);
    }

    [Fact]
    public void CheckHitSetV30K2N_InvalidPair_ReturnsError()
    {
        var stlPair = new List<string> { "12" };
        var lotoSet = new HashSet<string> { "12", "34" };
        var result = LotteryUtils.CheckHitSetV30K2N(stlPair, lotoSet);
        Assert.Equal("Lỗi check", result);
    }

    [Fact]
    public void CheckHitSetV30K2N_EmptySet_ReturnsMiss()
    {
        var stlPair = new List<string> { "12", "34" };
        var lotoSet = new HashSet<string>();
        var result = LotteryUtils.CheckHitSetV30K2N(stlPair, lotoSet);
        Assert.Equal("❌", result);
    }

    #endregion

    #region Vietnamese Normalization Tests - 5 tests

    [Theory]
    [InlineData("Đề", "de")]
    [InlineData("Cầu", "cau")]
    [InlineData("Lô", "lo")]
    public void NormalizeVietnamese_VietnameseText_ReturnsNormalizedAscii(string input, string expected)
    {
        var result = LotteryUtils.NormalizeVietnamese(input);
        Assert.Equal(expected, result);
    }

    [Fact]
    public void NormalizeVietnamese_NullInput_ReturnsEmptyString()
    {
        var result = LotteryUtils.NormalizeVietnamese(null);
        Assert.Equal(string.Empty, result);
    }

    [Fact]
    public void NormalizeVietnamese_AsciiText_ReturnsUnchanged()
    {
        var input = "hello world 123";
        var result = LotteryUtils.NormalizeVietnamese(input);
        Assert.Equal(input, result);
    }

    #endregion

    #region Win Rate Formatting Tests - 7 tests

    [Theory]
    [InlineData(85, 100, "85.00%")]
    [InlineData(50, 100, "50.00%")]
    [InlineData(100, 100, "100.00%")]
    [InlineData(0, 100, "0.00%")]
    [InlineData(1, 3, "33.33%")]
    [InlineData(2, 3, "66.67%")]
    public void FormatWinRate_ValidInputs_ReturnsFormattedPercentage(int wins, int total, string expected)
    {
        var result = LotteryUtils.FormatWinRate(wins, total);
        Assert.Equal(expected, result);
    }

    [Fact]
    public void FormatWinRate_ZeroTotal_ReturnsZeroPercent()
    {
        var result = LotteryUtils.FormatWinRate(10, 0);
        Assert.Equal("0.00%", result);
    }

    #endregion

    #region Validation Tests - 16 tests

    [Theory]
    [InlineData("00", true)]
    [InlineData("12", true)]
    [InlineData("99", true)]
    [InlineData("0", false)]
    [InlineData("123", false)]
    [InlineData("ab", false)]
    [InlineData("", false)]
    [InlineData(null, false)]
    public void IsValidLoto_VariousInputs_ReturnsExpectedResult(string? input, bool expected)
    {
        var result = LotteryUtils.IsValidLoto(input);
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("2024001", true)]
    [InlineData("1234", true)]
    [InlineData("12345678", true)]
    [InlineData("123", false)]
    [InlineData("abc", false)]
    [InlineData("", false)]
    [InlineData(null, false)]
    public void IsValidKy_VariousInputs_ReturnsExpectedResult(string? input, bool expected)
    {
        var result = LotteryUtils.IsValidKy(input);
        Assert.Equal(expected, result);
    }

    #endregion
}
