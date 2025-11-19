Getting Started
===============

This guide will help you get started with the Lottery Analysis System.

Installation
------------

Requirements
~~~~~~~~~~~~

* Python 3.8 or higher
* pip package manager

Install Dependencies
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -r requirements.txt

The main dependencies include:

* tkinter (GUI framework)
* xgboost (Machine learning)
* joblib (Model persistence)
* pytest (Testing framework)

Quick Start
-----------

Running the Application
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python main_app.py

This will launch the GUI application where you can:

1. Import lottery data
2. Run backtests
3. View predictions
4. Manage bridges

Basic Usage
-----------

Importing Data
~~~~~~~~~~~~~~

1. Click "Import Data" in the main window
2. Select a text file containing lottery results
3. Data will be parsed and stored in the database

Running Backtests
~~~~~~~~~~~~~~~~~

1. Navigate to the Backtest tab
2. Select mode (N1 or K2N)
3. Configure parameters
4. Click "Run Backtest"
5. View results in the output panel

Configuration
-------------

The system uses ``config.json`` for configuration:

.. code-block:: json

   {
     "STATS_DAYS": 7,
     "GAN_DAYS": 15,
     "HIGH_WIN_THRESHOLD": 47.0,
     "AI_SCORE_WEIGHT": 0.2,
     "AI_MAX_DEPTH": 6,
     "AI_N_ESTIMATORS": 200
   }

Testing
-------

Run the test suite:

.. code-block:: bash

   # Run all tests
   pytest tests/

   # Run with coverage
   pytest tests/ --cov=logic --cov-report=html

   # Run specific test file
   pytest tests/test_backtester.py

Next Steps
----------

* Read the :doc:`architecture` guide
* Explore the :doc:`api/index` documentation
* Check out :doc:`examples` for common use cases
