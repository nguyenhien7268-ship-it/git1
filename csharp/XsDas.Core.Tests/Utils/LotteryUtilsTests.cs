using XsDas.Core.Utils;

namespace XsDas.Core.Tests.Utils;

/// <summary>
/// Unit tests for LotteryUtils core functions.
/// Validates shadow mapping, STL generation, hit detection, and utility functions.
/// </summary>
public class LotteryUtilsTests
{
    #region Shadow Mapping Tests

    [Fact]
    public void GetBongDuong_ReturnsCorrectShadow()
    {
        // Test all shadow mappings
        Assert.Equal('5', LotteryUtils.GetBongDuong('0'));
        Assert.Equal('6', LotteryUtils.GetBongDuong('1'));
        Assert.Equal('7', LotteryUtils.GetBongDuong('2'));
        Assert.Equal('8', LotteryUtils.GetBongDuong('3'));
        Assert.Equal('9', LotteryUtils.GetBongDuong('4'));
        Assert.Equal('0', LotteryUtils.GetBongDuong('5'));
        Assert.Equal('1', LotteryUtils.GetBongDuong('6'));
        Assert.Equal('2', LotteryUtils.GetBongDuong('7'));
        Assert.Equal('3', LotteryUtils.GetBongDuong('8'));
        Assert.Equal('4', LotteryUtils.GetBongDuong('9'));
    }

    [Fact]
    public void GetBongDuong_InvalidInput_ReturnsSameCharacter()
    {
        Assert.Equal('x', LotteryUtils.GetBongDuong('x'));
        Assert.Equal('!', LotteryUtils.GetBongDuong('!'));
    }

    #endregion

    #region STL Pair Generation Tests

    [Fact]
    public void TaoStlV30Bong_DuplicateDigits_ReturnsShadowPair()
    {
        var result = LotteryUtils.TaoStlV30Bong(3, 3);
        
        Assert.Equal(2, result.Length);
        Assert.Equal("33", result[0]);
        Assert.Equal("88", result[1]); // Shadow of 3 is 8
    }

    [Fact]
    public void TaoStlV30Bong_DifferentDigits_ReturnsBothPermutations()
    {
        var result = LotteryUtils.TaoStlV30Bong(1, 2);
        
        Assert.Equal(2, result.Length);
        Assert.Equal("12", result[0]);
        Assert.Equal("21", result[1]);
    }

    [Theory]
    [InlineData("00", true)]
    [InlineData("99", true)]
    [InlineData("45", true)]
    [InlineData("12", true)]
    [InlineData("1", false)]
    [InlineData("100", false)]
    [InlineData("ab", false)]
    [InlineData("", false)]
    public void IsValidLoto_ValidatesCorrectly(string loto, bool expected)
    {
        Assert.Equal(expected, LotteryUtils.IsValidLoto(loto!));
    }

    #endregion
}
