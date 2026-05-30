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

# Set up the session for V-Order writing
"spark.sql.parquet.vorder.enabled", "true"
"spark.microsoft.delta.optimizeWrite.enabled", "true"
"spark.microsoft.delta.optimizeWrite.binSize", "1073741824"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import *

# Load data to the DataFrame
address = spark.read.table("silver.adventureworks.hist_address") \
.where(col("current") == True)
address = address.dropDuplicates(["AddressID"])
address = address[["AddressID", "AddressLine1", "AddressLine2", \
"City", "StateProvince", "CountryRegion"]]

# Add hash code using all selected columns
dimension_address = address.withColumn("ID", \
sha2(concat_ws("||", *address.columns), 256))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from delta.tables import *

deltaTable = DeltaTable.forPath(spark, \
'Tables/adventureworks/dimension_address')

deltaTable.alias('gold') \
  .merge(
    dimension_address.alias('updates'),
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
      "AddressID": "updates.AddressID",
      "AddressLine1": "updates.AddressLine1",
      "AddressLine2": "updates.AddressLine2",
      "City": "updates.City",
      "StateProvince": "updates.StateProvince",
      "CountryRegion": "updates.CountryRegion",
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
