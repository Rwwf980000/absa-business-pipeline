# bigquery_manager.py
"""
BigQuery Management Functions - With STRING timestamps
"""

from google.cloud import bigquery
import logging

logger = logging.getLogger(__name__)

def ensure_dataset_exists(client, project_id, dataset_name, location="me-central2"):
    """Create BigQuery dataset if it doesn't exist"""
    dataset_id = f"{project_id}.{dataset_name}"
    
    try:
        client.get_dataset(dataset_id)
        logger.info(f"✅ Dataset exists: {dataset_id}")
    except:
        logger.info(f"📊 Creating dataset: {dataset_id}")
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = location
        dataset.description = "ABSA Analysis for Fitness Reviews"
        client.create_dataset(dataset)
        logger.info(f"✅ Created dataset: {dataset_id}")

def ensure_table_exists(client, project_id, dataset_name, table_name):
    """Create partitioned table if it doesn't exist"""
    table_id = f"{project_id}.{dataset_name}.{table_name}"
    
    try:
        table = client.get_table(table_id)
        logger.info(f"✅ Table exists: {table_id} ({table.num_rows:,} rows)")
        return
    except:
        logger.info(f"📊 Creating partitioned table: {table_id}")
    
    # All fields NULLABLE, timestamps as STRING (not TIMESTAMP)
    schema = [
        bigquery.SchemaField("review_id", "STRING"),
        bigquery.SchemaField("data_source", "STRING"),
        bigquery.SchemaField("branch_id", "INTEGER"),
        bigquery.SchemaField("branch_name", "STRING"),
        bigquery.SchemaField("place_name", "STRING"),
        bigquery.SchemaField("place_id", "STRING"),
        bigquery.SchemaField("address", "STRING"),
        bigquery.SchemaField("phone", "STRING"),
        bigquery.SchemaField("overall_rating", "FLOAT"),
        bigquery.SchemaField("total_user_ratings", "INTEGER"),
        bigquery.SchemaField("author_name", "STRING"),
        bigquery.SchemaField("author_url", "STRING"),
        bigquery.SchemaField("author_id", "STRING"),
        bigquery.SchemaField("author_username", "STRING"),
        bigquery.SchemaField("rating", "INTEGER"),
        bigquery.SchemaField("raw_review", "STRING"),
        bigquery.SchemaField("normalized_text", "STRING"),
        bigquery.SchemaField("absa_result_json", "STRING"),
        bigquery.SchemaField("time", "INTEGER"),
        bigquery.SchemaField("relative_time", "STRING"),
        bigquery.SchemaField("language", "STRING"),
        bigquery.SchemaField("likes", "INTEGER"),
        bigquery.SchemaField("retweets", "INTEGER"),
        bigquery.SchemaField("replies", "INTEGER"),
        bigquery.SchemaField("collected_at", "STRING"),  # STRING not TIMESTAMP
        bigquery.SchemaField("created_at", "STRING"),    # STRING not TIMESTAMP  
        bigquery.SchemaField("query", "STRING"),
        bigquery.SchemaField("processed_at", "STRING"),  # STRING not TIMESTAMP
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table)
    logger.info(f"✅ Created table: {table_id} (timestamps as STRING)")

def get_processed_review_ids(client, project_id, dataset_name, table_name):
    """Get set of already processed review IDs"""
    try:
        query = f"""
        SELECT DISTINCT review_id 
        FROM `{project_id}.{dataset_name}.{table_name}`
        WHERE review_id IS NOT NULL
        """
        result = client.query(query).result()
        processed_ids = set(row.review_id for row in result)
        logger.info(f"✅ Found {len(processed_ids)} already processed reviews")
        return processed_ids
    except Exception as e:
        logger.warning(f"⚠️  Could not get processed IDs: {e}")
        return set()

