Backtester API
==============

The backtester module provides functions for testing lottery strategies with historical data.

Backtest Modules
----------------

.. automodule:: logic.backtest
   :members:
   :undoc-members:

K2N Mode Backtesting
--------------------

.. automodule:: logic.backtest.backtest_k2n
   :members:
   :undoc-members:
   :show-inheritance:

Key Functions:

* ``BACKTEST_15_CAU_K2N_V30_AI_V8``: Main K2N backtest with AI predictions
* ``BACKTEST_MANAGED_BRIDGES_K2N``: Backtest user-managed bridges in K2N mode

N1 Mode Backtesting
-------------------

.. automodule:: logic.backtest.backtest_n1
   :members:
   :undoc-members:
   :show-inheritance:

Key Functions:

* ``BACKTEST_15_CAU_N1_V31_AI_V8``: Main N1 backtest with AI predictions  
* ``BACKTEST_MANAGED_BRIDGES_N1``: Backtest user-managed bridges in N1 mode

Custom Bridge Backtesting
--------------------------

.. automodule:: logic.backtest.backtest_custom
   :members:
   :undoc-members:
   :show-inheritance:

Key Functions:

* ``BACKTEST_CUSTOM_CAU_V16``: Custom bridge backtest
* ``BACKTEST_MEMORY_BRIDGES``: Memory bridge backtest

Helper Modules
--------------

.. automodule:: logic.backtester
   :members:
   :undoc-members:

.. automodule:: logic.backtester_helpers
   :members:
   :undoc-members:

.. automodule:: logic.backtester_core
   :members:
   :undoc-members:
