using System.Collections.Generic;
using System.Threading.Tasks;
using XsDas.Core.Models;

namespace XsDas.Core.Interfaces;

/// <summary>
/// Generic repository interface for data access
/// Implements Repository Pattern for clean architecture
/// </summary>
public interface IRepository<T> where T : class
{
    Task<T?> GetByIdAsync(int id);
    Task<IEnumerable<T>> GetAllAsync();
    Task<T> AddAsync(T entity);
    Task UpdateAsync(T entity);
    Task DeleteAsync(int id);
}

/// <summary>
/// Specialized repository for Bridge entities
/// Ported from: logic/data_repository.py and logic/db_manager.py
/// </summary>
public interface IBridgeRepository : IRepository<Bridge>
{
    Task<IEnumerable<Bridge>> GetEnabledBridgesAsync();
    Task<IEnumerable<Bridge>> GetBridgesByTypeAsync(string type);
    Task<Bridge?> GetByNameAsync(string name);
    Task<IEnumerable<string>> GetAllBridgeNamesAsync();
    Task<bool> ExistsByNameAsync(string normalizedName);
    Task<int> BulkAddAsync(IEnumerable<Bridge> bridges);
    Task<int> DisableLowPerformingBridgesAsync(double threshold);
}

/// <summary>
/// Repository for lottery results
/// </summary>
public interface ILotteryResultRepository : IRepository<LotteryResult>
{
    Task<IEnumerable<LotteryResult>> GetRecentResultsAsync(int count);
    Task<LotteryResult?> GetByMaSoKyAsync(string maSoKy);
    Task<IEnumerable<LotteryResult>> GetResultsInDateRangeAsync(DateTime startDate, DateTime endDate);
}
