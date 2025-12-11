using Microsoft.EntityFrameworkCore;
using XsDas.Core.Interfaces;
using XsDas.Core.Models;
using XsDas.Infrastructure.Data;

namespace XsDas.Infrastructure.Repositories;

/// <summary>
/// Repository implementation for Bridge entities
/// Ported from: logic/data_repository.py and logic/db_manager.py
/// </summary>
public class BridgeRepository : IBridgeRepository
{
    private readonly LotteryDbContext _context;
    
    public BridgeRepository(LotteryDbContext context)
    {
        _context = context;
    }
    
    public async Task<Bridge?> GetByIdAsync(int id)
    {
        return await _context.Bridges.FindAsync(id);
    }
    
    public async Task<IEnumerable<Bridge>> GetAllAsync()
    {
        return await _context.Bridges.ToListAsync();
    }
    
    public async Task<Bridge> AddAsync(Bridge entity)
    {
        _context.Bridges.Add(entity);
        await _context.SaveChangesAsync();
        return entity;
    }
    
    public async Task UpdateAsync(Bridge entity)
    {
        _context.Bridges.Update(entity);
        await _context.SaveChangesAsync();
    }
    
    public async Task DeleteAsync(int id)
    {
        var entity = await GetByIdAsync(id);
        if (entity != null)
        {
            _context.Bridges.Remove(entity);
            await _context.SaveChangesAsync();
        }
    }
    
    public async Task<IEnumerable<Bridge>> GetEnabledBridgesAsync()
    {
        return await _context.Bridges
            .Where(b => b.IsEnabled)
            .ToListAsync();
    }
    
    public async Task<IEnumerable<Bridge>> GetBridgesByTypeAsync(string type)
    {
        return await _context.Bridges
            .Where(b => b.Type.Contains(type))
            .ToListAsync();
    }
    
    public async Task<Bridge?> GetByNameAsync(string name)
    {
        return await _context.Bridges
            .FirstOrDefaultAsync(b => b.Name == name);
    }
    
    public async Task<IEnumerable<string>> GetAllBridgeNamesAsync()
    {
        return await _context.Bridges
            .Select(b => b.Name)
            .ToListAsync();
    }
    
    public async Task<bool> ExistsByNameAsync(string normalizedName)
    {
        return await _context.Bridges
            .AnyAsync(b => b.NormalizedName == normalizedName);
    }
    
    public async Task<int> BulkAddAsync(IEnumerable<Bridge> bridges)
    {
        var bridgeList = bridges.ToList();
        await _context.Bridges.AddRangeAsync(bridgeList);
        return await _context.SaveChangesAsync();
    }
    
    public async Task<int> DisableLowPerformingBridgesAsync(double threshold)
    {
        var lowPerformers = await _context.Bridges
            .Where(b => b.IsEnabled && 
                       ((b.Type.Contains("LO") && b.K1nRateLo < threshold) ||
                        (b.Type.Contains("DE") && b.K1nRateDe < threshold)))
            .ToListAsync();
        
        foreach (var bridge in lowPerformers)
        {
            bridge.IsEnabled = false;
        }
        
        return await _context.SaveChangesAsync();
    }
}
