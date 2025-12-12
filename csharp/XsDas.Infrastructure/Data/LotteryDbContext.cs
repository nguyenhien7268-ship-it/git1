using Microsoft.EntityFrameworkCore;
using XsDas.Core.Models;

namespace XsDas.Infrastructure.Data;

/// <summary>
/// EF Core DbContext for Lottery Analytics System.
/// Provides access to SQLite database with schema compatible with Python implementation.
/// </summary>
public class LotteryDbContext : DbContext
{
    public LotteryDbContext(DbContextOptions<LotteryDbContext> options)
        : base(options)
    {
    }

    /// <summary>
    /// Lottery results (results_A_I table)
    /// </summary>
    public DbSet<LotteryResult> LotteryResults { get; set; }

    /// <summary>
    /// Managed bridges (ManagedBridges table)
    /// </summary>
    public DbSet<ManagedBridge> ManagedBridges { get; set; }

    /// <summary>
    /// AI data (DuLieu_AI table)
    /// </summary>
    public DbSet<DuLieuAi> DuLieuAi { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Configure LotteryResult entity
        modelBuilder.Entity<LotteryResult>(entity =>
        {
            entity.ToTable("results_A_I");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Ky).HasColumnName("ky").IsRequired();
            entity.Property(e => e.Date).HasColumnName("date").IsRequired();
            
            // Prize columns
            entity.Property(e => e.Gdb).HasColumnName("gdb");
            entity.Property(e => e.G1).HasColumnName("g1");
            entity.Property(e => e.G2).HasColumnName("g2");
            entity.Property(e => e.G3).HasColumnName("g3");
            entity.Property(e => e.G4).HasColumnName("g4");
            entity.Property(e => e.G5).HasColumnName("g5");
            entity.Property(e => e.G6).HasColumnName("g6");
            entity.Property(e => e.G7).HasColumnName("g7");
            
            // Lotto columns (l0-l26)
            entity.Property(e => e.L0).HasColumnName("l0");
            entity.Property(e => e.L1).HasColumnName("l1");
            entity.Property(e => e.L2).HasColumnName("l2");
            entity.Property(e => e.L3).HasColumnName("l3");
            entity.Property(e => e.L4).HasColumnName("l4");
            entity.Property(e => e.L5).HasColumnName("l5");
            entity.Property(e => e.L6).HasColumnName("l6");
            entity.Property(e => e.L7).HasColumnName("l7");
            entity.Property(e => e.L8).HasColumnName("l8");
            entity.Property(e => e.L9).HasColumnName("l9");
            entity.Property(e => e.L10).HasColumnName("l10");
            entity.Property(e => e.L11).HasColumnName("l11");
            entity.Property(e => e.L12).HasColumnName("l12");
            entity.Property(e => e.L13).HasColumnName("l13");
            entity.Property(e => e.L14).HasColumnName("l14");
            entity.Property(e => e.L15).HasColumnName("l15");
            entity.Property(e => e.L16).HasColumnName("l16");
            entity.Property(e => e.L17).HasColumnName("l17");
            entity.Property(e => e.L18).HasColumnName("l18");
            entity.Property(e => e.L19).HasColumnName("l19");
            entity.Property(e => e.L20).HasColumnName("l20");
            entity.Property(e => e.L21).HasColumnName("l21");
            entity.Property(e => e.L22).HasColumnName("l22");
            entity.Property(e => e.L23).HasColumnName("l23");
            entity.Property(e => e.L24).HasColumnName("l24");
            entity.Property(e => e.L25).HasColumnName("l25");
            entity.Property(e => e.L26).HasColumnName("l26");
            
            // Create unique index on ky
            entity.HasIndex(e => e.Ky).IsUnique();
        });

        // Configure ManagedBridge entity
        modelBuilder.Entity<ManagedBridge>(entity =>
        {
            entity.ToTable("ManagedBridges");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Name).HasColumnName("name").IsRequired();
            entity.Property(e => e.Description).HasColumnName("description");
            entity.Property(e => e.IsEnabled).HasColumnName("is_enabled").HasDefaultValue(true);
            entity.Property(e => e.DateAdded).HasColumnName("date_added");
            entity.Property(e => e.WinRateText).HasColumnName("win_rate_text").HasDefaultValue("N/A");
            entity.Property(e => e.CurrentStreak).HasColumnName("current_streak").HasDefaultValue(0);
            entity.Property(e => e.NextPredictionStl).HasColumnName("next_prediction_stl").HasDefaultValue("N/A");
            entity.Property(e => e.Pos1Idx).HasColumnName("pos1_idx");
            entity.Property(e => e.Pos2Idx).HasColumnName("pos2_idx");
            entity.Property(e => e.MaxLoseStreakK2n).HasColumnName("max_lose_streak_k2n").HasDefaultValue(0);
            entity.Property(e => e.RecentWinCount10).HasColumnName("recent_win_count_10").HasDefaultValue(0);
            entity.Property(e => e.SearchRateText).HasColumnName("search_rate_text").HasDefaultValue("0.00%");
            entity.Property(e => e.SearchPeriod).HasColumnName("search_period").HasDefaultValue(0);
            entity.Property(e => e.IsPinned).HasColumnName("is_pinned").HasDefaultValue(false);
            entity.Property(e => e.Type).HasColumnName("type").HasDefaultValue("UNKNOWN");
            
            // K1N/K2N rate columns (V11.2)
            entity.Property(e => e.K1nRateLo).HasColumnName("k1n_rate_lo").HasDefaultValue(0.0);
            entity.Property(e => e.K1nRateDe).HasColumnName("k1n_rate_de").HasDefaultValue(0.0);
            entity.Property(e => e.K2nRateLo).HasColumnName("k2n_rate_lo").HasDefaultValue(0.0);
            entity.Property(e => e.K2nRateDe).HasColumnName("k2n_rate_de").HasDefaultValue(0.0);
            entity.Property(e => e.IsPending).HasColumnName("is_pending").HasDefaultValue(true);
            entity.Property(e => e.ImportedAt).HasColumnName("imported_at");
            
            // Create unique index on name
            entity.HasIndex(e => e.Name).IsUnique();
            
            // Create index on is_enabled for faster queries
            entity.HasIndex(e => e.IsEnabled);
        });

        // Configure DuLieuAi entity
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
        });
    }
}
