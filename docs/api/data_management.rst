Data Management API
===================

Database access, data parsing, and repository functions.

Database Manager
----------------

.. automodule:: logic.db_manager
   :members:
   :undoc-members:

Key Functions:

* ``create_tables``: Create database tables
* ``insert_prizes``: Insert lottery results
* ``query_prizes``: Query lottery data
* ``create_indexes``: Create database indexes

Data Repository
---------------

.. automodule:: logic.data_repository
   :members:
   :undoc-members:

Key Functions:

* ``load_data_from_db``: Load data from database with caching
* ``get_all_managed_bridges``: Get user-managed bridges
* Cache management for performance

Data Parser
-----------

.. automodule:: logic.data_parser
   :members:
   :undoc-members:

Key Functions:

* ``parse_prize_data``: Parse lottery result text files
* ``validate_data``: Validate parsed data
* ``format_data``: Format data for database insertion
