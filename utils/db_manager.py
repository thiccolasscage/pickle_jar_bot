import asyncpg
import os
import asyncio
import logging
from utils.logger import logger

class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.pool = None
        self.connected = False
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    async def connect(self, required=False):
        if not self.db_url:
            logger.log("WARNING: DATABASE_URL not set. Database functionality will be limited.")
            return False

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                logger.log(f"Attempting to connect to database (attempt {retry_count + 1}/{self.max_retries})...")
                self.pool = await asyncpg.create_pool(self.db_url)
                self.connected = True
                logger.log("Successfully connected to database!")
                return True
            except (asyncpg.PostgresError, OSError) as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    logger.log(f"Database connection error: {str(e)}. Retrying in {self.retry_delay} seconds...", "error")
                    await asyncio.sleep(self.retry_delay)
                else:
                    if required:
                        logger.log(f"Failed to connect to database after {self.max_retries} attempts: {str(e)}", "error")
                        raise
                    else:
                        logger.log(f"Failed to connect to database after {self.max_retries} attempts: {str(e)}. Running in limited mode.", "error")
                        return False
    
    async def execute(self, query, *args):
        """Execute a SQL query that doesn't return data"""
        if not self.connected:
            logger.log("Database not connected. Cannot execute query.", "error")
            return None
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.log(f"Database query error in execute(): {str(e)}", "error")
            raise
    
    async def fetch(self, query, *args):
        """Execute a SQL query that returns multiple rows"""
        if not self.connected:
            logger.log("Database not connected. Cannot execute query.", "error")
            return []
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.log(f"Database query error in fetch(): {str(e)}", "error")
            raise
    
    async def fetchrow(self, query, *args):
        """Execute a SQL query that returns a single row"""
        if not self.connected:
            logger.log("Database not connected. Cannot execute query.", "error")
            return None
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.log(f"Database query error in fetchrow(): {str(e)}", "error")
            raise
    
    async def create_tables_from_schema(self, schema_file="schema.sql"):
        """Create database tables from schema file"""
        if not self.connected:
            logger.log("Database not connected. Cannot create tables.", "error")
            return False
            
        try:
            # Read schema file
            with open(schema_file, "r") as f:
                schema = f.read()
                
            # Split schema by semicolons to execute multiple statements
            statements = schema.split(';')
            
            # Execute each statement
            async with self.pool.acquire() as conn:
                for statement in statements:
                    statement = statement.strip()
                    if statement:  # Skip empty statements
                        await conn.execute(statement)
                        
            logger.log("Successfully created database tables!")
            return True
        except FileNotFoundError:
            logger.log(f"Schema file '{schema_file}' not found.", "error")
            return False
        except Exception as e:
            logger.log(f"Error creating database tables: {str(e)}", "error")
            return False
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            self.connected = False
            logger.log("Database connection closed.")

# Create a singleton instance
db = DatabaseManager()