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
metadata = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Import the necessary libraries
import json

# Check if the metadata parameter is present
try:
    json.loads(metadata)
except ValueError as e:
    mssparkutils.notebook.exit("Metadata is not a valid JSON object.")

json_metadata = json.loads(metadata)

# Load data and convert DataFrame
df = spark.read.table(f'bronze.{schemaName}.{tableName}')

# Check if columns in metadata exist in the DataFrame
missing_columns = [item["ColumnName"] for item in json_metadata \
if item["ColumnName"] not in df.columns]

# If columns are missing, stop the process
if missing_columns:
    mssparkutils.notebook.exit(f"Technical validations have failed: " \
    + join(missing_columns))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
