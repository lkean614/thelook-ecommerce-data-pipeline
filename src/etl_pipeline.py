import duckdb
import time

def clean_data():
    print(">>> Phase 1: Cleaning Raw Data...")
    print("-" * 70)
#===========================================================================
# 1. events
#===========================================================================
    rel_events= duckdb.sql("""
    SELECT
        id,
        COALESCE(user_id,0) AS user_id,
        sequence_number,
        session_id,
        created_at,
        ip_address,
        CASE WHEN
            city = 'null' THEN 'Unknown' ELSE
            city
        END AS city,
        state,
        postal_code,
        browser,
        traffic_source,
        uri,
        event_type
    FROM "../dataset/raw/events.csv"
    """)

    count_events = rel_events.shape[0]
    rel_events.to_parquet('../dataset/processed/clean_events.parquet')
    print(f"[OK] clean_events          : {count_events:,} records cleaned & saved.")
#===========================================================================
    # 2. inventory_items
#===========================================================================
    rel_inventory = duckdb.sql("""
    SELECT
        id,
        product_id,
        created_at,
        sold_at,
        cost,
        product_category,
        COALESCE(product_name,'Unknown') AS product_name,
        COALESCE(product_brand,'Unknown') AS product_brand,
        product_retail_price,
        product_department,
        product_sku,
        product_distribution_center_id
    FROM "../dataset/raw/inventory_items.csv"
    """)

    count_inventory = rel_inventory.shape[0]
    rel_inventory.to_parquet('../dataset/processed/clean_inventory_items.parquet')
    print(f"[OK] clean_inventory_items : {count_inventory:,} records cleaned & saved.")
#===========================================================================
    # 3. orders
#===========================================================================
    rel_orders = duckdb.sql("""
    SELECT
        order_id,
        user_id,
        status,
        gender,
        TRY_CAST(created_at AS timestamp) AS created_at,
        TRY_CAST(returned_at AS timestamp) AS returned_at,
        TRY_CAST(shipped_at AS timestamp) AS shipped_at,
        TRY_CAST(delivered_at AS timestamp) AS delivered_at,
        num_of_item
    FROM read_csv_auto('../dataset/raw/orders.csv', types={'gender': 'VARCHAR'})
    WHERE
        shipped_at >= created_at OR shipped_at IS NULL
    """)

    count_orders = rel_orders.shape[0]
    rel_orders.to_parquet('../dataset/processed/clean_orders.parquet')
    print(f"[OK] clean_orders          : {count_orders:,} records cleaned & saved.")
#===========================================================================
    # 4. order_items
#===========================================================================
    rel_order_items = duckdb.sql("""
    SELECT
        id,
        order_id,
        user_id,
        inventory_item_id,
        status,
        TRY_CAST(created_at AS timestamp) AS created_at,
        TRY_CAST(shipped_at AS timestamp) AS shipped_at,
        TRY_CAST(delivered_at AS timestamp) AS delivered_at,
        TRY_CAST(returned_at AS timestamp) AS returned_at,
        sale_price
    FROM "../dataset/raw/order_items.csv"
    WHERE 
        (created_at <= shipped_at OR shipped_at IS NULL) AND
        (created_at <= delivered_at OR delivered_at IS NULL) AND
        (created_at <= returned_at OR returned_at IS NULL)
    """)

    count_order_items = rel_order_items.shape[0]
    rel_order_items.to_parquet('../dataset/processed/clean_order_items.parquet')
    print(f"[OK] clean_order_items     : {count_order_items:,} records cleaned & saved.")
#===========================================================================
    # 4.2 exception_order_items
#===========================================================================
    exception_order_items = duckdb.sql("""
    SELECT
        id,
        order_id,
        user_id,
        inventory_item_id,
        status,
        TRY_CAST(created_at AS timestamp) AS created_at,
        TRY_CAST(shipped_at AS timestamp) AS shipped_at,
        TRY_CAST(delivered_at AS timestamp) AS delivered_at,
        TRY_CAST(returned_at AS timestamp) AS returned_at,
        sale_price
    FROM "../dataset/raw/order_items.csv"
    WHERE 
            created_at > returned_at or 
            created_at > shipped_at or 
            created_at > delivered_at
    """)
    count_exception_order_items = exception_order_items.shape[0]
    exception_order_items.to_parquet('../dataset/processed/exception_order_items.parquet')
    print(f"[OK] exception_order_items : {count_exception_order_items:,} records cleaned & saved.")
