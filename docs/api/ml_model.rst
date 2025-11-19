Machine Learning API
====================

The ML model module provides AI-powered prediction capabilities using XGBoost.

ML Model
--------

.. automodule:: logic.ml_model
   :members:
   :undoc-members:
   :show-inheritance:

Key Components:

* XGBoost Classifier for binary prediction
* Q-Features (Quality Features) for improved accuracy
* Feature extraction and scaling
* Model persistence with joblib

AI Feature Extractor
--------------------

.. automodule:: logic.ai_feature_extractor
   :members:
   :undoc-members:
   :show-inheritance:

Features Extracted:

* ``q_avg_win_rate``: Average win rate quality metric
* ``q_min_k2n_risk``: Minimum K2N risk quality metric
* Bridge statistics and patterns
* Historical performance metrics

Configuration Parameters
------------------------

The ML model uses these configuration parameters from ``config.json``:

* ``AI_MAX_DEPTH``: Maximum tree depth (default: 6)
* ``AI_N_ESTIMATORS``: Number of trees (default: 200)
* ``AI_LEARNING_RATE``: Learning rate (default: 0.05)
* ``AI_OBJECTIVE``: Objective function (default: "binary:logistic")
* ``AI_SCORE_WEIGHT``: AI score weight in final scoring (default: 0.2)
* ``AI_PROB_THRESHOLD``: Probability threshold (default: 45.0)

Usage Example
-------------

.. code-block:: python

   from logic.ml_model import load_model, predict
   from logic.ai_feature_extractor import extract_features
   
   # Load trained model
   model = load_model()
   
   # Extract features from data
   features = extract_features(lottery_data)
   
   # Make predictions
   predictions = predict(model, features)
