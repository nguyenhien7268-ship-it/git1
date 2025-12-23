using System.Windows;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.EntityFrameworkCore;
using XsDas.Core.Interfaces;
using XsDas.Infrastructure.Data;
using XsDas.Infrastructure.Repositories;
using XsDas.Infrastructure.Services;
using XsDas.Infrastructure.Background;
using XsDas.App.ViewModels;
using XsDas.App.Views;

namespace XsDas.App;

/// <summary>
/// Interaction logic for App.xaml
/// Configures dependency injection and application lifecycle
/// </summary>
public partial class App : Application
{
    private readonly IHost _host;
    
    public App()
    {
        _host = Host.CreateDefaultBuilder()
            .ConfigureServices((context, services) =>
            {
                // Database
                services.AddDbContext<LotteryDbContext>(options =>
                    options.UseSqlite("Data Source=lottery.db"));
                
                // Repositories
                services.AddScoped<IBridgeRepository, BridgeRepository>();
                services.AddScoped<ILotteryResultRepository, LotteryResultRepository>();
                
                // Services
                services.AddScoped<IBridgeScanner, ScannerService>();
                services.AddScoped<IAnalysisService, DeAnalysisService>();
                
                // Background Services
                services.AddHostedService<BridgeBackgroundService>();
                
                // ViewModels
                services.AddTransient<DashboardViewModel>();
                services.AddTransient<ScannerViewModel>();
                
                // Views
                services.AddTransient<DashboardView>();
                services.AddTransient<ScannerView>();
                services.AddSingleton<MainWindow>();
            })
            .Build();
    }
    
    protected override async void OnStartup(StartupEventArgs e)
    {
        await _host.StartAsync();
        
        // Ensure database is created
        var dbContext = _host.Services.GetRequiredService<LotteryDbContext>();
        await dbContext.Database.EnsureCreatedAsync();
        
        var mainWindow = _host.Services.GetRequiredService<MainWindow>();
        mainWindow.Show();
        
        base.OnStartup(e);
    }
    
    protected override async void OnExit(ExitEventArgs e)
    {
        await _host.StopAsync();
        _host.Dispose();
        
        base.OnExit(e);
    }
}


