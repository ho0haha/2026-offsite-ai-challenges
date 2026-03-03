-- This query finds the top 10 products by total revenue from completed orders
-- in 2025, along with the number of distinct customers who ordered each product.
-- It is intentionally unoptimized. Do NOT modify this file.

SELECT
    p.name AS product_name,
    p.category,
    SUM(oi.quantity * oi.unit_price) AS total_revenue,
    COUNT(DISTINCT o.customer_name) AS unique_customers,
    SUM(oi.quantity) AS total_quantity
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN products p ON p.id = oi.product_id
WHERE o.status = 'completed'
  AND o.order_date >= '2025-01-01'
  AND o.order_date < '2026-01-01'
  AND p.active = 1
  AND oi.product_id IN (
      SELECT product_id
      FROM order_items
      WHERE order_id IN (
          SELECT id FROM orders WHERE status = 'completed'
      )
      GROUP BY product_id
      HAVING SUM(quantity) > 10
  )
GROUP BY p.id, p.name, p.category
ORDER BY total_revenue DESC
LIMIT 10;
