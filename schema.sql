/* CONTEXT: E-Commerce Analytics Database 
  PROJECT: my-gcp-project
  DATASET: ecommerce_prod
*/

CREATE TABLE `my-gcp-project.ecommerce_prod.users` (
  user_id INT64 NOT NULL OPTIONS(description="Unique identifier for the user"),
  email STRING,
  signup_date DATE OPTIONS(description="Date when the user registered"),
  country STRING,
  -- Nested struct to test AI's ability to access dot-notation (e.g., address.zip_code)
  address STRUCT<
    city STRING,
    state STRING,
    zip_code STRING
  >,
  is_prime_member BOOL OPTIONS(description="True if the user has a premium subscription")
)
PARTITION BY signup_date
CLUSTER BY country;

CREATE TABLE `my-gcp-project.ecommerce_prod.products` (
  product_id INT64 NOT NULL,
  product_name STRING,
  category STRING,
  price FLOAT64,
  cost FLOAT64,
  -- Array to test UNNEST logic
  tags ARRAY<STRING> OPTIONS(description="List of search tags, e.g., ['summer', 'sale']")
);

CREATE TABLE `my-gcp-project.ecommerce_prod.orders` (
  order_id INT64 NOT NULL,
  user_id INT64,
  order_ts TIMESTAMP OPTIONS(description="UTC Timestamp of the purchase"),
  status STRING OPTIONS(description="Values: 'PENDING', 'SHIPPED', 'CANCELLED', 'RETURNED'"),
  total_amount FLOAT64,
  -- Nested & Repeated field (The ultimate SQL test)
  items ARRAY<STRUCT<
    product_id INT64,
    quantity INT64,
    price_at_purchase FLOAT64
  >>
)
PARTITION BY DATE(order_ts)
CLUSTER BY status;

CREATE TABLE `my-gcp-project.ecommerce_prod.web_events` (
  event_id STRING,
  user_id INT64,
  session_id STRING,
  event_name STRING OPTIONS(description="e.g., 'view_item', 'add_to_cart', 'checkout'"),
  event_ts TIMESTAMP,
  page_url STRING,
  device_type STRING
)
PARTITION BY DATE(event_ts);

