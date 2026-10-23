-- Sales analysis: monthly sales trend
-- only 'delivered' orders are counted.

SELECT
    strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,
    ROUND(SUM(oi.price), 2)                       AS total_sales,
    COUNT(DISTINCT o.order_id)                    AS order_count
FROM olist_orders      AS o
JOIN olist_order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL
GROUP BY order_month
ORDER BY order_month;