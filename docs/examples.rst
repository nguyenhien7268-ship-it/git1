Examples
========

Common use cases and code examples for the Lottery Analysis System.

Basic Examples
--------------

Running a Backtest
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from logic.backtest import BACKTEST_15_CAU_K2N_V30_AI_V8
   from logic.db_manager import DB_NAME
   
   # Run K2N backtest
   results = BACKTEST_15_CAU_K2N_V30_AI_V8(
       db_name=DB_NAME,
       limit_range=30,  # Last 30 results
       top_n=5,  # Top 5 predictions
       ai_score_weight=0.2  # AI score weight
   )
   
   # Process results
   for result in results:
       print(f"Date: {result['date']}, "
             f"Prediction: {result['prediction']}, "
             f"Hit: {result['hit']}")

Making Predictions
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from logic.dashboard import get_prediction_consensus
   from logic.db_manager import DB_NAME
   
   # Get last lottery result
   last_row = get_last_result(DB_NAME)
   
   # Get consensus predictions
   predictions = get_prediction_consensus(
       last_row=last_row,
       db_name=DB_NAME
   )
   
   # Display top predictions
   for pred in predictions[:5]:
       print(f"Pair: {pred['pair']}, "
             f"Sources: {pred['sources']}, "
             f"Confidence: {pred['confidence']}")

Advanced Examples
-----------------

Custom Bridge Analysis
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from logic.bridges.bridges_memory import getAllBridges_Memory_FAST
   from logic.backtest import BACKTEST_CUSTOM_CAU_V16
   
   # Get memory bridges
   result = {"numbers": "12-34-56-78-90"}
   bridges = getAllBridges_Memory_FAST(result)
   
   # Backtest custom bridges
   results = BACKTEST_CUSTOM_CAU_V16(
       db_name=DB_NAME,
       limit_range=50,
       bridge_functions=bridges
   )

AI-Powered Scoring
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from logic.dashboard import get_top_scored_pairs
   from logic.ml_model import load_model, predict
   
   # Load ML model
   model = load_model()
   
   # Get predictions from various sources
   stats = get_loto_stats_last_n_days(data, n=7)
   consensus = get_prediction_consensus(last_row, DB_NAME)
   high_win = get_high_win_rate_predictions(last_row, 47.0, DB_NAME)
   
   # Calculate AI predictions
   ai_predictions = predict(model, features)
   
   # Get top scored pairs with AI weighting
   top_pairs = get_top_scored_pairs(
       stats=stats,
       consensus=consensus,
       high_win=high_win,
       pending_k2n=[],
       gan_stats=gan_stats,
       top_memory_bridges=memory_predictions,
       ai_predictions=ai_predictions
   )

Data Management
~~~~~~~~~~~~~~~

.. code-block:: python

   from logic.data_parser import parse_prize_data
   from logic.db_manager import insert_prizes, create_indexes
   
   # Parse data file
   with open('lottery_data.txt', 'r') as f:
       content = f.read()
   
   prizes = parse_prize_data(content)
   
   # Insert into database
   insert_prizes(DB_NAME, prizes)
   
   # Create indexes for performance
   create_indexes(DB_NAME)

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from logic.config_manager import load_settings, update_setting
   from logic.constants import DEFAULT_SETTINGS
   
   # Load current settings
   settings = load_settings()
   
   # Update a setting
   update_setting('STATS_DAYS', 14)
   
   # Use default if not configured
   stats_days = settings.get('STATS_DAYS', 
                              DEFAULT_SETTINGS['STATS_DAYS'])

Multi-threading
~~~~~~~~~~~~~~~

.. code-block:: python

   from core_services import TaskManager, Logger
   
   # Create task manager
   task_manager = TaskManager()
   logger = Logger()
   
   def long_running_task():
       # Perform backtest
       results = run_backtest()
       return results
   
   def on_complete(results):
       # Update UI with results
       logger.info(f"Backtest complete: {len(results)} results")
       display_results(results)
   
   # Run asynchronously
   task_manager.run_async(long_running_task, on_complete)

Testing Examples
----------------

Unit Test Example
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from logic.validators import validate_config_value, ValidationError
   
   def test_validate_config_accepts_valid_value():
       # Should not raise exception
       validate_config_value('STATS_DAYS', 7)
   
   def test_validate_config_rejects_invalid_value():
       with pytest.raises(ValidationError):
           validate_config_value('STATS_DAYS', -1)

Integration Test Example
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_full_backtest_workflow():
       # Parse data
       data = parse_test_data()
       
       # Insert to database
       insert_prizes(TEST_DB, data)
       
       # Run backtest
       results = BACKTEST_15_CAU_K2N_V30_AI_V8(
           db_name=TEST_DB,
           limit_range=10,
           top_n=3,
           ai_score_weight=0.2
       )
       
       # Verify results
       assert len(results) > 0
       assert 'hit' in results[0]

Best Practices
--------------

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from logic.validators import ValidationError
   
   try:
       validate_file_upload(file_path)
       data = parse_prize_data(file_path)
   except ValidationError as e:
       logger.error(f"Validation error: {e}")
       show_error_message(str(e))
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       show_error_message("An unexpected error occurred")

Resource Management
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sqlite3
   from contextlib import closing
   
   with closing(sqlite3.connect(DB_NAME)) as conn:
       cursor = conn.cursor()
       cursor.execute("SELECT * FROM prizes")
       results = cursor.fetchall()

Logging
~~~~~~~

.. code-block:: python

   from core_services import Logger
   
   logger = Logger()
   
   logger.info("Starting backtest")
   logger.debug(f"Parameters: range={limit_range}, top_n={top_n}")
   
   try:
       results = run_backtest()
       logger.info(f"Backtest complete: {len(results)} results")
   except Exception as e:
       logger.error(f"Backtest failed: {e}", exc_info=True)
