using System.IO;
using System.Windows;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using XsDas.Core.Interfaces;
using XsDas.Infrastructure.Data;
using XsDas.Infrastructure.Services;

namespace XsDas.App;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : Application
{
    private IHost? _host;

    public App()
    {
        _host = Host.CreateDefaultBuilder()
            .ConfigureServices((context, services) =>
            {
                // Database
                var dbPath = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "XsDas", 
                    "xo_so_prizes_all_logic.db");
                
                // Ensure directory exists
                Directory.CreateDirectory(Path.GetDirectoryName(dbPath)!);
                
                services.AddDbContext<LotteryDbContext>(options =>
                    options.UseSqlite($"Data Source={dbPath}"));

                // Repositories
                services.AddScoped(typeof(IRepository<>), typeof(Repository<>));

                // Services
                services.AddScoped<ScannerService>();

                // ViewModels (if needed)
                // services.AddTransient<MainViewModel>();

                // Main Window
                services.AddSingleton<MainWindow>();
            })
            .Build();
    }

    protected override async void OnStartup(StartupEventArgs e)
    {
        await _host!.StartAsync();

        // Ensure database is created
        using (var scope = _host.Services.CreateScope())
        {
            var context = scope.ServiceProvider.GetRequiredService<LotteryDbContext>();
            await context.Database.EnsureCreatedAsync();
        }

        var mainWindow = _host.Services.GetRequiredService<MainWindow>();
        mainWindow.Show();

        base.OnStartup(e);
    }

    protected override async void OnExit(ExitEventArgs e)
    {
        if (_host != null)
        {
            await _host.StopAsync();
            _host.Dispose();
        }

        base.OnExit(e);
    }
}

