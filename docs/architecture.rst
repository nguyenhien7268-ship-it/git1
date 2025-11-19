Architecture Overview
=====================

This document describes the architecture of the Lottery Analysis System.

System Architecture
-------------------

The system follows a layered architecture pattern:

.. code-block:: text

   ┌─────────────────────────────────────┐
   │         UI Layer (Tkinter)          │
   │   main_app.py, app_controller.py    │
   └─────────────────┬───────────────────┘
                     │
   ┌─────────────────▼───────────────────┐
   │      Service Layer                  │
   │  lottery_service.py, core_services  │
   └─────────────────┬───────────────────┘
                     │
   ┌─────────────────▼───────────────────┐
   │       Business Logic Layer          │
   │  logic/ (backtester, ml_model, etc) │
   └─────────────────┬───────────────────┘
                     │
   ┌─────────────────▼───────────────────┐
   │       Data Access Layer             │
   │  db_manager, data_repository        │
   └─────────────────┬───────────────────┘
                     │
   ┌─────────────────▼───────────────────┐
   │          Database (SQLite)          │
   │     xo_so_prizes_all_logic.db       │
   └─────────────────────────────────────┘

Module Organization
-------------------

Core Modules
~~~~~~~~~~~~

The system is organized into focused modules:

**Backtest Package** (``logic/backtest/``)

* ``backtest_k2n.py`` (396 LOC): K2N mode backtesting
* ``backtest_n1.py`` (271 LOC): N1 mode backtesting
* ``backtest_custom.py`` (346 LOC): Custom bridge backtesting

**Dashboard Package** (``logic/dashboard/``)

* ``dashboard_stats.py`` (127 LOC): Statistics calculations
* ``dashboard_predictions.py`` (331 LOC): Prediction functions
* ``dashboard_scoring.py`` (232 LOC): Scoring algorithms
* ``dashboard_simulation.py`` (220 LOC): Simulation functions

**Bridges Package** (``logic/bridges/``)

* ``bridges_classic.py``: Classic bridge functions
* ``bridges_memory.py``: Memory bridge patterns
* ``bridges_v16.py``: Version 16 bridge algorithms
* ``bridge_manager_core.py``: Bridge management

Design Patterns
---------------

MVP Pattern
~~~~~~~~~~~

The application uses the Model-View-Presenter (MVP) pattern:

* **Model**: Business logic (``logic/`` modules)
* **View**: UI components (``ui/`` modules)
* **Presenter**: Controller logic (``app_controller.py``)

Repository Pattern
~~~~~~~~~~~~~~~~~~

Data access is abstracted through repositories:

* ``data_repository.py``: Data loading and caching
* ``db_manager.py``: Direct database operations

Strategy Pattern
~~~~~~~~~~~~~~~~

Bridge strategies use the strategy pattern:

* ``i_bridge_strategy.py``: Strategy interface
* ``bridge_factory.py``: Strategy factory

Multi-threading
---------------

The system uses multi-threading to prevent UI freezing:

TaskManager
~~~~~~~~~~~

.. code-block:: python

   from core_services import TaskManager
   
   task_manager = TaskManager()
   task_manager.run_async(long_running_function, callback)

Logger
~~~~~~

Thread-safe logging:

.. code-block:: python

   from core_services import Logger
   
   logger = Logger()
   logger.info("Message")

Configuration Management
-------------------------

Single Source of Truth
~~~~~~~~~~~~~~~~~~~~~~

All configuration values are centralized in ``logic/constants.py``:

.. code-block:: python

   from logic.constants import DEFAULT_SETTINGS, DB_PATH
   
   stats_days = DEFAULT_SETTINGS['STATS_DAYS']

This eliminates duplicate configuration values across modules.

Database Schema
---------------

Tables
~~~~~~

* ``prizes``: Historical lottery results
* ``managed_bridges``: User-managed bridge patterns
* ``ai_features``: Extracted features for ML
* ``backtest_results``: Cached backtest results

Indexes
~~~~~~~

Optimized indexes for fast queries:

* ``idx_prizes_date``: Date-based lookups
* ``idx_prizes_region``: Region filtering
* ``idx_managed_bridges_name``: Bridge name search

Performance Characteristics
---------------------------

Benchmarks
~~~~~~~~~~

* Database queries: < 10ms (with indexes)
* Bulk inserts: < 500ms (100 records)
* N1/K2N backtest: < 1000ms (small dataset)
* Data loading: < 200ms (1000 records)
* Memory: No leaks detected

Code Quality Metrics
--------------------

* **Test Coverage**: 15%
* **Test Count**: 148 passing, 12 skipped
* **Code Quality**: All files < 500 LOC
* **Security**: 0 vulnerabilities

Testing Strategy
----------------

Test Types
~~~~~~~~~~

* **Unit Tests** (53%): Individual function testing
* **Functional Tests** (28%): Feature-level testing
* **Integration Tests** (19%): Component integration
* **Performance Tests** (9%): Benchmark validation

See :doc:`api/testing` for testing guidelines.
