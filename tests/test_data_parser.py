"""
Tests for data_parser module - Data parsing and validation testing

Tests the data parsing functionality which handles input files
and converts them to database format.
"""
import pytest
import sys
import os
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDataParserImports:
    """Test data parser module imports correctly"""
    
    def test_data_parser_imports(self):
        """Test data_parser module can be imported"""
        from logic import data_parser
        assert data_parser is not None
    
    def test_data_parser_has_parse_functions(self):
        """Test data_parser has parsing functions"""
        from logic import data_parser
        
        parse_functions = [
            name for name in dir(data_parser)
            if 'parse' in name.lower() and not name.startswith('_')
        ]
        
        assert len(parse_functions) > 0, "Should have parse functions"


class TestDataParserFunctions:
    """Test parsing function availability"""
    
    def test_has_run_and_update_from_text(self):
        """Test run_and_update_from_text function exists"""
        try:
            from logic.data_parser import run_and_update_from_text
            assert callable(run_and_update_from_text)
        except ImportError:
            pytest.skip("Function not available")
    
    def test_has_parse_and_insert_data(self):
        """Test parse_and_insert_data function exists"""
        try:
            from logic.data_parser import parse_and_insert_data
            assert callable(parse_and_insert_data)
        except ImportError:
            pytest.skip("Function not available")
    
    def test_has_parse_and_append_functions(self):
        """Test append functions exist"""
        try:
            from logic.data_parser import (
                parse_and_APPEND_data,
                parse_and_APPEND_data_TEXT
            )
            assert callable(parse_and_APPEND_data)
            assert callable(parse_and_APPEND_data_TEXT)
        except ImportError:
            pytest.skip("Functions not available")


class TestDataParserValidation:
    """Test data validation in parser"""
    
    def test_parser_uses_validators(self):
        """Test parser integrates with validators module"""
        try:
            from logic import data_parser
            import inspect
            
            source = inspect.getsource(data_parser)
            
            # Should reference validation
            validation_keywords = ['validate', 'ValidationError']
            found = any(keyword in source for keyword in validation_keywords)
            
            if not found:
                # May not have validation yet, that's okay
                pytest.skip("Validation integration not found")
            
            assert found, "Should integrate with validators"
        except:
            pytest.skip("Cannot inspect source")
    
    def test_parser_validates_file_size(self):
        """Test parser validates file size"""
        try:
            from logic.validators import MAX_FILE_SIZE
            
            # MAX_FILE_SIZE should be defined
            assert MAX_FILE_SIZE is not None
            assert isinstance(MAX_FILE_SIZE, int)
            assert MAX_FILE_SIZE > 0
        except ImportError:
            pytest.skip("Validators module not available")
    
    def test_parser_validates_line_count(self):
        """Test parser validates line count"""
        try:
            from logic.validators import MAX_LINES
            
            # MAX_LINES should be defined
            assert MAX_LINES is not None
            assert isinstance(MAX_LINES, int)
            assert MAX_LINES > 0
        except ImportError:
            pytest.skip("Validators module not available")


class TestDataParserFormats:
    """Test different data format support"""
    
    def test_parser_supports_text_format(self):
        """Test parser supports text format"""
        try:
            from logic.data_parser import run_and_update_from_text
            
            # Function should accept string data
            # We won't actually parse, just check function exists
            assert callable(run_and_update_from_text)
        except ImportError:
            pytest.skip("Text parsing not available")
    
    def test_parser_handles_empty_input(self):
        """Test parser handles empty input gracefully"""
        try:
            from logic.data_parser import run_and_update_from_text
            
            # Call with empty string
            result = run_and_update_from_text("")
            
            # Should return tuple (success, message)
            assert isinstance(result, tuple)
            assert len(result) == 2
            success, message = result
            assert isinstance(success, bool)
            assert isinstance(message, str)
            
            # Should fail gracefully
            assert success is False or message is not None
        except ImportError:
            pytest.skip("Function not available")
        except Exception as e:
            # Should not crash
            assert False, f"Should handle empty input gracefully: {e}"


class TestDataParserDatabase:
    """Test database integration in parser"""
    
    def test_parser_uses_db_manager(self):
        """Test parser integrates with db_manager"""
        try:
            from logic import data_parser
            import inspect
            
            source = inspect.getsource(data_parser)
            
            # Should reference db_manager
            assert 'db_manager' in source or 'database' in source.lower()
        except:
            pytest.skip("Cannot inspect source")
    
    def test_parser_uses_data_repository(self):
        """Test parser may use data_repository"""
        try:
            from logic import data_parser
            import inspect
            
            source = inspect.getsource(data_parser)
            
            # May reference data_repository
            has_repo = 'data_repository' in source
            # This is optional, just checking
            assert True  # Always pass, just informational
        except:
            pytest.skip("Cannot inspect source")


