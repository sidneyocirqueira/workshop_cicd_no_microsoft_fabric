# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "289c0390-715e-40e1-bc15-fe27c9ad31f6",
# META       "default_lakehouse_name": "gold",
# META       "default_lakehouse_workspace_id": "89ed2ee4-2011-47c8-a88a-eaa6b2308f33",
# META       "known_lakehouses": [
# META         {
# META           "id": "289c0390-715e-40e1-bc15-fe27c9ad31f6"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql.functions import *
import notebookutils 

# Load data to the dataframes
orderdetail = spark.read.table("silver.adventureworks.hist_salesorderdetail") \
.where(col("current") == True)
orderdetail = orderdetail.dropDuplicates(["SalesOrderID"])
orderdetail = orderdetail[["SalesOrderID", "SalesOrderDetailID", \
"ProductID", "OrderQty", "UnitPrice"]]
orderdetail = orderdetail \
.withColumn("Revenue",orderdetail["OrderQty"] \
* orderdetail["UnitPrice"] )

orderheader = spark.read.table("silver.adventureworks.hist_salesorderheader") \
.where(col("current") == True)
orderheader = orderheader.dropDuplicates(["SalesOrderID"])
orderheader = orderheader[["SalesOrderID", "CustomerID", \
"BillToAddressID", "OrderDate"]]
orderheader = orderheader \
.withColumnRenamed("SalesOrderID", "SalesOrderID2")

# Perform the joins
sales = orderdetail.join(orderheader, \
orderdetail['SalesOrderID'] == orderheader['SalesOrderID2'], "left")

sales = sales.withColumn('SalesKey', concat(sales['SalesOrderID'], \
sales['SalesOrderDetailID']))

# Select only the relevant columns
sales = sales[["SalesKey", "ProductID", "CustomerID", \
"BillToAddressID", "Revenue", "OrderDate", "OrderQty", "UnitPrice"]]

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load the current data from the dimension tables
dimension_address = spark.read.table("adventureworks.dimension_address") \
.where(col("current_flag") == True)
dimension_customer = spark.read.table("adventureworks.dimension_customer") \
.where(col("current_flag") == True)
dimension_product = spark.read.table("adventureworks.dimension_product") \
.where(col("current_flag") == True)
dimension_date = spark.read.table("adventureworks.dimension_date")

# Join the fact table with the dimension tables using the business keys
fact_sales = sales.join(dimension_address,(sales.BillToAddressID \
    == dimension_address.AddressID), "left") \
    .join(dimension_customer,(sales.CustomerID \
    == dimension_customer.CustomerID), "left") \
    .join(dimension_product,(sales.ProductID \
    == dimension_product.ProductID), "left") \
    .join(dimension_date,(sales.OrderDate \
    == dimension_date.OrderDate), "left") \
    .select(col("dimension_address.ID").alias("AddressKey"), \
    col("dimension_customer.ID").alias("CustomerKey"), \
    col("dimension_product.ID").alias("ProductKey"), \
    col("dimension_date.ID").alias("DateKey"), \
    col("SalesKey"), col("Revenue"), col("OrderQty"), col("UnitPrice"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from delta.tables import *

deltaTable = DeltaTable.forPath(spark, \
'Tables/adventureworks/fact_sales')

deltaTable.alias('gold') \
  .merge(
    fact_sales.alias('updates'),
    'gold.SalesKey = updates.SalesKey \
    AND gold.AddressKey = updates.AddressKey \
    AND gold.CustomerKey = updates.CustomerKey \
    AND gold.ProductKey = updates.ProductKey \
    AND gold.DateKey = updates.DateKey' \
  ).whenMatchedUpdate(set =
    {
      "current_flag": lit("1"),
      "current_date": current_date(),
      "end_date": """to_date('9999-12-31', 'yyyy-MM-dd')"""
    }
  ).whenNotMatchedInsert(values =
    {
      "SalesKey": "updates.SalesKey",
      "AddressKey": "updates.AddressKey",
      "CustomerKey": "updates.CustomerKey",
      "ProductKey": "updates.ProductKey",
      "DateKey": "updates.DateKey",
      "Revenue": "updates.Revenue",
      "OrderQty": "updates.OrderQty",
      "UnitPrice": "updates.UnitPrice",
      "current_flag": lit("1"),
      "current_date": current_date(),
      "end_date": """to_date('9999-12-31', 'yyyy-MM-dd')"""
    }
  ).whenNotMatchedBySourceUpdate(set =
    {
      "current_flag": lit("0"),
      "end_date": current_date()
    }
  ).execute()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
