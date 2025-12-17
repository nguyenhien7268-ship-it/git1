using Microsoft.EntityFrameworkCore;
using XsDas.Core.Interfaces;
using XsDas.Core.Models;
using XsDas.Infrastructure.Data;

namespace XsDas.Infrastructure.Repositories;

/// <summary>
/// Repository implementation for LotteryResult entities
/// </summary>
public class LotteryResultRepository : ILotteryResultRepository
{
    private readonly LotteryDbContext _context;
    
    public LotteryResultRepository(LotteryDbContext context)
    {
        _context = context;
    }
    
    public async Task<LotteryResult?> GetByIdAsync(int id)
    {
        return await _context.LotteryResults.FindAsync(id);
    }
    
    public async Task<IEnumerable<LotteryResult>> GetAllAsync()
    {
        return await _context.LotteryResults
            .OrderByDescending(r => r.DrawDate)
            .ToListAsync();
    }
    
    public async Task<LotteryResult> AddAsync(LotteryResult entity)
    {
        _context.LotteryResults.Add(entity);
        await _context.SaveChangesAsync();
        return entity;
    }
    
    public async Task UpdateAsync(LotteryResult entity)
    {
        _context.LotteryResults.Update(entity);
        await _context.SaveChangesAsync();
    }
    
    public async Task DeleteAsync(int id)
    {
        var entity = await GetByIdAsync(id);
        if (entity != null)
        {
            _context.LotteryResults.Remove(entity);
            await _context.SaveChangesAsync();
        }
    }
    
    public async Task<IEnumerable<LotteryResult>> GetRecentResultsAsync(int count)
    {
        return await _context.LotteryResults
            .OrderByDescending(r => r.DrawDate)
            .Take(count)
            .ToListAsync();
    }
    
    public async Task<LotteryResult?> GetByMaSoKyAsync(string maSoKy)
    {
        return await _context.LotteryResults
            .FirstOrDefaultAsync(r => r.MaSoKy == maSoKy);
    }
    
    public async Task<IEnumerable<LotteryResult>> GetResultsInDateRangeAsync(
        DateTime startDate, 
        DateTime endDate)
    {
        return await _context.LotteryResults
            .Where(r => r.DrawDate >= startDate && r.DrawDate <= endDate)
            .OrderByDescending(r => r.DrawDate)
            .ToListAsync();
    }
}