#===========================================================================
    # 5. users
#===========================================================================
    rel_users = duckdb.sql("""
    SELECT
        id,
        first_name,
        last_name,
        COALESCE(email,'Unknown') AS email,
        COALESCE(age,null) AS age,
        COALESCE(gender,'Unknown') AS gender,
        state,
        COALESCE(street_address,'Unknown') AS street_address,
        postal_code,
        COALESCE(NULLIF(LOWER(city), 'null'), 'Unknown') AS city,
        country,
        latitude,
        longitude,
        traffic_source,
        COALESCE(created_at,null) AS created_at,
        user_geom
    FROM "../dataset/raw/users.csv"
    """)

    count_users = rel_users.shape[0]
    rel_users.to_parquet('../dataset/processed/clean_users.parquet')
    print(f"[OK] clean_users           : {count_users:,} records cleaned & saved.")

    print("-" * 70)
    print("Phase 1 Completed: All raw data cleaned and loaded into Data Lake.\n")


def build_obts():
    print(">>> Phase 2: Building One Big Tables (OBTs)...")
    print("-" * 70)

#=================================================================================
# 1. Frontend_Traffic_OBT
#=================================================================================
    Frontend_Traffic_OBT =duckdb.sql("""
    SELECT
        e.id AS event_id,
        e.user_id AS user_id,
        session_id,
        u.created_at AS user_created_at,
        e.created_at AS event_created_at,
        event_type,
        sequence_number,
        browser,
        u.traffic_source AS user_traffic_source,
        e.traffic_source AS event_traffic_source,
        age,
        gender,
        u.state AS user_home_state,
        e.state AS event_ip_state,
        u.city AS user_home_city,
        e.city AS event_ip_city,
        u.postal_code AS user_postal_code,
        latitude,
        longitude,
        uri
    FROM '../dataset/processed/clean_events.parquet' AS e
    LEFT JOIN '../dataset/processed/clean_users.parquet' AS u ON e.user_id = u.id
    ORDER BY user_id
    """)

    count_F_OBT = Frontend_Traffic_OBT.shape[0]
    Frontend_Traffic_OBT.to_parquet('../dataset/processed/Frontend_Traffic_OBT.parquet')
    print(f"[OK] Frontend_Traffic_OBT        : {count_F_OBT:,} records built & saved.")

#=================================================================================
# 2. Backend_Sales_OBT
#=================================================================================
    Backend_Sales_OBT= duckdb.sql("""
    WITH t1 AS(
        SELECT
            ii.id AS inventory_item_id,
            product_id,
            it.id AS order_items_id,
            product_distribution_center_id,
            ii.created_at AS inventory_items_created_at,
            sold_at,
            cost,
            product_category,
            product_name,
            product_brand,
            product_retail_price,
            product_department,
            product_sku,
            order_id,
            user_id,
            status AS items_status,
            it.created_at AS items_created_at,
            shipped_at AS items_shipped_at,
            delivered_at AS items_delivered_at,
            returned_at AS items_returned_at,
            sale_price
        FROM
            '../dataset/processed/clean_inventory_items.parquet' AS ii
        LEFT JOIN
            '../dataset/processed/clean_order_items.parquet' AS it ON ii.id = it.inventory_item_id
        )
    SELECT
        t1.order_id AS order_id,
        order_items_id,
        inventory_item_id,
        product_id,
        t1.user_id AS user_id,
        product_distribution_center_id,
        o.created_at AS order_created_at,
        returned_at AS order_returned_at,
        shipped_at AS order_shipped_at,
        delivered_at AS order_delivered_at,
        items_created_at,
        items_returned_at,
        items_shipped_at,
        items_delivered_at,
        inventory_items_created_at,
        sold_at,
        u.created_at AS user_created_at,
        items_status,
        status AS orders_status,
        cost,
        product_retail_price,
        num_of_item,
        sale_price,
        age,
        u.gender,
        product_brand,
        product_department,
        product_category,
        product_name,
        traffic_source,
        state,
        postal_code,
        country,
        city,
        latitude,
        longitude,
        product_sku
    FROM
        t1
    LEFT JOIN
        '../dataset/processed/clean_orders.parquet' AS o ON t1.order_id = o.order_id
    LEFT JOIN
        '../dataset/processed/clean_users.parquet' AS u ON t1.user_id = u.id
    """)

    count_B_OBT = Backend_Sales_OBT.shape[0]
    Backend_Sales_OBT.to_parquet('../dataset/processed/Backend_Sales_OBT.parquet')
    print(f"[OK] Backend_Sales_OBT           : {count_B_OBT:,} records built & saved.")

    print("-" * 70)
    print("Phase 2 Completed: OBTs generated successfully.\n")

