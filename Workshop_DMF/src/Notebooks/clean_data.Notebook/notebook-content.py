# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "e73a38c2-7caf-43be-9601-37cf398bfaac",
# META       "default_lakehouse_name": "silver",
# META       "default_lakehouse_workspace_id": "89ed2ee4-2011-47c8-a88a-eaa6b2308f33",
# META       "known_lakehouses": [
# META         {
# META           "id": "e73a38c2-7caf-43be-9601-37cf398bfaac"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# Import necessary libraries
from pyspark.sql.functions import *
from pyspark.sql.types import StringType
from notebookutils import credentials
from Pathlib import Path

# Create database
spark.sql(f'CREATE SCHEMA IF NOT EXISTS adventureworks')

# Load data
customers = spark.read.table("bronze.adventureworks.customer")

# Drop columns that are not needed
customers = customers.drop("PasswordHash", "PasswordSalt", "rowguid", "ModifiedDate")

# Function to determine gender  
def determine_gender_udf(title):  
    if title == 'Mr.':  
        return 'Male'  
    elif title == 'Ms.':  
        return 'Female'  
    else:
        return 'Unknown'  # Add a default value for other cases

determine_gender_udf = udf(determine_gender_udf, StringType())

# Adding gender to each dictionary in the list
customers = customers.withColumn("Gender", \
determine_gender_udf(trim(customers["Title"])))

# Define the strip_prefix function
def strip_prefix(value):
    return value.strip("adventure-works\\")

# Define the strip_prefix_udf function
strip_prefix_udf = udf(strip_prefix, StringType())

# Updating SalesPerson in each dictionary in the list  
customers = customers.withColumn("SalesPerson", \
strip_prefix_udf(customers["SalesPerson"]))

# Making all telephone numbers consistent
customers = customers.withColumn("Phone", \
regexp_replace(customers["Phone"], r"1 \(\d{2}\) ", ""))

# Write customers data
customers.write.mode("Overwrite").saveAsTable("adventureworks.clean_customer")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load data
address = spark.read.table("bronze.adventureworks.address")

# Drop columns that are not needed
address = address.drop("rowguid")

# Write address data
address.write.mode("Overwrite").saveAsTable("adventureworks.clean_address")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load data
customeraddress = spark.read.table("bronze.adventureworks.customeraddress")

# Drop columns that are not needed
customeraddress = customeraddress.drop("rowguid")

# Write customeraddress data
customeraddress.write.mode("Overwrite").saveAsTable("adventureworks.clean_customeraddress")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load data
product = spark.read.table("bronze.adventureworks.product")

# Drop columns that are not needed
product = product.drop("rowguid")

# Write product data
product.write.mode("Overwrite").saveAsTable("adventureworks.clean_product")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load data
productcategory = spark.read.table("bronze.adventureworks.productcategory")

# Drop columns that are not needed
productcategory = productcategory.drop("rowguid")

# Write productcategory data
productcategory.write.mode("Overwrite").saveAsTable("adventureworks.clean_productcategory")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load data
productdescription = spark.read.table("bronze.adventureworks.productdescription")

# Drop columns that are not needed
productdescription = productdescription.drop("rowguid")

# Write productdescription data
productdescription.write.mode("Overwrite").saveAsTable("adventureworks.clean_productdescription")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load data
productmodel = spark.read.table("bronze.adventureworks.productmodel")

# Drop columns that are not needed
productmodel = productmodel.drop("rowguid")

# Write productmodel data
productmodel.write.mode("Overwrite").saveAsTable("adventureworks.clean_productmodel")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load data
productmodelproductdescription = spark.read.table("bronze.adventureworks.productmodelproductdescription")

# Drop columns that are not needed
productmodelproductdescription = productmodelproductdescription.drop("rowguid")

# Write productmodelproductdescription data
productmodelproductdescription.write.mode("Overwrite").saveAsTable("adventureworks.clean_productmodelproductdescription")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load data
salesorderdetail = spark.read.table("bronze.adventureworks.salesorderdetail")

# Drop columns that are not needed
salesorderdetail = salesorderdetail.drop("rowguid")

# Write salesorderdetail data
salesorderdetail.write.mode("Overwrite").saveAsTable("adventureworks.clean_salesorderdetail")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load data
salesorderheader = spark.read.table("bronze.adventureworks.salesorderheader")

# Drop columns that are not needed
salesorderheader = salesorderheader.drop("rowguid")

# Write salesorderheader data
salesorderheader.write.mode("Overwrite").saveAsTable("adventureworks.clean_salesorderheader")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
