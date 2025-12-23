using Microsoft.EntityFrameworkCore;
using XsDas.Core.Models;

namespace XsDas.Infrastructure.Data;

/// <summary>
/// Entity Framework DbContext for lottery database
/// Manages connection to SQLite database (xo_so_prizes_all_logic.db)
/// </summary>
public class LotteryDbContext : DbContext
{
    public LotteryDbContext(DbContextOptions<LotteryDbContext> options) 
        : base(options)
    {
    }

    /// <summary>
    /// Lottery results table (corresponds to results_A_I)
    /// </summary>
    public DbSet<LotteryResult> LotteryResults { get; set; }

    /// <summary>
    /// Managed bridges table (corresponds to ManagedBridges)
    /// </summary>
    public DbSet<Bridge> Bridges { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Configure LotteryResult entity
        modelBuilder.Entity<LotteryResult>(entity =>
        {
            entity.ToTable("results_A_I");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Ky).IsRequired();
            entity.HasIndex(e => e.Ky).IsUnique();
            entity.Property(e => e.Date).IsRequired();
        });

        // Configure Bridge entity
        modelBuilder.Entity<Bridge>(entity =>
        {
            entity.ToTable("ManagedBridges");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).IsRequired();
            entity.HasIndex(e => e.Name).IsUnique();
            
            // Set default values
            entity.Property(e => e.IsEnabled).HasDefaultValue(true);
            entity.Property(e => e.WinRateText).HasDefaultValue("N/A");
            entity.Property(e => e.NextPredictionStl).HasDefaultValue("N/A");
            entity.Property(e => e.SearchRateText).HasDefaultValue("0.00%");
            entity.Property(e => e.Type).HasDefaultValue("UNKNOWN");
            entity.Property(e => e.IsPending).HasDefaultValue(true);
            entity.Property(e => e.CurrentStreak).HasDefaultValue(0);
            entity.Property(e => e.MaxLoseStreakK2n).HasDefaultValue(0);
            entity.Property(e => e.RecentWinCount10).HasDefaultValue(0);
            entity.Property(e => e.SearchPeriod).HasDefaultValue(0);
            entity.Property(e => e.K1nRateLo).HasDefaultValue(0.0);
            entity.Property(e => e.K1nRateDe).HasDefaultValue(0.0);
            entity.Property(e => e.K2nRateLo).HasDefaultValue(0.0);
            entity.Property(e => e.K2nRateDe).HasDefaultValue(0.0);
            entity.Property(e => e.IsPinned).HasDefaultValue(false);
            
            // Date properties
            entity.Property(e => e.DateAdded)
                .HasDefaultValueSql("datetime('now', 'localtime')");
            entity.Property(e => e.ImportedAt)
                .HasDefaultValueSql("datetime('now', 'localtime')");
        });
    }
}
