Configuration API
=================

Configuration management and constants.

Constants
---------

.. automodule:: logic.constants
   :members:
   :undoc-members:

Default Settings:

* ``STATS_DAYS``: Statistics calculation days (default: 7)
* ``GAN_DAYS``: GAN statistics days (default: 15)
* ``HIGH_WIN_THRESHOLD``: High win threshold (default: 47.0)
* ``K2N_RISK_START_THRESHOLD``: K2N risk start threshold (default: 4)
* ``K2N_RISK_PENALTY_PER_FRAME``: K2N risk penalty (default: 0.5)
* ``AI_SCORE_WEIGHT``: AI score weight (default: 0.2)

Paths:

* ``DB_PATH``: Database file path
* ``MODEL_PATH``: ML model file path
* ``SCALER_PATH``: Feature scaler path

Config Manager
--------------

.. automodule:: logic.config_manager
   :members:
   :undoc-members:

Key Functions:

* ``load_settings``: Load settings from config.json
* ``save_settings``: Save settings to config.json
* ``get_setting``: Get individual setting value
* ``update_setting``: Update individual setting

Validators
----------

.. automodule:: logic.validators
   :members:
   :undoc-members:

Key Functions:

* ``validate_file_upload``: Validate file uploads
* ``validate_config_value``: Validate configuration values
* ``ValidationError``: Validation error exception
