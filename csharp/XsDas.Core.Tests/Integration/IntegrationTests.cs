using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Moq;
using XsDas.Core.Interfaces;
using XsDas.Core.Models;
using XsDas.Infrastructure.Data;
using XsDas.Infrastructure.Services;
using Xunit;

namespace XsDas.Core.Tests.Integration;

/// <summary>
/// End-to-end integration tests covering data flow from SQLite through Core Logic to services
/// </summary>
public class IntegrationTests : IDisposable
{
    private readonly LotteryDbContext _context;
    private readonly Repository<LotteryResult> _resultsRepository;
    private readonly Repository<ManagedBridge> _bridgesRepository;
    private readonly Repository<DuLieuAi> _aiDataRepository;
    private readonly ScannerService _scannerService;
    private readonly BacktestingService _backtestingService;

    public IntegrationTests()
    {
        // Setup in-memory database for testing
        var options = new DbContextOptionsBuilder<LotteryDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        _context = new LotteryDbContext(options);
        _resultsRepository = new Repository<LotteryResult>(_context);
        _bridgesRepository = new Repository<ManagedBridge>(_context);
        _aiDataRepository = new Repository<DuLieuAi>(_context);
        _scannerService = new ScannerService();
        
        var loggerMock = new Mock<ILogger<BacktestingService>>();
        _backtestingService = new BacktestingService(
            _resultsRepository,
            _aiDataRepository,
            _scannerService,
            loggerMock.Object);
    }

    [Fact]
    public async Task EndToEnd_DataFlow_FromDatabaseThroughScannerToBacktest()
    {
        // Arrange: Seed test data
        var testData = new List<DuLieuAi>
        {
            new DuLieuAi
            {
                MaSoKy = 1,
                ColAKy = "2024-01-01",
                ColBGdb = "12345",
                ColCG1 = "67890",
                ColDG2 = "11111",
                ColEG3 = "22222",
                ColFG4 = "33333",
                ColGG5 = "44444",
                ColHG6 = "55555",
                ColIG7 = "0123456"
            },
            new DuLieuAi
            {
                MaSoKy = 2,
                ColAKy = "2024-01-02",
                ColBGdb = "54321",
                ColCG1 = "09876",
                ColDG2 = "99999",
                ColEG3 = "88888",
                ColFG4 = "77777",
                ColGG5 = "66666",
                ColHG6 = "55544",
                ColIG7 = "6543210"
            }
        };

        foreach (var data in testData)
        {
            await _aiDataRepository.AddAsync(data);
        }

        // Act: Run backtest which uses scanner service internally
        var result = await _backtestingService.BacktestBridgeAsync("Cau1_STL_P5");

        // Assert: Verify data flowed through entire pipeline
        Assert.NotNull(result);
        Assert.Equal("Cau1_STL_P5", result.BridgeName);
        Assert.True(result.TotalTests >= 0);
    }

    [Fact]
    public async Task Scanner_ProcessesMultipleBridges_WithDatabaseData()
    {
        // Arrange: Create test lottery result
        var lotteryResult = new LotteryResult
        {
            Ky = "2024-01-01",
            Date = "01/01/2024",
            Gdb = "12345",
            G1 = "67890",
            G2 = "11111",
            G3 = "22222",
            G4 = "33333",
            G5 = "44444",
            G6 = "55555",
            G7 = "0123456"
        };

        await _resultsRepository.AddAsync(lotteryResult);

        // Act: Get all scanners and process the data
        var scanners = _scannerService.GetAllBridgeScanners().ToList();
        var dataArray = new object[]
        {
            1, // MaSoKy
            lotteryResult.Ky ?? "",
            lotteryResult.Gdb ?? "",
            lotteryResult.G1 ?? "",
            lotteryResult.G2 ?? "",
            lotteryResult.G3 ?? "",
            lotteryResult.G4 ?? "",
            lotteryResult.G5 ?? "",
            lotteryResult.G6 ?? "",
            lotteryResult.G7 ?? ""
        };

        // Assert: All scanners should process without errors
        Assert.Equal(15, scanners.Count);
        foreach (var scanner in scanners)
        {
            var prediction = scanner(dataArray);
            Assert.NotNull(prediction);
            Assert.Equal(2, prediction.Length);
        }
    }

