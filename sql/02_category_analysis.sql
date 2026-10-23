-- Category analysis: top product categories by sales
-- only 'delivered' orders are counted.

SELECT
    COALESCE(t.product_category_name_english, p.product_category_name) AS category,
    ROUND(SUM(oi.price), 2) AS total_sales,
    COUNT(DISTINCT oi.order_id) AS order_count
FROM olist_order_items AS oi
JOIN olist_products AS p ON p.product_id = oi.product_id
LEFT JOIN product_category_name_translation AS t ON t.product_category_name = p.product_category_name
JOIN olist_orders AS o ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY category
ORDER BY total_sales DESC
LIMIT 10;