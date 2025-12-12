using System.Diagnostics;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Moq;
using XsDas.Core.Models;
using XsDas.Infrastructure.Data;
using XsDas.Infrastructure.Services;
using Xunit;
using Xunit.Abstractions;

namespace XsDas.Core.Tests.Performance;

/// <summary>
/// Performance benchmarks testing system throughput under load
/// Simulates 10,000+ records to evaluate SQLite, Core Logic, and Dashboard responsiveness
/// </summary>
public class PerformanceBenchmarks : IDisposable
{
    private readonly ITestOutputHelper _output;
    private readonly LotteryDbContext _context;
    private readonly Repository<DuLieuAi> _aiDataRepository;
    private readonly Repository<ManagedBridge> _bridgesRepository;
    private readonly ScannerService _scannerService;
    private readonly BacktestingService _backtestingService;

    public PerformanceBenchmarks(ITestOutputHelper output)
    {
        _output = output;
        
        var options = new DbContextOptionsBuilder<LotteryDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        _context = new LotteryDbContext(options);
        _aiDataRepository = new Repository<DuLieuAi>(_context);
        _bridgesRepository = new Repository<ManagedBridge>(_context);
        _scannerService = new ScannerService();
        
        var loggerMock = new Mock<ILogger<BacktestingService>>();
        _backtestingService = new BacktestingService(
            new Repository<LotteryResult>(_context),
            _aiDataRepository,
            _scannerService,
            loggerMock.Object);
    }

    [Fact]
    public async Task Benchmark_SQLite_BulkWrite_10000Records()
    {
        // Arrange
        var records = GenerateTestData(10000);
        var stopwatch = Stopwatch.StartNew();

        // Act: Bulk insert
        foreach (var record in records)
        {
            await _aiDataRepository.AddAsync(record);
        }

        stopwatch.Stop();

        // Assert & Report
        _output.WriteLine($"SQLite Bulk Write (10,000 records): {stopwatch.ElapsedMilliseconds}ms");
        _output.WriteLine($"Average: {stopwatch.ElapsedMilliseconds / 10000.0:F3}ms per record");
        
        Assert.True(stopwatch.ElapsedMilliseconds < 30000, 
            "Bulk write should complete within 30 seconds");
    }

    [Fact]
    public async Task Benchmark_SQLite_BulkRead_10000Records()
    {
        // Arrange: Insert test data
        var records = GenerateTestData(10000);
        foreach (var record in records)
        {
            await _aiDataRepository.AddAsync(record);
        }

        var stopwatch = Stopwatch.StartNew();

        // Act: Bulk read
        var allRecords = await _aiDataRepository.GetAllAsync();
        var recordsList = allRecords.ToList();

        stopwatch.Stop();

        // Assert & Report
        _output.WriteLine($"SQLite Bulk Read (10,000 records): {stopwatch.ElapsedMilliseconds}ms");
        _output.WriteLine($"Records retrieved: {recordsList.Count}");
        
        Assert.Equal(10000, recordsList.Count);
        Assert.True(stopwatch.ElapsedMilliseconds < 5000, 
            "Bulk read should complete within 5 seconds");
    }

    [Fact]
    public void Benchmark_CoreLogic_ScannerThroughput_1000Iterations()
    {
        // Arrange
        var testData = new object[]
        {
            1, "2024-01-01", "12345", "67890", "11111", "22222", "33333", "44444", "55555", "0123456"
        };

        var stopwatch = Stopwatch.StartNew();

        // Act: Run all scanners 1000 times
        for (int i = 0; i < 1000; i++)
        {
            foreach (var scanner in _scannerService.GetAllBridgeScanners())
            {
                var result = scanner(testData);
            }
        }

        stopwatch.Stop();

        // Assert & Report
        var totalOperations = 1000 * 15; // 15 scanners
        _output.WriteLine($"Scanner Throughput (15,000 operations): {stopwatch.ElapsedMilliseconds}ms");
        _output.WriteLine($"Average: {stopwatch.ElapsedMilliseconds / (double)totalOperations:F3}ms per scan");
        _output.WriteLine($"Throughput: {totalOperations * 1000.0 / stopwatch.ElapsedMilliseconds:F0} ops/sec");
        
        Assert.True(stopwatch.ElapsedMilliseconds < 5000, 
            "15,000 scanner operations should complete within 5 seconds");
    }

    [Fact]
    public async Task Benchmark_Backtesting_LargeDataset_1000Periods()
    {
        // Arrange: Create 1000 periods of data
        var testData = GenerateTestData(1000);
        foreach (var record in testData)
        {
            await _aiDataRepository.AddAsync(record);
        }

        var stopwatch = Stopwatch.StartNew();

        // Act: Run backtest
        var result = await _backtestingService.BacktestBridgeAsync("Cau1_STL_P5");

        stopwatch.Stop();

        // Assert & Report
        _output.WriteLine($"Backtesting (1,000 periods): {stopwatch.ElapsedMilliseconds}ms");
        _output.WriteLine($"Tests performed: {result.TotalTests}");
        _output.WriteLine($"Average: {stopwatch.ElapsedMilliseconds / (double)result.TotalTests:F3}ms per test");
        
        Assert.True(stopwatch.ElapsedMilliseconds < 10000, 
            "Backtesting 1000 periods should complete within 10 seconds");
    }

