# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "84f526ef-641b-4465-89b7-2e8d35904975",
# META       "default_lakehouse_name": "bronze",
# META       "default_lakehouse_workspace_id": "89ed2ee4-2011-47c8-a88a-eaa6b2308f33",
# META       "known_lakehouses": [
# META         {
# META           "id": "84f526ef-641b-4465-89b7-2e8d35904975"
# META         }
# META       ]
# META     }
# META   }
# META }

# PARAMETERS CELL ********************

# Infer base parameters from the pipeline context
schemaName = ""
tableName = ""
filePath = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Import functions
from pyspark.sql.functions import current_date

# Create schema
spark.sql(f'CREATE SCHEMA IF NOT EXISTS {schemaName}')

# Drop table
spark.sql(f'DROP TABLE IF EXISTS {schemaName}.{tableName}')

# Read data
df = spark.read.parquet(f"Files/{schemaName}/{filePath}/{tableName}.parquet")

# Add metadata loading_date column using current date
df = df.withColumn("loading_date", current_date().cast("string"))

# Overwrite table
df.write.mode("Overwrite").saveAsTable(f"{schemaName}.{tableName}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
