# Databricks notebook source
# MAGIC %run ./Includes/Configuration

# COMMAND ----------

spark.conf.set("spark.sql.shuffle.partitions", 8)

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql.functions import *

body_schema = StructType([
    StructField("Body", BinaryType(), True)
])

# COMMAND ----------

stock_df = (
  spark 
    .readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "avro")
    .schema(body_schema)
    .load("/mnt/bronze-crypto/crypto-eventhub201/*")
)

# COMMAND ----------

raw_event = stock_df.select(stock_df.Body.cast("string"))

# COMMAND ----------

stock_schema = StructType([
  StructField("data", ArrayType(
      StructType([
          StructField("p", DoubleType(), True),
          StructField("s", StringType(), True),
          StructField("t", StringType(), True)
      ])
   ), True)
])


# COMMAND ----------

from pyspark.sql.functions import *

event_exp = raw_event.withColumn(
   "Body",
    from_json(col("Body"), stock_schema)
)

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql.functions import *

flat_schema_stock = (
    event_exp.select(explode("Body.data").alias("data"))
        .select(col("data.p").alias("current_price"),
                col("data.s").alias("abbreviation"),
                to_utc_timestamp(from_unixtime((col("data.t") / 1000), "yyyy-MM-dd HH:mm:ss"), "UTC-3").alias("date"))
    .withColumn("year", year(col("date")))
    .withColumn("month", month(col("date")))
    .withColumn("day", dayofmonth(col("date")))
    .withColumn("hour", hour(col("date")))
    .withColumn("minute", minute(col("date")))
    .withColumn("second", second(col("date")))
)

# COMMAND ----------

from pyspark.sql.functions import *

silver_df = (
    flat_schema_stock
    .select(
        col("current_price"),
        col("abbreviation"),
        col("date"),
        col("year"),
        col("month"),
        col("day"),
        col("hour"),
        col("minute"),
        col("second")
      )
  .dropDuplicates(["abbreviation", "date"])
)

# COMMAND ----------

silver_query = (
silver_df.writeStream
  .partitionBy("year", "month", "day", "hour", "minute", "second")
  .format("delta")
  .trigger(once=True)
  .option("checkpointLocation", silver_check)
  .start(silver_output)
)

# COMMAND ----------

display(spark.read.format("delta").load(silver_output))

# COMMAND ----------