    [Fact]
    public async Task Benchmark_Database_QueryPerformance_ComplexFilter()
    {
        // Arrange: Insert test data with varying K1N rates
        var bridges = new List<ManagedBridge>();
        for (int i = 0; i < 1000; i++)
        {
            bridges.Add(new ManagedBridge
            {
                Name = $"Bridge_{i}",
                K1nRateLo = 50 + (i % 50),
                K1nRateDe = 45 + (i % 50),
                IsEnabled = i % 2 == 0,
                DateAdded = DateTime.Now.AddDays(-i).ToString("yyyy-MM-dd")
            });
        }

        foreach (var bridge in bridges)
        {
            await _bridgesRepository.AddAsync(bridge);
        }

        var stopwatch = Stopwatch.StartNew();

        // Act: Complex query with filtering
        var cutoffDate = DateTime.Now.AddDays(-30).ToString("yyyy-MM-dd");
        var filteredBridges = await _bridgesRepository.FindAsync(b => 
            b.IsEnabled && 
            b.K1nRateLo >= 70 && 
            string.Compare(b.DateAdded, cutoffDate) > 0);

        var resultList = filteredBridges.ToList();

        stopwatch.Stop();

        // Assert & Report
        _output.WriteLine($"Complex Query (1,000 records): {stopwatch.ElapsedMilliseconds}ms");
        _output.WriteLine($"Filtered results: {resultList.Count}");
        
        Assert.True(stopwatch.ElapsedMilliseconds < 1000, 
            "Complex query should complete within 1 second");
    }

    [Fact]
    public async Task Benchmark_ConcurrentOperations_MultipleServices()
    {
        // Arrange
        var testData = GenerateTestData(100);
        foreach (var record in testData)
        {
            await _aiDataRepository.AddAsync(record);
        }

        var stopwatch = Stopwatch.StartNew();

        // Act: Run multiple operations concurrently
        var tasks = new List<Task>
        {
            _backtestingService.BacktestBridgeAsync("Cau1_STL_P5"),
            _backtestingService.BacktestBridgeAsync("Cau2_VT1"),
            _backtestingService.BacktestBridgeAsync("Cau3_VT2"),
            Task.Run(() => _scannerService.GetAllBridgeScanners().ToList()),
            _aiDataRepository.GetAllAsync()
        };

        await Task.WhenAll(tasks);

        stopwatch.Stop();

        // Assert & Report
        _output.WriteLine($"Concurrent Operations (5 tasks): {stopwatch.ElapsedMilliseconds}ms");
        
        Assert.True(stopwatch.ElapsedMilliseconds < 5000, 
            "Concurrent operations should complete within 5 seconds");
    }

    [Fact]
    public void Benchmark_MemoryUsage_ScannerService()
    {
        // Arrange
        var initialMemory = GC.GetTotalMemory(true);

        // Act: Create many scanner instances and process data
        for (int i = 0; i < 1000; i++)
        {
            var testData = new object[]
            {
                i, $"2024-01-{i:D2}", "12345", "67890", "11111", "22222", "33333", "44444", "55555", "0123456"
            };

            foreach (var scanner in _scannerService.GetAllBridgeScanners())
            {
                var result = scanner(testData);
            }
        }

        // Force garbage collection to measure actual memory
        GC.Collect();
        GC.WaitForPendingFinalizers();
        GC.Collect();

        var finalMemory = GC.GetTotalMemory(true);
        var memoryUsed = (finalMemory - initialMemory) / 1024.0 / 1024.0; // MB

        // Report
        _output.WriteLine($"Memory Usage (1,000 iterations): {memoryUsed:F2} MB");
        _output.WriteLine($"Initial Memory: {initialMemory / 1024.0 / 1024.0:F2} MB");
        _output.WriteLine($"Final Memory: {finalMemory / 1024.0 / 1024.0:F2} MB");
        
        Assert.True(memoryUsed < 50, 
            "Memory usage should be less than 50 MB for 1000 iterations");
    }

    private List<DuLieuAi> GenerateTestData(int count)
    {
        var data = new List<DuLieuAi>();
        var random = new Random(42); // Fixed seed for reproducibility

        for (int i = 0; i < count; i++)
        {
            data.Add(new DuLieuAi
            {
                MaSoKy = i + 1,
                ColAKy = $"2024-{(i % 12) + 1:D2}-{(i % 28) + 1:D2}",
                ColBGdb = GenerateRandomNumber(random, 5),
                ColCG1 = GenerateRandomNumber(random, 5),
                ColDG2 = GenerateRandomNumber(random, 5),
                ColEG3 = GenerateRandomNumber(random, 5),
                ColFG4 = GenerateRandomNumber(random, 5),
                ColGG5 = GenerateRandomNumber(random, 5),
                ColHG6 = GenerateRandomNumber(random, 5),
                ColIG7 = GenerateRandomNumber(random, 7)
            });
        }

        return data;
    }

    private string GenerateRandomNumber(Random random, int length)
    {
        return string.Join("", Enumerable.Range(0, length).Select(_ => random.Next(0, 10)));
    }

    public void Dispose()
    {
        _context?.Dispose();
    }
}