def update_views(client, project_id, dataset_name, table_name):
    """Create or update all BigQuery views"""
    logger.info("\n>>> Updating BigQuery Views...")
    
    views = {
        "reviews_parsed": f"""
        CREATE OR REPLACE VIEW `{project_id}.{dataset_name}.reviews_parsed` AS
        SELECT 
          review_id, data_source, place_name, raw_review, normalized_text,
          rating, 
          PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', SUBSTR(processed_at, 1, 19)) as processed_at,
          JSON_EXTRACT_SCALAR(aspect_obj, '$.aspect') AS aspect,
          JSON_EXTRACT_SCALAR(aspect_obj, '$.polarity') AS polarity
        FROM `{project_id}.{dataset_name}.{table_name}`,
          UNNEST(JSON_EXTRACT_ARRAY(absa_result_json)) AS aspect_obj
        WHERE JSON_EXTRACT_SCALAR(aspect_obj, '$.aspect') IS NOT NULL
          AND JSON_EXTRACT_SCALAR(aspect_obj, '$.aspect') NOT IN ('System', 'Error')
        """,
        
        "aspect_summary": f"""
        CREATE OR REPLACE VIEW `{project_id}.{dataset_name}.aspect_summary` AS
        SELECT 
          data_source, aspect, polarity,
          COUNT(*) as mention_count,
          COUNT(DISTINCT review_id) as unique_reviews,
          ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(PARTITION BY data_source), 2) as percentage_in_source,
          ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage_overall
        FROM `{project_id}.{dataset_name}.reviews_parsed`
        GROUP BY data_source, aspect, polarity
        ORDER BY mention_count DESC
        """,
        
        "sentiment_by_source": f"""
        CREATE OR REPLACE VIEW `{project_id}.{dataset_name}.sentiment_by_source` AS
        SELECT 
          data_source, polarity,
          COUNT(*) as mention_count,
          COUNT(DISTINCT review_id) as unique_reviews,
          ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(PARTITION BY data_source), 2) as percentage
        FROM `{project_id}.{dataset_name}.reviews_parsed`
        GROUP BY data_source, polarity
        ORDER BY data_source, mention_count DESC
        """,
        
        "daily_processing_stats": f"""
        CREATE OR REPLACE VIEW `{project_id}.{dataset_name}.daily_processing_stats` AS
        SELECT 
          DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', SUBSTR(processed_at, 1, 19))) as processing_date,
          data_source,
          COUNT(*) as reviews_processed,
          COUNT(DISTINCT place_name) as unique_places,
          AVG(rating) as avg_rating
        FROM `{project_id}.{dataset_name}.{table_name}`
        WHERE rating IS NOT NULL AND processed_at IS NOT NULL
        GROUP BY processing_date, data_source
        ORDER BY processing_date DESC
        """,
        
        "top_aspects_by_place": f"""
        CREATE OR REPLACE VIEW `{project_id}.{dataset_name}.top_aspects_by_place` AS
        SELECT 
          place_name, aspect, polarity,
          COUNT(*) as mention_count,
          COUNT(DISTINCT review_id) as unique_reviews
        FROM `{project_id}.{dataset_name}.reviews_parsed`
        WHERE place_name IS NOT NULL
        GROUP BY place_name, aspect, polarity
        ORDER BY place_name, mention_count DESC
        """,
        
        "negative_feedback": f"""
        CREATE OR REPLACE VIEW `{project_id}.{dataset_name}.negative_feedback` AS
        SELECT 
          review_id, data_source, place_name, raw_review, aspect, rating, processed_at
        FROM `{project_id}.{dataset_name}.reviews_parsed`
        WHERE polarity = 'سلبي'
        ORDER BY processed_at DESC
        """,
        
        "rating_vs_sentiment": f"""
        CREATE OR REPLACE VIEW `{project_id}.{dataset_name}.rating_vs_sentiment` AS
        SELECT 
          place_name, rating, polarity,
          COUNT(*) as count,
          ROUND(AVG(rating), 2) as avg_numeric_rating
        FROM `{project_id}.{dataset_name}.reviews_parsed`
        WHERE rating IS NOT NULL
        GROUP BY place_name, rating, polarity
        ORDER BY place_name, rating DESC
        """
    }
    
    for view_name, view_sql in views.items():
        try:
            client.query(view_sql).result()
            logger.info(f"✅ Updated view: {view_name}")
        except Exception as e:
            logger.error(f"❌ Error updating view {view_name}: {e}")
