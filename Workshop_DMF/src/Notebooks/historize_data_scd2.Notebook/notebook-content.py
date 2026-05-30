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

# Import functions
from pyspark import *
from pyspark.sql import functions as F
from pyspark.sql.functions import *
import datetime

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# SCD2 function
def fn_SCD2(schemaName, tableName, primaryKey):

    # Fetch data from Bronze or intermediate Silver layer
    dataChanged = spark.read.table(f"{schemaName}.clean_{tableName}")

    # Remove loading_date column from dataset
    dataChanged = dataChanged.drop('loading_date')

    # Generate a hash key if the primary key is missing
    if not primaryKey or primaryKey == "":
        dataChanged = dataChanged.withColumn("hash", \
        sha2(concat_ws("||", *dataChanged.columns), 256))
        primaryKey = 'hash'

    # Create list with all columns
    columnNames = dataChanged.schema.names

    # Set date
    current_date = datetime.date.today()

    # Try and read existing dataset
    try:
        # Read original data - this is your SCD2 table holding all data
        dataOriginal = spark.read.table(f"{schemaName}.hist_{tableName}")
    except:
        # Use first load when no data exists yet
        newOriginalData = dataChanged.withColumn('current', lit(True)) \
        .withColumn('effectiveDate', lit(current_date)) \
        .withColumn('endDate', lit(datetime.date(9999, 12, 31)))
        newOriginalData.write.format("delta").mode("overwrite") \
        .saveAsTable(f"{schemaName}.hist_{tableName}")

    # Read original data - this is your SCD2 table holding all data
    dataOriginal = spark.read.table(f"{schemaName}.hist_{tableName}")

    # Rename all columns in dataChanged, prepend src_ to column names
    df_new = dataChanged.select([F.col(c).alias("src_"+c) \
    for c in dataChanged.columns])
    src_columnNames = df_new.schema.names
    df_new2 = df_new.withColumn('src_current', lit(True)) \
    .withColumn('src_effectiveDate', lit(current_date)) \
    .withColumn('src_endDate', lit(datetime.date(9999, 12, 31)))

    # Create dynamic columns
    src_primaryKey = 'src_' + primaryKey

    # FULL Merge, join on key column and also
    # date column to make only join to the latest records
    df_merge = dataOriginal.join(df_new2, (df_new2[src_primaryKey] \
    == dataOriginal[primaryKey]), how='fullouter')

    # Derive new column to indicate the action
    df_merge = df_merge.withColumn('action',
        when(concat_ws('+', *columnNames) == \
        concat_ws('+', *src_columnNames), 'NOACTION')
        .when(df_merge.current == False, 'NOACTION')
        .when(df_merge[src_primaryKey].isNull() & df_merge.current, 'DELETE')
        .when(df_merge[src_primaryKey].isNull(), 'INSERT')
        .otherwise('UPDATE')
    )

    # Generate target selections based on action codes
    column_names = columnNames + ['current', 'effectiveDate', 'endDate']
    src_column_names = src_columnNames + ['src_current', \
    'src_effectiveDate', 'src_endDate']

    # For records that needs no action
    df_merge_p1 = df_merge.filter(df_merge.action == \
    'NOACTION').select(column_names)

    # For records that needs insert only
    df_merge_p2 = df_merge.filter(df_merge.action == \
    'INSERT').select(src_column_names)
    df_merge_p2_1 = df_merge_p2.select([F.col(c) \
    .alias(c.replace(c[0:4], "")) for c in df_merge_p2.columns])

    # For records that needs to be deleted
    df_merge_p3 = df_merge.filter(df_merge.action == \
    'DELETE').select(column_names).withColumn('current', lit(False)) \
    .withColumn('endDate', lit(current_date))

    # For records that needs to be expired and then inserted
    df_merge_p4_1 = df_merge.filter(df_merge.action == \
    'UPDATE').select(src_column_names)
    df_merge_p4_2 = df_merge_p4_1.select([F.col(c) \
    .alias(c.replace(c[0:4], "")) for c in df_merge_p2.columns])

    # Replace src_ alias in all columns
    df_merge_p4_3 = df_merge.filter(df_merge.action == \
    'UPDATE').withColumn('endDate', date_sub(df_merge.src_effectiveDate, 1)) \
    .withColumn('current', lit(False)).select(column_names)

    # Union all records together
    df_merge_final = df_merge_p1.unionAll(df_merge_p2) \
    .unionAll(df_merge_p3).unionAll(df_merge_p4_2).unionAll(df_merge_p4_3)

    # At last, you can overwrite existing data using this new DataFrame
    df_merge_final.write.format("delta").mode("overwrite") \
    .saveAsTable(schemaName + ".hist_" + tableName)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

fn_SCD2("adventureworks","address","AddressID")
fn_SCD2("adventureworks","customer","CustomerID")
fn_SCD2("adventureworks","customeraddress","")
fn_SCD2("adventureworks","product","ProductID")
fn_SCD2("adventureworks","productcategory","ProductCategoryID")
fn_SCD2("adventureworks","productdescription","ProductDescriptionID")
fn_SCD2("adventureworks","productmodel","ProductModelID")
fn_SCD2("adventureworks","productmodelproductdescription","")
fn_SCD2("adventureworks","salesorderdetail","")
fn_SCD2("adventureworks","salesorderheader","SalesOrderID")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
