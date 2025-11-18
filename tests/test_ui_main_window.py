# Test for DataAnalysisApp.update_output method
import os
import sys
from unittest.mock import Mock, MagicMock

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.mark.unit
def test_update_output_method_exists():
    """Test that DataAnalysisApp has the update_output method"""
    try:
        import tkinter  # noqa: F401
    except ImportError:
        pytest.skip("tkinter not available in this environment")

    # Mock tkinter components to avoid GUI creation
    import tkinter as tk
    from unittest.mock import patch

    with patch.object(tk, 'Tk'):
        with patch('ui.ui_main_window.DashboardWindow'):
            with patch('ui.ui_main_window.LookupWindow'):
                with patch('ui.ui_main_window.OptimizerTab'):
                    from ui.ui_main_window import DataAnalysisApp

                    # Create a mock root
                    mock_root = MagicMock()
                    mock_root.title = MagicMock()
                    mock_root.columnconfigure = MagicMock()
                    mock_root.rowconfigure = MagicMock()
                    mock_root.geometry = MagicMock()

                    # Create app instance
                    app = DataAnalysisApp(mock_root)

                    # Verify the method exists
                    assert hasattr(app, 'update_output'), "DataAnalysisApp should have update_output method"
                    assert callable(app.update_output), "update_output should be callable"


@pytest.mark.unit
def test_update_output_calls_logger():
    """Test that update_output properly delegates to logger.log"""
    try:
        import tkinter  # noqa: F401
    except ImportError:
        pytest.skip("tkinter not available in this environment")

    # Mock tkinter components
    import tkinter as tk
    from unittest.mock import patch

    with patch.object(tk, 'Tk'):
        with patch('ui.ui_main_window.DashboardWindow'):
            with patch('ui.ui_main_window.LookupWindow'):
                with patch('ui.ui_main_window.OptimizerTab'):
                    from ui.ui_main_window import DataAnalysisApp

                    # Create a mock root
                    mock_root = MagicMock()
                    mock_root.title = MagicMock()
                    mock_root.columnconfigure = MagicMock()
                    mock_root.rowconfigure = MagicMock()
                    mock_root.geometry = MagicMock()

                    # Create app instance
                    app = DataAnalysisApp(mock_root)

                    # Mock the logger
                    app.logger = Mock()
                    app.logger.log = Mock()

                    # Call update_output
                    test_message = "Test message"
                    app.update_output(test_message)

                    # Verify logger.log was called with the correct message
                    app.logger.log.assert_called_once_with(test_message)
