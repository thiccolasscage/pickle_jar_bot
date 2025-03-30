import asyncpg
import os
from utils.logger import logger

class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.pool = None

    async def connect(self, required=True):
        """
        Connects to the PostgreSQL database.
        
        Args:
            required (bool): If True, raises an exception when connection fails.
                            If False, returns False on failure instead of raising.
        
        Returns:
            bool: True if connection was successful, False otherwise.
        """
        try:
            if not self.db_url:
                raise ValueError("DATABASE_URL environment variable is not set")
                
            self.pool = await asyncpg.create_pool(self.db_url)
            logger.log(f"Successfully connected to database")
            return True
        except Exception as e:
            logger.log(f"Database connection error: {str(e)}", "error")
            if required:
                raise e
            return False

    async def create_tables_from_schema(self, schema_path):
        """
        Creates database tables from a SQL schema file.
        
        Args:
            schema_path (str): Path to the SQL schema file.
            
        Returns:
            bool: True if tables were created successfully, False otherwise.
        """
        try:
            if not self.pool:
                logger.log("Cannot create tables: Not connected to database", "error")
                return False
                
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
                
            async with self.pool.acquire() as conn:
                await conn.execute(schema_sql)
                
            logger.log(f"Successfully created tables from schema: {schema_path}")
            return True
        except FileNotFoundError:
            logger.log(f"Schema file not found: {schema_path}", "error")
            return False
        except Exception as e:
            logger.log(f"Error creating tables from schema: {str(e)}", "error")
            return False

    async def execute(self, query, *args):
        """Execute a query with no return value expected."""
        if not self.pool:
            logger.log("Cannot execute query: Not connected to database", "error")
            return None
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.log(f"Database execute error: {str(e)}", "error")
            raise

    async def fetchval(self, query, *args):
        """Execute a query and return a single value."""
        if not self.pool:
            logger.log("Cannot fetch value: Not connected to database", "error")
            return None
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.log(f"Database fetchval error: {str(e)}", "error")
            return None

    async def fetch(self, query, *args):
        """Execute a query and return all results as a list of records."""
        if not self.pool:
            logger.log("Cannot fetch records: Not connected to database", "error")
            return []
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.log(f"Database fetch error: {str(e)}", "error")
            return []

    async def fetchrow(self, query, *args):
        """Execute a query and return the first row."""
        if not self.pool:
            logger.log("Cannot fetch row: Not connected to database", "error")
            return None
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.log(f"Database fetchrow error: {str(e)}", "error")
            return None

    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.log("Database connection closed")

db = DatabaseManager()