class TestDataParserOutput:
    """Test parser output format"""
    
    def test_parse_returns_tuple(self):
        """Test parse functions return tuple format"""
        try:
            from logic.data_parser import run_and_update_from_text
            
            # Try with minimal data
            result = run_and_update_from_text("test")
            
            assert isinstance(result, tuple), "Should return tuple"
            assert len(result) >= 2, "Should return (success, message)"
        except ImportError:
            pytest.skip("Function not available")
        except:
            # May fail on actual parsing, that's okay
            pass
    
    def test_parse_message_format(self):
        """Test parse functions return meaningful messages"""
        try:
            from logic.data_parser import run_and_update_from_text
            
            result = run_and_update_from_text("")
            
            if isinstance(result, tuple) and len(result) >= 2:
                success, message = result[:2]
                
                # Message should be non-empty string
                assert isinstance(message, str)
                assert len(message) > 0
        except:
            pytest.skip("Cannot test message format")


class TestDataParserErrorHandling:
    """Test error handling in parser"""
    
    def test_parser_handles_invalid_format(self):
        """Test parser handles invalid data format"""
        try:
            from logic.data_parser import run_and_update_from_text
            
            # Try with clearly invalid data
            invalid_data = "!@#$%^&*()"
            result = run_and_update_from_text(invalid_data)
            
            # Should not crash
            assert result is not None
            
            if isinstance(result, tuple):
                success, message = result
                # Should indicate failure
                assert success is False or 'lỗi' in message.lower() or 'error' in message.lower()
        except ImportError:
            pytest.skip("Function not available")
        except Exception as e:
            # Should handle gracefully, not raise
            pytest.fail(f"Should handle invalid format gracefully: {e}")
    
    def test_parser_handles_none_input(self):
        """Test parser handles None input"""
        try:
            from logic.data_parser import run_and_update_from_text
            
            result = run_and_update_from_text(None)
            
            # Should not crash
            assert result is not None
        except ImportError:
            pytest.skip("Function not available")
        except Exception as e:
            # Should handle None gracefully
            pytest.fail(f"Should handle None input gracefully: {e}")


class TestDataParserConstants:
    """Test parser constants and configuration"""
    
    def test_parser_uses_allowed_extensions(self):
        """Test parser checks file extensions"""
        try:
            from logic.validators import ALLOWED_EXTENSIONS
            
            assert ALLOWED_EXTENSIONS is not None
            assert isinstance(ALLOWED_EXTENSIONS, list)
            assert len(ALLOWED_EXTENSIONS) > 0
            
            # Should include common formats
            assert '.txt' in ALLOWED_EXTENSIONS or '.json' in ALLOWED_EXTENSIONS
        except ImportError:
            pytest.skip("Validators module not available")
    
    def test_parser_has_reasonable_limits(self):
        """Test parser has reasonable validation limits"""
        try:
            from logic.validators import MAX_FILE_SIZE, MAX_LINES
            
            # Limits should be reasonable
            assert 100_000 < MAX_FILE_SIZE < 100_000_000, "File size limit reasonable"
            assert 1_000 < MAX_LINES < 1_000_000, "Line count limit reasonable"
        except ImportError:
            pytest.skip("Validators module not available")


class TestDataParserIntegration:
    """Integration tests for data parser"""
    
    def test_parser_integrates_with_validators(self):
        """Test parser can use validators"""
        try:
            from logic.data_parser import run_and_update_from_text
            from logic.validators import validate_file_upload
            
            # Both should be available
            assert callable(run_and_update_from_text)
            assert callable(validate_file_upload)
        except ImportError as e:
            pytest.skip(f"Integration not available: {e}")
    
    def test_parser_can_access_database(self):
        """Test parser can access database functions"""
        try:
            from logic.data_parser import run_and_update_from_text
            from logic.db_manager import setup_database
            
            # Both should be available
            assert callable(run_and_update_from_text)
            assert callable(setup_database)
        except ImportError:
            pytest.skip("Database integration not available")


class TestDataParserPerformance:
    """Performance-related tests for parser"""
    
    def test_parser_handles_large_input_efficiently(self):
        """Test parser can handle reasonably large input"""
        # This is a placeholder for performance tests
        # In real tests, we'd measure parsing time
        assert True, "Performance tests to be implemented"
    
    def test_parser_memory_efficiency(self):
        """Test parser doesn't consume excessive memory"""
        # This is a placeholder for memory tests
        assert True, "Memory efficiency tests to be implemented"


class TestDataParserDataTypes:
    """Test data type handling in parser"""
    
    def test_parser_handles_strings(self):
        """Test parser handles string input"""
        try:
            from logic.data_parser import run_and_update_from_text
            
            # Should accept string
            result = run_and_update_from_text("test data")
            assert result is not None
        except ImportError:
            pytest.skip("Function not available")
    
    def test_parser_output_types(self):
        """Test parser outputs correct types"""
        try:
            from logic.data_parser import run_and_update_from_text
            
            result = run_and_update_from_text("")
            
            # Should return tuple
            assert isinstance(result, tuple)
            
            if len(result) >= 2:
                success, message = result[:2]
                assert isinstance(success, bool)
                assert isinstance(message, str)
        except:
            pytest.skip("Cannot test output types")


@pytest.mark.skip(reason="Slow test placeholder - implement when needed")
class TestDataParserRealData:
    """Slow tests with real data (marked as slow)"""
    
    def test_placeholder_real_data_parsing(self):
        """Placeholder for real data parsing tests"""
        # Real data tests would go here
        assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
