
from django.db import connection
import time
import logging
from functools import wraps

def query_performance_monitor(func):
    """Decorator to monitor query performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_queries = len(connection.queries)

        result = func(*args, **kwargs)

        end_time = time.time()
        end_queries = len(connection.queries)

        logger.info(
            f"Function {func.__name__} took {end_time - start_time:.2f}s "
            f"and executed {end_queries - start_queries} queries"
        )

        return result
    return wrapper

class PerformanceMetrics:
    """Track database performance metrics"""

    @staticmethod
    def get_table_sizes():
        """Get table sizes for monitoring"""
        with connection.cursor() as cursor:
            cursor.execute("""
                           SELECT
                               table_name,
                               pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
                           FROM information_schema.tables
                           WHERE table_schema = 'public'
                           ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;
                           """)
            return dict(cursor.fetchall())