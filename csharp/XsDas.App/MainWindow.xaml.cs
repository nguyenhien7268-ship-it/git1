using System.Windows;
using XsDas.App.ViewModels;

namespace XsDas.App;

/// <summary>
/// Interaction logic for MainWindow.xaml
/// </summary>
public partial class MainWindow : Window
{
    public MainWindow(DashboardViewModel dashboardViewModel, ScannerViewModel scannerViewModel)
    {
        InitializeComponent();
        
        // Set DataContexts for views
        // Note: In production, this would be done via a ViewModelLocator or more sophisticated DI
        Loaded += async (s, e) =>
        {
            await dashboardViewModel.LoadDataCommand.ExecuteAsync(null);
        };
    }
}