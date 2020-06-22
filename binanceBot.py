import functions as fc
import binance
import time
from datetime import datetime
from binance.client import Client
import numpy as np
import os
#import talib
from binance.websockets import BinanceSocketManager # Import the Binance Socket Manager
from twisted.internet import reactor
import time
import dateparser
import pytz
import json
import numpy as np
from datetime import datetime

name = 'bd'

#dagangan key
api_key='#####YOUR KEY####'
api_secret='#####YOUR KEY####'

# Instantiate a Client
client = Client(api_key=api_key, api_secret=api_secret)

## Define all params needed
symb = 'ETHUSDT'#'BTCUSDT'#'USDCUSDT'#

#filled_order = client.get_all_orders(symbol=symb, limit=3)
#print (filled_order)
print (name)
fc.updateparams(symb,client,name)
bm = BinanceSocketManager(client)

# This is our callback function. For now, it just prints messages as they come.
def handle_message(msg):
    symb = 'ETHUSDT'#'BTCUSDT'#'USDCUSDT'#
    name = 'bd'
    fc.handle_main(msg,symb,name,client)

# Start trade socket with 'ETHUSDT' and use handle_message to.. handle the message.
print ("Running", name,".....\n")
conn_key = bm.start_symbol_ticker_socket(symb,handle_message)
# then start the socket manager
bm.start()
# let some data flow..
time.sleep(15)
