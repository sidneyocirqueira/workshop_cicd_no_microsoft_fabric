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

# Load data to the dataframes
product = spark.read.table("silver.adventureworks.hist_product") \
.where(col("current") == True)
product = product.dropDuplicates(["ProductID"])
product = product[["ProductID", "Name", "ProductNumber", \
"Color", "Size", "Weight", "ProductCategoryID", "ProductModelID"]]
category = spark.read.table("silver.adventureworks.hist_productcategory") \
.where(col("current") == True)
category = category.dropDuplicates(["ProductCategoryID"])
category = category[["ProductCategoryID", "Name"]]
category = category.withColumnRenamed("Name", "CategoryName")
model = spark.read.table("silver.adventureworks.hist_productmodel") \
.where(col("current") == True)
model = model.dropDuplicates(["ProductModelID"])
model = model[["ProductModelID", "Name", "CatalogDescription"]]
model = model.withColumnRenamed("Name", "ProductModelName")

# Perform the joins
dimension_product = product.join(category, on="ProductCategoryID", how="left")
dimension_product = dimension_product.join(model, \
on="ProductModelID", how="left")

# Select only the relevant columns
dimension_product = dimension_product[["ProductID", "Name", "ProductNumber", \
"Color", "Size", "Weight" , "CategoryName" , "ProductModelName"]]

# Add hash code using all selected columns
dimension_product = dimension_product.withColumn("ID", \
sha2(concat_ws("||", *dimension_product.columns), 256))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from delta.tables import *

deltaTable = DeltaTable.forPath(spark, \
'Tables/adventureworks/dimension_product')

deltaTable.alias('gold') \
  .merge(
    dimension_product.alias('updates'),
    'gold.ID = updates.ID'
  ).whenMatchedUpdate(set =
    {
      "current_flag": lit("1"),
      "current_date": current_date(),
      "end_date": """to_date('9999-12-31', 'yyyy-MM-dd')"""
    }
  ).whenNotMatchedInsert(values =
    {
      "ID": "updates.ID",
      "ProductID": "updates.ProductID",
      "ProductNumber": "updates.ProductNumber",
      "Color": "updates.Color",
      "Size": "updates.Size",
      "Weight": "updates.Weight",
      "CategoryName": "updates.CategoryName",
      "ProductModelName": "updates.ProductModelName",
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
