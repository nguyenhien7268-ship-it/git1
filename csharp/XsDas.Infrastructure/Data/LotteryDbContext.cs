using Microsoft.EntityFrameworkCore;
using XsDas.Core.Models;

namespace XsDas.Infrastructure.Data;

/// <summary>
/// Entity Framework Core DbContext for Lottery database
/// </summary>
public class LotteryDbContext : DbContext
{
    public LotteryDbContext(DbContextOptions<LotteryDbContext> options) : base(options)
    {
    }

    public DbSet<LotteryResult> LotteryResults { get; set; } = null!;
    public DbSet<ManagedBridge> ManagedBridges { get; set; } = null!;
    public DbSet<DuLieuAi> DuLieuAiData { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Configure LotteryResult
        modelBuilder.Entity<LotteryResult>(entity =>
        {
            entity.ToTable("results_A_I");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Ky).HasColumnName("ky").IsRequired();
            entity.HasIndex(e => e.Ky).IsUnique();
            
            entity.Property(e => e.Date).HasColumnName("date");
            entity.Property(e => e.Gdb).HasColumnName("gdb");
            entity.Property(e => e.G1).HasColumnName("g1");
            entity.Property(e => e.G2).HasColumnName("g2");
            entity.Property(e => e.G3).HasColumnName("g3");
            entity.Property(e => e.G4).HasColumnName("g4");
            entity.Property(e => e.G5).HasColumnName("g5");
            entity.Property(e => e.G6).HasColumnName("g6");
            entity.Property(e => e.G7).HasColumnName("g7");
            
            // Map loto columns
            for (int i = 0; i <= 26; i++)
            {
                entity.Property($"L{i}").HasColumnName($"l{i}");
            }
        });

        // Configure ManagedBridge
        modelBuilder.Entity<ManagedBridge>(entity =>
        {
            entity.ToTable("ManagedBridges");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Name).HasColumnName("name").IsRequired();
            entity.HasIndex(e => e.Name).IsUnique();
            
            entity.Property(e => e.Description).HasColumnName("description");
            entity.Property(e => e.IsEnabled).HasColumnName("is_enabled");
            entity.Property(e => e.DateAdded).HasColumnName("date_added");
            entity.Property(e => e.WinRateText).HasColumnName("win_rate_text");
            entity.Property(e => e.CurrentStreak).HasColumnName("current_streak");
            entity.Property(e => e.NextPredictionStl).HasColumnName("next_prediction_stl");
            entity.Property(e => e.Pos1Idx).HasColumnName("pos1_idx");
            entity.Property(e => e.Pos2Idx).HasColumnName("pos2_idx");
            entity.Property(e => e.MaxLoseStreakK2n).HasColumnName("max_lose_streak_k2n");
            entity.Property(e => e.RecentWinCount10).HasColumnName("recent_win_count_10");
            entity.Property(e => e.SearchRateText).HasColumnName("search_rate_text");
            entity.Property(e => e.SearchPeriod).HasColumnName("search_period");
            entity.Property(e => e.IsPinned).HasColumnName("is_pinned");
            entity.Property(e => e.Type).HasColumnName("type");
            entity.Property(e => e.K1nRateLo).HasColumnName("k1n_rate_lo");
            entity.Property(e => e.K1nRateDe).HasColumnName("k1n_rate_de");
            entity.Property(e => e.K2nRateLo).HasColumnName("k2n_rate_lo");
            entity.Property(e => e.K2nRateDe).HasColumnName("k2n_rate_de");
            entity.Property(e => e.IsPending).HasColumnName("is_pending");
            entity.Property(e => e.ImportedAt).HasColumnName("imported_at");
            
            entity.HasIndex(e => e.IsEnabled);
        });

        // Configure DuLieuAi
        modelBuilder.Entity<DuLieuAi>(entity =>
        {
            entity.ToTable("DuLieu_AI");
            entity.HasKey(e => e.MaSoKy);
            entity.Property(e => e.MaSoKy).HasColumnName("MaSoKy");
            entity.Property(e => e.ColAKy).HasColumnName("Col_A_Ky");
            entity.Property(e => e.ColBGdb).HasColumnName("Col_B_GDB");
            entity.Property(e => e.ColCG1).HasColumnName("Col_C_G1");
            entity.Property(e => e.ColDG2).HasColumnName("Col_D_G2");
            entity.Property(e => e.ColEG3).HasColumnName("Col_E_G3");
            entity.Property(e => e.ColFG4).HasColumnName("Col_F_G4");
            entity.Property(e => e.ColGG5).HasColumnName("Col_G_G5");
            entity.Property(e => e.ColHG6).HasColumnName("Col_H_G6");
            entity.Property(e => e.ColIG7).HasColumnName("Col_I_G7");
            
            entity.HasIndex(e => e.MaSoKy);
        });
    }
}
