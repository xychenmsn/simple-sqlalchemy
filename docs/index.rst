Simple SQLAlchemy Documentation
==================================

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.8+

.. image:: https://img.shields.io/badge/sqlalchemy-1.4+-green.svg
   :target: https://www.sqlalchemy.org/
   :alt: SQLAlchemy 1.4+

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

A simplified, enhanced SQLAlchemy package that combines the power of SQLAlchemy ORM with convenient string-schema validation for modern database operations.

Quick Start
-----------

Get started in 30 seconds with the most common database operations:

.. code-block:: python

   from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
   from sqlalchemy import Column, String, Integer, Boolean

   # 1. Setup database and model
   db = DbClient("sqlite:///app.db")

   class User(CommonBase):
       __tablename__ = 'users'
       name = Column(String(100), nullable=False)
       email = Column(String(100), unique=True)
       active = Column(Boolean, default=True)

   CommonBase.metadata.create_all(db.engine)

   # 2. Create CRUD operations
   user_crud = BaseCrud(User, db)

   # 3. Use it! - Returns validated dictionaries ready for APIs
   users = user_crud.query_with_schema(
       schema_str="id:int, name:string, email:email?, active:bool",
       filters={"active": True},
       sort_by="name",
       limit=10
   )

Features
--------

🎯 **90% Convenience**: String-schema operations for common use cases

🔧 **10% Power**: Full SQLAlchemy access when you need it

📊 **Enhanced Filtering**: null/not-null, comparisons, lists, ranges

📄 **Pagination**: Built-in pagination with metadata

🔍 **Search**: Text search across multiple fields

📈 **Aggregation**: Group by, count, sum, avg with schema validation

🔄 **Hybrid Approach**: Mix SQLAlchemy models and validated dicts

🗃️ **Database Agnostic**: SQLite, PostgreSQL, MySQL support

⚡ **Zero Breaking Changes**: Enhances existing SQLAlchemy patterns

Installation
------------

.. code-block:: bash

   pip install simple-sqlalchemy

For PostgreSQL vector support:

.. code-block:: bash

   pip install simple-sqlalchemy[postgres]

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   quickstart
   string_schema
   traditional_sqlalchemy
   advanced_features
   postgresql_features
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/crud
   api/helpers
   api/postgres

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog
   license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