def build_marts():
    print(">>> Phase 3: Generating Data Marts...")
    print("-" * 70)


#=================================================================================
# 1. Mart Financial Summary
#=================================================================================
    mart_financial_summary= duckdb.sql("""
    WITH Base_Metrics AS (
        SELECT
            CONCAT(YEAR(order_created_at), '-Q', QUARTER(order_created_at)) AS year_quarter,
            CONCAT('Q', QUARTER(order_created_at)) AS quarter,
            YEAR(order_created_at) AS year,

            COUNT(DISTINCT user_id) AS active_buyers,
            COUNT(DISTINCT order_id) AS total_orders,
            COUNT(order_items_id) AS total_items_sold,

            SUM(CASE WHEN items_status = 'Returned' THEN 1 ELSE 0 END) AS returned_items_count,

            SUM(sale_price) AS GMV,
            SUM(CASE WHEN items_status = 'Returned' THEN sale_price ELSE 0 END) AS return_amount,
            
            SUM(CASE WHEN items_status NOT IN ('Returned', 'Cancelled') THEN sale_price ELSE 0 END) AS net_revenue,
            SUM(CASE WHEN items_status NOT IN ('Returned', 'Cancelled') THEN cost ELSE 0 END) AS COGS

        FROM '../dataset/processed/Backend_Sales_OBT.parquet'
        WHERE user_id IS NOT NULL
        GROUP BY YEAR(order_created_at), QUARTER(order_created_at)
    )

    SELECT
        year_quarter,
        quarter,
        year,
        active_buyers,
        total_orders,
        total_items_sold,

        ROUND(return_amount, 2) AS return_amount,
        ROUND(GMV, 2) AS GMV,
        ROUND(net_revenue, 2) AS net_revenue,
        ROUND(COGS, 2) AS COGS,
        ROUND(net_revenue - COGS, 2) AS gross_profit,

        ROUND(100.0 * (net_revenue - COGS) / NULLIF(net_revenue, 0), 2) AS gross_margin_pct,
        ROUND(GMV / NULLIF(total_orders, 0), 2) AS AOV,
        ROUND(net_revenue / NULLIF(active_buyers, 0), 2) AS ARPU,
        ROUND(100.0 * returned_items_count / NULLIF(total_items_sold, 0), 2) AS return_rate_pct,

    FROM Base_Metrics
    ORDER BY Year, Quarter
    """)

    count_mart_financial_summary = mart_financial_summary.shape[0]
    mart_financial_summary.to_parquet('../dataset/processed/mart_financial_summary.parquet')
    print(f"[OK] mart_financial_summary          : {count_mart_financial_summary:,} records built & saved.")

    
