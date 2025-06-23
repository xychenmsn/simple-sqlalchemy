"""
PostgreSQL-specific utilities for simple-sqlalchemy
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class PostgreSQLUtils:
    """
    Utility class for PostgreSQL-specific operations.
    
    Provides utilities for sequence management, constraint handling,
    and PostgreSQL-specific features.
    """
    
    def __init__(self, db_client):
        """
        Initialize PostgreSQL utilities.
        
        Args:
            db_client: Database client instance
        """
        self.db_client = db_client
    
    def reset_sequence(self, table_name: str, column_name: str = 'id') -> bool:
        """
        Reset a PostgreSQL sequence to match the current max value.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column (default: 'id')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_client.session_scope() as session:
                # Get the current max value
                max_query = text(f"SELECT COALESCE(MAX({column_name}), 0) FROM {table_name}")
                max_value = session.execute(max_query).scalar()
                
                # Reset the sequence
                sequence_query = text(
                    f"SELECT setval(pg_get_serial_sequence('{table_name}', '{column_name}'), {max_value})"
                )
                session.execute(sequence_query)
                
                logger.info(f"Reset sequence for {table_name}.{column_name} to {max_value}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error resetting sequence for {table_name}.{column_name}: {e}")
            return False
    
    def drop_constraint(self, table_name: str, constraint_name: str) -> bool:
        """
        Drop a constraint from a table.
        
        Args:
            table_name: Name of the table
            constraint_name: Name of the constraint
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_client.session_scope() as session:
                drop_query = text(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}")
                session.execute(drop_query)
                logger.info(f"Dropped constraint {constraint_name} from {table_name}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error dropping constraint {constraint_name} from {table_name}: {e}")
            return False
    
    def add_foreign_key_constraint(
        self,
        table_name: str,
        constraint_name: str,
        column_name: str,
        ref_table: str,
        ref_column: str = 'id'
    ) -> bool:
        """
        Add a foreign key constraint to a table.
        
        Args:
            table_name: Name of the table
            constraint_name: Name of the constraint
            column_name: Name of the column
            ref_table: Name of the referenced table
            ref_column: Name of the referenced column (default: 'id')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_client.session_scope() as session:
                add_query = text(
                    f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} "
                    f"FOREIGN KEY ({column_name}) REFERENCES {ref_table} ({ref_column})"
                )
                session.execute(add_query)
                logger.info(f"Added foreign key constraint {constraint_name} to {table_name}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error adding foreign key constraint {constraint_name} to {table_name}: {e}")
            return False
    
    def get_table_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all constraints for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of constraint information dictionaries
        """
        try:
            with self.db_client.session_scope() as session:
                query = text("""
                    SELECT 
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM 
                        information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        LEFT JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                    WHERE 
                        tc.table_name = :table_name
                        AND tc.table_schema = 'public'
                    ORDER BY tc.constraint_name
                """)
                
                result = session.execute(query, {"table_name": table_name})
                return [dict(row) for row in result]
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting constraints for {table_name}: {e}")
            return []
    
    def vacuum_table(self, table_name: str, analyze: bool = True) -> bool:
        """
        Vacuum a table to reclaim space and update statistics.
        
        Args:
            table_name: Name of the table
            analyze: Whether to also run ANALYZE
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_client.session_scope() as session:
                # Note: VACUUM cannot be run inside a transaction block
                # This is a limitation when using session_scope
                vacuum_cmd = f"VACUUM {'ANALYZE' if analyze else ''} {table_name}"
                
                # We need to use autocommit mode for VACUUM
                connection = session.connection()
                connection.execute(text("COMMIT"))  # End current transaction
                connection.execute(text(vacuum_cmd))
                
                logger.info(f"Vacuumed table {table_name}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error vacuuming table {table_name}: {e}")
            return False
    
    def get_table_size(self, table_name: str) -> Dict[str, Any]:
        """
        Get size information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with size information
        """
        try:
            with self.db_client.session_scope() as session:
                query = text("""
                    SELECT 
                        pg_size_pretty(pg_total_relation_size(:table_name)) as total_size,
                        pg_size_pretty(pg_relation_size(:table_name)) as table_size,
                        pg_size_pretty(pg_total_relation_size(:table_name) - pg_relation_size(:table_name)) as index_size,
                        (SELECT COUNT(*) FROM """ + table_name + """) as row_count
                """)
                
                result = session.execute(query, {"table_name": table_name}).first()
                
                return {
                    "total_size": result.total_size,
                    "table_size": result.table_size,
                    "index_size": result.index_size,
                    "row_count": result.row_count
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting size for table {table_name}: {e}")
            return {}
    
    def create_index(
        self,
        table_name: str,
        column_names: List[str],
        index_name: Optional[str] = None,
        unique: bool = False,
        concurrent: bool = False
    ) -> bool:
        """
        Create an index on a table.
        
        Args:
            table_name: Name of the table
            column_names: List of column names to index
            index_name: Name of the index (auto-generated if None)
            unique: Whether to create a unique index
            concurrent: Whether to create the index concurrently
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not index_name:
                columns_str = "_".join(column_names)
                index_name = f"idx_{table_name}_{columns_str}"
            
            columns_str = ", ".join(column_names)
            
            create_cmd = f"CREATE {'UNIQUE' if unique else ''} INDEX {'CONCURRENTLY' if concurrent else ''} {index_name} ON {table_name} ({columns_str})"
            
            with self.db_client.session_scope() as session:
                session.execute(text(create_cmd))
                logger.info(f"Created index {index_name} on {table_name}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error creating index on {table_name}: {e}")
            return False
    
    def drop_index(self, index_name: str, concurrent: bool = False) -> bool:
        """
        Drop an index.
        
        Args:
            index_name: Name of the index
            concurrent: Whether to drop the index concurrently
            
        Returns:
            True if successful, False otherwise
        """
        try:
            drop_cmd = f"DROP INDEX {'CONCURRENTLY' if concurrent else ''} IF EXISTS {index_name}"
            
            with self.db_client.session_scope() as session:
                session.execute(text(drop_cmd))
                logger.info(f"Dropped index {index_name}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error dropping index {index_name}: {e}")
            return False
