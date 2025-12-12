using System.Linq.Expressions;

namespace XsDas.Core.Interfaces;

/// <summary>
/// Generic repository interface for data access.
/// Provides common CRUD operations for all entities.
/// </summary>
/// <typeparam name="T">Entity type</typeparam>
public interface IRepository<T> where T : class
{
    /// <summary>
    /// Get entity by ID
    /// </summary>
    Task<T?> GetByIdAsync(int id);
    
    /// <summary>
    /// Get all entities
    /// </summary>
    Task<IEnumerable<T>> GetAllAsync();
    
    /// <summary>
    /// Find entities matching predicate
    /// </summary>
    Task<IEnumerable<T>> FindAsync(Expression<Func<T, bool>> predicate);
    
    /// <summary>
    /// Add new entity
    /// </summary>
    Task<T> AddAsync(T entity);
    
    /// <summary>
    /// Add multiple entities
    /// </summary>
    Task AddRangeAsync(IEnumerable<T> entities);
    
    /// <summary>
    /// Update entity
    /// </summary>
    Task UpdateAsync(T entity);
    
    /// <summary>
    /// Delete entity
    /// </summary>
    Task DeleteAsync(T entity);
    
    /// <summary>
    /// Delete multiple entities
    /// </summary>
    Task DeleteRangeAsync(IEnumerable<T> entities);
    
    /// <summary>
    /// Count entities matching predicate
    /// </summary>
    Task<int> CountAsync(Expression<Func<T, bool>>? predicate = null);
    
    /// <summary>
    /// Check if any entity matches predicate
    /// </summary>
    Task<bool> AnyAsync(Expression<Func<T, bool>> predicate);
}
