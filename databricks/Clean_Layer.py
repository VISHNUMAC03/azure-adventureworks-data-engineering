# Databricks notebook source
# MAGIC %md
# MAGIC # Clean_Layer: raw (bronze) → clean (silver)
# MAGIC
# MAGIC Reads the AdventureWorks CSV files that Azure Data Factory landed in the **raw** container,
# MAGIC applies the cleaning and enrichment rules below with PySpark, and writes each table as
# MAGIC **Parquet** to the **clean** container, where Synapse serverless SQL reads it.
# MAGIC
# MAGIC | Item | Value |
# MAGIC |---|---|
# MAGIC | Workspace | `ADB_AW_PROJECT_VMAC03` |
# MAGIC | Cluster | `AWProjectCluster` |
# MAGIC | Storage account | `awvmac03` (ADLS Gen2) |
# MAGIC | Input | `abfss://raw@awvmac03.dfs.core.windows.net/<Table>/` (CSV) |
# MAGIC | Output | `abfss://clean@awvmac03.dfs.core.windows.net/<Table>/` (Parquet) |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Access to ADLS Gen2 with a service principal
# MAGIC The app registration has the **Storage Blob Data Contributor** role on `awvmac03`.
# MAGIC Its credentials live in a Databricks secret scope, never in the notebook.

# COMMAND ----------

storage_account = "awvmac03"
scope = "aw-project-scope"

client_id = dbutils.secrets.get(scope=scope, key="sp-client-id")
tenant_id = dbutils.secrets.get(scope=scope, key="sp-tenant-id")
client_secret = dbutils.secrets.get(scope=scope, key="sp-client-secret")

host = f"{storage_account}.dfs.core.windows.net"
spark.conf.set(f"fs.azure.account.auth.type.{host}", "OAuth")
spark.conf.set(f"fs.azure.account.oauth.provider.type.{host}",
               "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
spark.conf.set(f"fs.azure.account.oauth2.client.id.{host}", client_id)
spark.conf.set(f"fs.azure.account.oauth2.client.secret.{host}", client_secret)
spark.conf.set(f"fs.azure.account.oauth2.client.endpoint.{host}",
               f"https://login.microsoftonline.com/{tenant_id}/oauth2/token")

RAW = f"abfss://raw@{host}"
CLEAN = f"abfss://clean@{host}"

# COMMAND ----------

from pyspark.sql.functions import (col, concat_ws, count, month, year, regexp_replace,
                                   split, to_timestamp)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Read the raw layer

# COMMAND ----------

def read_raw(folder):
    """Read one table that Data Factory landed in raw/<folder>/."""
    return (spark.read.format("csv")
            .option("header", True)
            .option("inferSchema", True)
            .load(f"{RAW}/{folder}"))


df_cal = read_raw("Calendar")
df_cus = read_raw("Customers")
df_prodcat = read_raw("Product_Categories")
df_prodsubcat = read_raw("Product_Subcategories")
df_prod = read_raw("Products")
df_ret = read_raw("Returns")
df_ter = read_raw("Territories")
df_sales = read_raw("Sales_*")          # Sales_2015, Sales_2016 and Sales_2017 in one DataFrame

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Transformations

# COMMAND ----------

# Calendar: add Month and Year so the gold layer can group by them directly.
df_cal = (df_cal
          .withColumn("Month", month(col("Date")))
          .withColumn("Year", year(col("Date"))))
df_cal.display()

# COMMAND ----------

# Customers: build a single full-name column from prefix, first and last name.
df_cus = df_cus.withColumn("fullName",
                           concat_ws(" ", col("Prefix"), col("FirstName"), col("LastName")))
df_cus.display()

# COMMAND ----------

# Products: keep the SKU family (text before the first "-") and the first word of the name.
df_prod = (df_prod
           .withColumn("ProductSKU", split(col("ProductSKU"), "-")[0])
           .withColumn("ProductName", split(col("ProductName"), " ")[0]))
df_prod.display()

# COMMAND ----------

# Sales: typed stock timestamp, order numbers re-prefixed S → T, and a line-level multiplier.
df_sales = (df_sales
            .withColumn("StockDate", to_timestamp(col("StockDate")))
            .withColumn("OrderNumber", regexp_replace(col("OrderNumber"), "S", "T"))
            .withColumn("multiply", col("OrderLineItem") * col("OrderQuantity")))
df_sales.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Quick analysis before publishing

# COMMAND ----------

# Orders per day
df_sales.groupBy("OrderDate").agg(count("OrderNumber").alias("total_orders")).display()

# COMMAND ----------

# Rows per product category and per territory
df_prodcat.display()
df_ter.display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Write the clean (silver) layer as Parquet
# MAGIC `overwrite` keeps the notebook safe to re-run without duplicating rows.

# COMMAND ----------

tables = {
    "Calendar": df_cal,
    "Customers": df_cus,
    "Product_Categories": df_prodcat,
    "Product_Subcategories": df_prodsubcat,
    "Products": df_prod,
    "Returns": df_ret,
    "Territories": df_ter,
    "Sales": df_sales,
}

for name, df in tables.items():
    (df.write.format("parquet")
       .mode("overwrite")
       .option("path", f"{CLEAN}/{name}")
       .save())
    print(f"wrote {name}: {df.count():,} rows → {CLEAN}/{name}")