#=================================================================================
# 2. Mart RFM Segmentation
#=================================================================================
    mart_rfm_segmentation= duckdb.sql("""
    WITH Max_Date AS (
        SELECT MAX(order_created_at) AS global_max_date
        FROM '../dataset/processed/Backend_Sales_OBT.parquet'
    ),
    RFM_Base AS (
        SELECT 
            CONCAT(YEAR(order_created_at), '-Q', QUARTER(order_created_at)) AS Year_Quarter,
            user_id,
            DATEDIFF('day', MAX(order_created_at), (SELECT global_max_date FROM Max_Date)) AS recency,
            COUNT(DISTINCT order_id) AS frequency,
            ROUND(SUM(sale_price), 2) AS monetary
        FROM '../dataset/processed/Backend_Sales_OBT.parquet'
        WHERE items_status NOT IN ('Cancelled','Returned') 
        AND user_id IS NOT NULL 
        AND order_created_at >= (SELECT global_max_date - INTERVAL 1 YEAR FROM Max_Date)
        GROUP BY user_id, YEAR(order_created_at), QUARTER(order_created_at)
    ),
    RFM_Scores AS (
        SELECT 
            *,
            NTILE(5) OVER (PARTITION BY Year_Quarter ORDER BY recency DESC) AS r_score,
            NTILE(5) OVER (PARTITION BY Year_Quarter ORDER BY frequency ASC) AS f_score,
            NTILE(5) OVER (PARTITION BY Year_Quarter ORDER BY monetary ASC) AS m_score
        FROM RFM_Base
    )
    SELECT 
        *,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score = 1 AND f_score >= 4 AND m_score >= 4 THEN 'Cant Lose Them' 
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyalists'
            WHEN r_score >= 4 AND f_score = 1 THEN 'New Customers'
            WHEN r_score >= 3 AND f_score <= 3 THEN 'Potential Loyalists' 
            WHEN r_score IN (2, 3) AND f_score IN (2, 3) THEN 'Need Attention'
            WHEN r_score <= 2 AND f_score >= 2 AND m_score >= 2 THEN 'At Risk'
            WHEN r_score <= 2 AND f_score >= 4 AND m_score <= 2 THEN 'Lost Bargain Hunters'
            WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN 'Hibernating / Lost'
            ELSE 'Others' 
        END AS rfm_segment
    FROM RFM_Scores
    ORDER BY Year_Quarter, r_score DESC, f_score DESC, m_score DESC
    """)

    count_mart_rfm_segmentation = mart_rfm_segmentation.shape[0]
    mart_rfm_segmentation.to_parquet('../dataset/processed/mart_rfm_segmentation.parquet')
    print(f"[OK] mart_rfm_segmentation           : {count_mart_rfm_segmentation:,} records built & saved.")


#=================================================================================
# 3. Mart Logistics Experience
#=================================================================================
    mart_logistics_experience= duckdb.sql("""
    SELECT
        user_id,
        order_id,
        COUNT(DISTINCT order_items_id) AS total_items,
        COUNT(DISTINCT product_distribution_center_id) AS total_dc,
        DATEDIFF('hour',MIN(order_created_at),MAX(items_delivered_at)) AS total_fulfillment_time_hours,
        MAX(CASE WHEN orders_status = 'Returned' THEN 1 ELSE 0 END) AS return_flag
    FROM
        '../dataset/processed/Backend_Sales_OBT.parquet'
    WHERE
        user_id IS NOT NULL AND items_delivered_at IS NOT NULL 
    GROUP BY
        order_id,user_id
    ORDER BY user_id 
    """)

    count_mart_logistics_experience = mart_logistics_experience.shape[0]
    mart_logistics_experience.to_parquet('../dataset/processed/mart_logistics_experience.parquet')
    print(f"[OK] mart_logistics_experience       : {count_mart_logistics_experience:,} records built & saved.")


#=================================================================================
# 4. Mart Experimentation Base
#=================================================================================
    mart_experimentation_base= duckdb.sql("""
    WITH frontend_agg AS (
        SELECT 
            user_id,
            ANY_VALUE(user_traffic_source) AS experiment_group,
            COUNT(event_id) AS total_page_view
        FROM '../dataset/processed/Frontend_Traffic_OBT.parquet'
        WHERE user_id != 0
        GROUP BY user_id
    ),
    backend_agg AS (
        SELECT
            user_id,
            SUM(sale_price) AS total_spend
        FROM '../dataset/processed/Backend_Sales_OBT.parquet'
        GROUP BY user_id
    )
    SELECT
        f.user_id,
        f.experiment_group,
        f.total_page_view,
        CASE WHEN b.user_id IS NOT NULL THEN 1 ELSE 0 END AS is_converted,
        COALESCE(b.total_spend, 0) AS total_spend
    FROM frontend_agg AS f
    LEFT JOIN backend_agg AS b 
        ON f.user_id = b.user_id
    ORDER BY user_id
    """)

    count_mart_experimentation_base = mart_experimentation_base.shape[0]
    mart_experimentation_base.to_parquet('../dataset/processed/mart_experimentation_base.parquet')
    print(f"[OK] mart_experimentation_base       : {count_mart_experimentation_base:,} records built & saved.")


