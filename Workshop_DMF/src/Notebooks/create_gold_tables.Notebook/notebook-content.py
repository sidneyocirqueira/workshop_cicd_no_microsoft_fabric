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

from pyspark.sql.types import *
from notebookutils import credentials 

# Create the schema
spark.sql(f'CREATE SCHEMA IF NOT EXISTS adventureworks')

# Define the schema for address
schemaAddress = StructType([
    StructField("ID", StringType()),
    StructField("AddressID", IntegerType()),
    StructField("AddressLine1", StringType()),
    StructField("AddressLine2", StringType()),
    StructField("City", StringType()),
    StructField("StateProvince", StringType()),
    StructField("CountryRegion", StringType()),
    StructField("current_flag", BooleanType()),
    StructField("current_date", DateType()),
    StructField("end_date", DateType())
])

# Create the DataFrame
dfAddress = spark.createDataFrame([], schemaAddress)

# Create the table
dfAddress.write.mode("append").saveAsTable("adventureworks.dimension_address")

# Define the schema for customer
schemaCustomer = StructType([
    StructField("ID", StringType()),
    StructField("CustomerID", IntegerType()),
    StructField("Title", StringType()),
    StructField("FirstName", StringType()),
    StructField("MiddleName", StringType()),
    StructField("LastName", StringType()),
    StructField("CompanyName", StringType()),
    StructField("EmailAddress", StringType()),
    StructField("Phone", StringType()),
    StructField("current_flag", BooleanType()),
    StructField("current_date", DateType()),
    StructField("end_date", DateType())
])

# Create the DataFrame
dfCustomer = spark.createDataFrame([], schemaCustomer)

# Create the table
dfCustomer.write.mode("append").saveAsTable("adventureworks.dimension_customer")

# Define the schema for date
schemaDate = StructType([
    StructField("ID", StringType()),
    StructField("OrderDate", DateType()),
    StructField("Day", IntegerType()),
    StructField("Month", IntegerType()),
    StructField("Year", IntegerType())
])

# Create the DataFrame
dfDate = spark.createDataFrame([], schemaDate)

# Create the table
dfDate.write.mode("append").saveAsTable("adventureworks.dimension_date")

# Define the schema for product
schemaProduct = StructType([
    StructField("ID", StringType()),
    StructField("ProductID", IntegerType()),
    StructField("ProductNumber", StringType()),
    StructField("Color", StringType()),
    StructField("Size", StringType()),
    StructField("Weight", StringType()),
    StructField("CategoryName", StringType()),
    StructField("ProductModelName", StringType()),
    StructField("current_flag", BooleanType()),
    StructField("current_date", DateType()),
    StructField("end_date", DateType())
])

# Create the DataFrame
dfProduct = spark.createDataFrame([], schemaProduct)

# Create the table
dfProduct.write.mode("append").saveAsTable("adventureworks.dimension_product")

# Define the schema for sales
schemaSales = StructType([
    StructField("SalesKey", StringType()),
    StructField("AddressKey", StringType()),
    StructField("CustomerKey", StringType()),
    StructField("ProductKey", StringType()),
    StructField("DateKey", StringType()),
    StructField("Revenue", DoubleType()),
    StructField("OrderQty", IntegerType()),
    StructField("UnitPrice", DoubleType()),
    StructField("current_flag", BooleanType()),
    StructField("current_date", DateType()),
    StructField("end_date", DateType())
])

# Create the DataFrame
dfSales = spark.createDataFrame([], schemaSales)

# Create the table
dfSales.write.mode("append").saveAsTable("adventureworks.fact_sales")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
