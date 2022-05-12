# Databricks notebook source
# MAGIC %md
# MAGIC ## ![Spark Logo Tiny](https://files.training.databricks.com/images/105/logo_spark_tiny.png) Install packages for FinnHub API and EventHub

# COMMAND ----------

# MAGIC %pip install websocket
# MAGIC %pip install websocket-client
# MAGIC %pip install azure-eventhub

# COMMAND ----------

token="c694osiad3i87ccnocgg"

# COMMAND ----------

import websocket
from azure.eventhub import EventHubProducerClient, EventData

def on_message(ws, message):
    producer = EventHubProducerClient.from_connection_string(
    conn_str=dbutils.secrets.get(scope = "crypto-db-scope", key = "eventhub-connstr"),
    eventhub_name="crypto201"
    )
    stock = [EventData(message)]
    with producer:
        producer.send_batch(stock)
    print(message)


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"BINANCE:ETHUSDT"}') # Bitcoin
    ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}') # Etherium


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://ws.finnhub.io?token={}".format(token),
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()


# COMMAND ----------

