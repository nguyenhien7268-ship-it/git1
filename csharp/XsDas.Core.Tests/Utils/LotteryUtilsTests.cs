using Xunit;
using XsDas.Core.Utils;

namespace XsDas.Core.Tests.Utils;

/// <summary>
/// Unit tests for LotteryUtils
/// Verifies mathematical accuracy against Python implementation
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
    
    [Theory]
    [InlineData(1, 2, new[] { "12", "21" })] // Different digits
    [InlineData(3, 8, new[] { "38", "83" })] // Different digits
    [InlineData(0, 5, new[] { "05", "50" })] // Different digits
    [InlineData(3, 3, new[] { "33", "88" })] // Same digit (kep) - 3's shadow is 8
    [InlineData(0, 0, new[] { "00", "55" })] // Same digit (kep) - 0's shadow is 5
    [InlineData(9, 9, new[] { "99", "44" })] // Same digit (kep) - 9's shadow is 4
    public void CreateStlWithShadow_ReturnsCorrectPairs(int a, int b, string[] expected)
    {
        // Act
        var result = LotteryUtils.CreateStlWithShadow(a, b);
        
        // Assert
        Assert.Equal(expected.Length, result.Count);
        Assert.Equal(expected[0], result[0]);
        Assert.Equal(expected[1], result[1]);
    }
    
    [Fact]
    public void CheckHitSet_BothHit_ReturnsCorrectMessage()
    {
        // Arrange
        var stlPair = new List<string> { "12", "21" };
        var lotoSet = new HashSet<string> { "12", "21", "34" };
        
        // Act
        var result = LotteryUtils.CheckHitSet(stlPair, lotoSet);
        
        // Assert
        Assert.Equal("✅ (Ăn 2)", result);
    }
    
    [Fact]
    public void CheckHitSet_OneHit_ReturnsCorrectMessage()
    {
        // Arrange
        var stlPair = new List<string> { "12", "21" };
        var lotoSet = new HashSet<string> { "12", "34" };
        
        // Act
        var result = LotteryUtils.CheckHitSet(stlPair, lotoSet);
        
        // Assert
        Assert.Equal("✅ (Ăn 1)", result);
    }
    
    [Fact]
    public void CheckHitSet_NoHit_ReturnsCorrectMessage()
    {
        // Arrange
        var stlPair = new List<string> { "12", "21" };
        var lotoSet = new HashSet<string> { "34", "56" };
        
        // Act
        var result = LotteryUtils.CheckHitSet(stlPair, lotoSet);
        
        // Assert
        Assert.Equal("❌", result);
    }
    
    [Theory]
    [InlineData("Test-Bridge-01", "testbridge01")]
    [InlineData("LO_STL_FIXED_01", "lostlfixed01")]
    [InlineData("Cầu [Bộ] (G7+5)", "caubog75")]
    [InlineData("Test  _  Bridge", "testbridge")]
    public void NormalizeBridgeName_ReturnsNormalizedString(string input, string expected)
    {
        // Act
        var result = LotteryUtils.NormalizeBridgeName(input);
        
        // Assert
        Assert.Equal(expected, result);
    }
    
    [Fact]
    public void CalculateStrictPerformance_WithPerfectStreak_ReturnsCorrectMetrics()
    {
        // Arrange
        var results = new List<bool> { true, true, true, true, true, false, false };
        
        // Act
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        
        // Assert
        Assert.Equal(5, metrics.Streak); // First 5 are wins
        Assert.Equal(5, metrics.TotalWins);
        Assert.Equal(71.43, metrics.WinRate, 2); // 5/7 * 100 = 71.43%
        Assert.Equal(5, metrics.Wins10); // All within first 10
        Assert.Equal(7, metrics.TotalDays);
    }
    
    [Fact]
    public void CalculateStrictPerformance_WithBrokenStreak_ReturnsCorrectMetrics()
    {
        // Arrange
        var results = new List<bool> { true, true, false, true, true, true };
        
        // Act
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        
        // Assert
        Assert.Equal(2, metrics.Streak); // Broken after 2nd result
        Assert.Equal(5, metrics.TotalWins);
        Assert.Equal(83.33, metrics.WinRate, 2); // 5/6 * 100 = 83.33%
        Assert.Equal(5, metrics.Wins10);
        Assert.Equal(6, metrics.TotalDays);
    }
    
    [Fact]
    public void CalculateStrictPerformance_WithAllLosses_ReturnsZeroStreak()
    {
        // Arrange
        var results = new List<bool> { false, false, false };
        
        // Act
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        
        // Assert
        Assert.Equal(0, metrics.Streak);
        Assert.Equal(0, metrics.TotalWins);
        Assert.Equal(0, metrics.WinRate);
        Assert.Equal(0, metrics.Wins10);
        Assert.Equal(3, metrics.TotalDays);
    }
    
    [Fact]
    public void CalculateStrictPerformance_With12Results_CalculatesWins10Correctly()
    {
        // Arrange - First 10 have 7 wins, last 2 have 1 win
        var results = new List<bool> 
        { 
            true, true, false, true, true, 
            false, true, true, false, true,  // 7 wins in first 10
            false, true                       // 1 more win
        };
        
        // Act
        var metrics = LotteryUtils.CalculateStrictPerformance(results);
        
        // Assert
        Assert.Equal(2, metrics.Streak); // First TWO results are true
        Assert.Equal(8, metrics.TotalWins);
        Assert.Equal(66.67, metrics.WinRate, 2); // 8/12 * 100
        Assert.Equal(7, metrics.Wins10); // 7 wins in first 10 results
        Assert.Equal(12, metrics.TotalDays);
    }
}