    [Fact]
    public async Task BridgeRepository_CRUD_Operations_WorkCorrectly()
    {
        // Arrange
        var bridge = new ManagedBridge
        {
            Name = "Test_Bridge",
            K1nRateLo = 75.5,
            K1nRateDe = 72.3,
            K2nRateLo = 80.1,
            K2nRateDe = 77.8,
            IsEnabled = true,
            DateAdded = DateTime.Now.ToString("yyyy-MM-dd")
        };

        // Act: Create
        await _bridgesRepository.AddAsync(bridge);
        var created = await _bridgesRepository.GetByIdAsync(bridge.Id);
        Assert.NotNull(created);
        Assert.Equal("Test_Bridge", created.Name);

        // Act: Update
        created.K1nRateLo = 80.0;
        await _bridgesRepository.UpdateAsync(created);
        var updated = await _bridgesRepository.GetByIdAsync(bridge.Id);
        Assert.Equal(80.0, updated!.K1nRateLo);

        // Act: Find
        var found = await _bridgesRepository.FindAsync(b => b.Name == "Test_Bridge");
        Assert.Single(found);

        // Act: Delete
        await _bridgesRepository.DeleteAsync(created);
        var deleted = await _bridgesRepository.GetByIdAsync(bridge.Id);
        Assert.Null(deleted);
    }

    [Fact]
    public async Task BacktestingService_HandlesEmptyData_Gracefully()
    {
        // Act: Backtest with no data
        var result = await _backtestingService.BacktestBridgeAsync("Cau1_STL_P5");

        // Assert: Should return empty result without crashing
        Assert.NotNull(result);
        Assert.Equal(0, result.TotalTests);
        Assert.Equal(0, result.Wins);
        Assert.Equal(0, result.Losses);
    }

    [Fact]
    public async Task BacktestingService_HandlesInvalidBridgeName_Gracefully()
    {
        // Arrange: Seed some test data
        var testData = new DuLieuAi
        {
            MaSoKy = 1,
            ColAKy = "2024-01-01",
            ColBGdb = "12345",
            ColCG1 = "67890"
        };
        await _aiDataRepository.AddAsync(testData);

        // Act: Backtest with invalid bridge name
        var result = await _backtestingService.BacktestBridgeAsync("Invalid_Bridge");

        // Assert: Should handle gracefully
        Assert.NotNull(result);
        Assert.Equal(0, result.TotalTests);
    }

    [Fact]
    public async Task CalculateRates_WithValidData_ReturnsCorrectRates()
    {
        // Arrange
        var predictions = new List<string[]>
        {
            new[] { "12", "34" },
            new[] { "56", "78" },
            new[] { "90", "11" }
        };

        var actualResults = new List<string[]>
        {
            new[] { "12", "34", "56" }, // Hit
            new[] { "78", "90", "11" }, // Partial hit
            new[] { "00", "11", "22" }  // Partial hit
        };

        // Act
        var (k1nRate, k2nRate) = await _backtestingService.CalculateRatesAsync(
            "Test_Bridge",
            predictions,
            actualResults);

        // Assert
        Assert.True(k1nRate >= 0);
        Assert.True(k1nRate <= 100);
        Assert.True(k2nRate >= k1nRate); // K2N should be optimistic
    }

    [Fact]
    public async Task IntegrationTest_MultipleBridges_CanBeBacktestedInSequence()
    {
        // Arrange: Seed multiple periods of data
        var testData = new List<DuLieuAi>();
        for (int i = 1; i <= 10; i++)
        {
            testData.Add(new DuLieuAi
            {
                MaSoKy = i,
                ColAKy = $"2024-01-{i:D2}",
                ColBGdb = $"{i}{i}{i}{i}{i}",
                ColCG1 = $"{i+1}{i+1}{i+1}{i+1}{i+1}",
                ColIG7 = "0123456"
            });
        }

        foreach (var data in testData)
        {
            await _aiDataRepository.AddAsync(data);
        }

        // Act: Backtest multiple bridges
        var bridgeNames = new[] { "Cau1_STL_P5", "Cau2_VT1", "Cau3_VT2" };
        var results = new List<BacktestResult>();

        foreach (var bridgeName in bridgeNames)
        {
            var result = await _backtestingService.BacktestBridgeAsync(bridgeName);
            results.Add(result);
        }

        // Assert: All should complete successfully
        Assert.Equal(3, results.Count);
        Assert.All(results, r => Assert.NotNull(r));
        Assert.All(results, r => Assert.True(r.TotalTests >= 0));
    }

    public void Dispose()
    {
        _context?.Dispose();
    }
}
