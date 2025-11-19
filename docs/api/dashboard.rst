Dashboard API
=============

The dashboard module provides real-time analytics, predictions, and scoring functions.

Dashboard Modules
-----------------

.. automodule:: logic.dashboard
   :members:
   :undoc-members:

Statistics Functions
--------------------

.. automodule:: logic.dashboard.dashboard_stats
   :members:
   :undoc-members:
   :show-inheritance:

Key Functions:

* ``get_loto_stats_last_n_days``: Get statistics for recent days
* ``get_loto_gan_stats``: Get GAN statistics

Prediction Functions
--------------------

.. automodule:: logic.dashboard.dashboard_predictions
   :members:
   :undoc-members:
   :show-inheritance:

Key Functions:

* ``get_prediction_consensus``: Get consensus predictions
* ``get_high_win_rate_predictions``: Get high win rate predictions
* ``get_top_memory_bridge_predictions``: Get memory bridge predictions
* ``get_pending_k2n_bridges``: Get pending K2N bridges

Scoring Functions
-----------------

.. automodule:: logic.dashboard.dashboard_scoring
   :members:
   :undoc-members:
   :show-inheritance:

Key Functions:

* ``get_top_scored_pairs``: Calculate and rank lottery pairs with weighted scoring

Simulation Functions
--------------------

.. automodule:: logic.dashboard.dashboard_simulation
   :members:
   :undoc-members:
   :show-inheritance:

Key Functions:

* ``get_consensus_simulation``: Simulate consensus predictions
* ``get_high_win_simulation``: Simulate high win rate predictions
* ``get_historical_dashboard_data``: Get historical dashboard data