#=================================================================================
# 5. Mart Impulse Penalty
#=================================================================================
    mart_impulse_penalty = duckdb.sql("""
    WITH session_aggregated AS (
        SELECT 
            session_id,
            MAX(user_id) AS user_id, 
            DATE_DIFF('minute', MIN(event_created_at), MAX(event_created_at)) AS session_duration_minutes,
            COUNT(event_id) AS total_page_views,
            SUM(CASE WHEN event_type IN ('product', 'cart', 'department') THEN 1 ELSE 0 END) AS high_intent_clicks,
            MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS is_purchase_session,
            MAX(CASE WHEN event_type = 'purchase' THEN event_created_at ELSE NULL END) AS purchase_event_time
        FROM '../dataset/processed/Frontend_Traffic_OBT.parquet'
        GROUP BY session_id
    ),
    intent_tagged AS (
        SELECT 
            session_id,
            user_id,
            session_duration_minutes,
            purchase_event_time,
            CASE 
                WHEN session_duration_minutes < 10 AND total_page_views <= 6 THEN 'Impulse Buyers'
                WHEN session_duration_minutes > 60 OR total_page_views >= 12 THEN 'Heavy Browsers'
                ELSE 'Targeted Searchers'
            END AS user_intent
        FROM session_aggregated
        WHERE is_purchase_session = 1
    ),
    session_with_orders AS (
        SELECT
            i.session_id, 
            i.user_intent, 
            i.session_duration_minutes,
            o.order_id, 
            o.order_items_id,
            CASE WHEN o.items_status = 'Returned' THEN 1 ELSE 0 END AS is_returned,
            CASE WHEN o.items_status IN ('Complete','Returned') THEN 1 ELSE 0 END AS is_delivered,
            o.items_status, 
            o.order_created_at,
            ABS(DATE_DIFF('second', i.purchase_event_time, o.order_created_at)) AS gap_sec  
        FROM intent_tagged i
        JOIN '../dataset/processed/Backend_Sales_OBT.parquet' o
        ON i.user_id = o.user_id
        AND o.order_created_at BETWEEN i.purchase_event_time - INTERVAL 30 MINUTE
                                    AND i.purchase_event_time + INTERVAL 30 MINUTE
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY o.order_items_id
            ORDER BY ABS(DATE_DIFF('second', i.purchase_event_time, o.order_created_at))
        ) = 1
    )
    SELECT
        user_intent AS User_Intent,
        COUNT(*)                         AS items,
        COUNT(DISTINCT session_id)       AS sessions,
        COUNT(DISTINCT order_id)         AS orders,
        SUM(is_returned)                 AS returned_items,
        SUM(is_delivered)                AS delivered_items,
        SUM(is_returned) * 1.0 / COUNT(*)                   AS return_rate_all_items,
        SUM(is_returned) * 1.0 / NULLIF(SUM(is_delivered), 0) AS return_rate_delivered,
        AVG(LEAST(session_duration_minutes, 120))           AS avg_session_mins
    FROM session_with_orders
    GROUP BY user_intent
    """)

    count_mart_impulse_penalty = mart_impulse_penalty.shape[0]
    mart_impulse_penalty.to_parquet('../dataset/processed/mart_impulse_penalty.parquet')
    print(f"[OK] mart_impulse_penalty            : {count_mart_impulse_penalty:,} records built & saved.")
    print("-" * 70)
    print("Phase 3 Completed: All Data Marts are ready for BI reporting.")

def main():
    print("Starting TheLook E-Commerce ETL Pipeline...")
    start_time = time.time()
    
    clean_data()
    build_obts()
    build_marts()
    
    end_time = time.time()
    print(f"\nETL Pipeline finished successfully in {end_time - start_time:.2f} seconds!")

if __name__ == "__main__":
    main()

