using Microsoft.EntityFrameworkCore;
using XsDas.Core.Models;

namespace XsDas.Infrastructure.Data;

/// <summary>
/// Entity Framework Core DbContext for Lottery Analytics
/// Ported from: logic/db_manager.py database schema
/// </summary>
public class LotteryDbContext : DbContext
{
    public LotteryDbContext(DbContextOptions<LotteryDbContext> options)
        : base(options)
    {
    }
    
    public DbSet<LotteryResult> LotteryResults { get; set; } = null!;
    public DbSet<Bridge> Bridges { get; set; } = null!;
    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        
        // Configure LotteryResult entity
        modelBuilder.Entity<LotteryResult>(entity =>
        {
            entity.ToTable("DuLieu_AI");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.MaSoKy).HasMaxLength(50).IsRequired();
            entity.Property(e => e.DrawDate).IsRequired();
            entity.Property(e => e.GiaiDacBiet).HasMaxLength(10);
            entity.Property(e => e.Giai1).HasMaxLength(10);
            entity.Property(e => e.Giai2).HasMaxLength(100);
            entity.Property(e => e.Giai3).HasMaxLength(100);
            entity.Property(e => e.Giai4).HasMaxLength(200);
            entity.Property(e => e.Giai5).HasMaxLength(200);
            entity.Property(e => e.Giai6).HasMaxLength(300);
            entity.Property(e => e.Giai7).HasMaxLength(300);
            
            entity.HasIndex(e => e.MaSoKy).IsUnique();
            entity.HasIndex(e => e.DrawDate);
        });
        
        // Configure Bridge entity
        modelBuilder.Entity<Bridge>(entity =>
        {
            entity.ToTable("ManagedBridges");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).HasMaxLength(200).IsRequired();
            entity.Property(e => e.NormalizedName).HasMaxLength(200).IsRequired();
            entity.Property(e => e.Description).HasMaxLength(500);
            entity.Property(e => e.Type).HasMaxLength(50).IsRequired();
            entity.Property(e => e.Kind).HasMaxLength(20).IsRequired();
            entity.Property(e => e.Stl).HasMaxLength(500);
            entity.Property(e => e.Reason).HasMaxLength(200);
            entity.Property(e => e.IsEnabled).IsRequired().HasDefaultValue(true);
            
            entity.HasIndex(e => e.NormalizedName).IsUnique();
            entity.HasIndex(e => e.Type);
            entity.HasIndex(e => e.IsEnabled);
            entity.HasIndex(e => new { e.Type, e.IsEnabled });
        });
    }
}
