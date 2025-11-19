Testing Guidelines
==================

Guidelines for testing the Lottery Analysis System.

Test Structure
--------------

Tests are organized by type:

* **Unit Tests**: ``tests/test_*.py``
* **Functional Tests**: ``tests/test_*_functional.py``
* **Integration Tests**: ``tests/test_integration.py``
* **Performance Tests**: ``tests/test_performance.py``

Running Tests
-------------

Run all tests:

.. code-block:: bash

   pytest tests/

Run with coverage:

.. code-block:: bash

   pytest tests/ --cov=logic --cov-report=html

Run specific test file:

.. code-block:: bash

   pytest tests/test_backtester.py -v

Writing Tests
-------------

Test Naming Convention
~~~~~~~~~~~~~~~~~~~~~~

* Test files: ``test_<module_name>.py``
* Test classes: ``Test<Feature>``
* Test functions: ``test_<what_is_tested>``

Example:

.. code-block:: python

   class TestBacktester:
       def test_k2n_backtest_returns_results(self):
           # Test implementation
           pass

Test Organization
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from logic.backtester import backtest_function
   
   class TestBacktesterFunctions:
       """Tests for backtest functions"""
       
       def test_function_with_valid_input(self):
           # Arrange
           data = prepare_test_data()
           
           # Act
           result = backtest_function(data)
           
           # Assert
           assert result is not None
           assert len(result) > 0

Fixtures
~~~~~~~~

Use pytest fixtures for common test data:

.. code-block:: python

   @pytest.fixture
   def sample_lottery_data():
       return [
           {"date": "2025-01-01", "prize": "12-34"},
           {"date": "2025-01-02", "prize": "56-78"},
       ]
   
   def test_with_fixture(sample_lottery_data):
       result = process_data(sample_lottery_data)
       assert len(result) == 2

Performance Testing
-------------------

Benchmark tests to ensure performance standards:

.. code-block:: python

   def test_database_query_performance():
       import time
       start = time.time()
       
       # Run query
       result = db.query_large_dataset()
       
       elapsed = time.time() - start
       assert elapsed < 0.01  # Should complete in < 10ms

Test Coverage Goals
-------------------

* **Phase 1**: 60% coverage
* **Final Goal**: 80% coverage
* **Current**: 15% coverage

Priority modules for testing:

1. Backtester modules
2. ML model and feature extractor
3. Dashboard functions
4. Bridge analysis
5. Data management
