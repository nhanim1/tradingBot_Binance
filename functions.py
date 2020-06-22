import time
import dateparser
import pytz
import json
#import matplotlib
#import matplotlib.pyplot as plt
#import matplotlib.ticker as mticker
#import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
from binance.client import Client

def handle_main(msg,symb,name,client):
    logfile = '%s.txt'%(name)
    rsifile = 'rsi%s.txt'%(name)
    simulation = False#True#
    if symb == 'ETHUSDT':
        price_delta = 10
        buy_factor = 1
    if symb == 'BTCUSDT':
        price_delta = 150
        buy_factor = 0.01
    param = '%s_param.txt'%(name)
    p1 = open(param,'r')
    param_ = p1.readlines()
    #t0 = float(param_[0])
    lastbuy = float(param_[1])
    bal_usdt = float(param_[2])
    asset = float(param_[3])
    #######################
    f = open(logfile,'a+')
    open_price = float(msg['o'])
    prcnt = float(msg['P'])
    close_price = float(msg['c'])
    high_price = float(msg['h'])
    low_price = float(msg['l'])
    price_diff = high_price - low_price
    if price_diff <= price_delta:
        target_profit = 1.12
        dynamic_range = 0.15
        rnge = dynamic_range*(high_price - low_price)
        low_limit = round((low_price + rnge),2)
        buy_target = low_limit
        rsi_lowlimit = 25
        rsi_highlimit = 70
    else:
        buy_target = low_price
        target_profit = 1.022
        dynamic_range = 0.25
        rsi_lowlimit = 20
        rsi_highlimit = 70
    #high_limit = round((low_price + (.85*price_diff)),2)
    if lastbuy != 0:
        profit = round((close_price / lastbuy),2)
        '''
        if profit >=1:
            print ("Profit :", profit)
        else:
            loss = round((1-profit),2)
            print ("Loss :-", loss,"/%")
        '''

    else:
        profit = 0
        #print ("no last buy")

    if close_price <= buy_target and bal_usdt >= 11:
        print ("close_price:", close_price," buy_target:", buy_target)
        f.write("close_price:%s , buy_target:%s\n" %(close_price,buy_target))
        #######check the rsi value saved in txt file
        latest_rsi = calc_rsi(symb,rsifile)
        #print (symb, '--> RSI:', latest_rsi )
        ######saved into txt file
        now = time.ctime(int(time.time()))
        t = "%s\n" %(now)
        print ('Close   Lowest    Highest    RSI')
        print (close_price,"--",low_price,"--",high_price,"--",latest_rsi)
        f.write("%s" %(t))
        f.write("Close   Highest    Lowest    RSI\n")
        f.write("%s , %s , %s , %s \n" %(close_price,high_price,low_price,latest_rsi))
        if latest_rsi <= rsi_lowlimit:
            print ('Buying...')
            print ('Client.....')
            buy(f,client,symb,simulation,close_price)
            ###update usdt file and asset file
            updateparams(symb,client,name)


    elif profit >= target_profit:
        #print ("close_price:", close_price,"high_limit:",high_limit)
        if asset != 0:
            print ("Profit :", profit)
            f.write("close_price:%s, profit:%s\n" %(close_price,profit))
            #print ('Client.....')
            sell(symb,client,f,close_price,target_profit,simulation)
            ###update usdt file and asset file
            updateparams(symb,client,name)

        else:
            print ('no asset to sell at the moment')
    else:
        #limit the loss
        if profit <=0.96:
            latest_rsi = calc_rsi(symb,rsifile)
            if latest_rsi >= rsi_highlimit:
                loss = round((1-profit),2)
                print ("Loss :-", loss,"%")
                #sell2(symb,client,f,close_price,target_profit,simulation)
                #updateparams(symb,client,name)

    f.close()
    p1.close()


def updateparams(symb,client,name):
    now = time.ctime(int(time.time()))
    print (now)
    lastbuy = buyorder(symb,client)
    bal_usdt = getusdt(client)
    asset = getasset(symb,client)
    param = '%s_param.txt'%(name)
    f = open(param,'w+')
    data = "%s\n%s\n%s\n%s\n" %(now,lastbuy,bal_usdt,asset)
    f.write(data)
    f.close()

def buyorder(symb,client):
    last_buy = '100000'
    data =[]
    filled_order = client.get_all_orders(symbol=symb, limit=5)
    filled_len = len(filled_order)
    #print (filled_order)
    #print 'Filled Orders:',filled_len
    if filled_len != 0:
        for x in range (filled_len-1,-1,-1):
            if filled_order[x]['status']== 'FILLED':
                record_list = [(str(filled_order[x]['side'])),(float(filled_order[x]['executedQty'])),(float(filled_order[x]['cummulativeQuoteQty']))]
                data.append(record_list)
                #print (data)
        if data[0][0] == 'BUY':
            last_buy = (data[0][2]/data[0][1])
            print ('Bought: $',last_buy)
        else:
            last_sold = (data[0][2]/data[0][1])
            print ('Sold: $',last_sold)
    return(last_buy)

def getusdt(client):
    balance = client.get_asset_balance(asset='USDT')
    bal_usdt = (float(balance['free']))
    bal_usdt = float(format((bal_usdt),'.2f'))
    print ('USDT Balance: $',bal_usdt)
    return(bal_usdt)

def getasset(symb,client):
    ##Check available asset:
    asset_name = str(symb[:3])
    bal_symbol = client.get_asset_balance(asset=asset_name)
    asset_str = str((bal_symbol['free']))
    freed_asset = float(asset_str)
    freed_asset = float(format((freed_asset),'.2f'))
    locked_asset = float(bal_symbol['locked'])
    total_asset = locked_asset + freed_asset
    print ('Freed Asset: ', freed_asset)
    return (freed_asset)

def calc_rsi(symb,filename):
    datep = []
    openp = []
    lowp = []
    highp = []
    closep = []
    volumep = []
    interval = Client.KLINE_INTERVAL_5MINUTE
    start = "1 hours ago UTC"
    end = "now UTC"
    klines = get_historical_klines(symb, interval, start, end)
    for kline in klines:
        time1 = int(kline[0])
        open1 = float(kline[1])
        Low = float(kline[2])
        High = float(kline[3])
        Close = float(kline[4])
        Volume = float(kline[5])
        datep.append(time1)
        openp.append(open1)
        lowp.append(Low)
        highp.append(High)
        closep.append(Close)
        volumep.append(Volume)
    ###Get RSI value
    rsi = rsiFunc(closep)
    len_rsi = len(rsi) - 1
    latest_rsi = rsi[len_rsi]
    latest_rsi = round(latest_rsi, 2)
    rsi_file = open(filename,'w+')
    data = "%s\n" %(latest_rsi)
    rsi_file.write(data)
    rsi_file.close()
    return (latest_rsi)

def sell(symb,client,f,close_price,target_profit,simulation):
    asset_name = str(symb[:3])
    bal_symbol = client.get_asset_balance(asset=asset_name)
    #asset_str = str((bal_symbol['free']))
    freed_asset = (float(bal_symbol['free']))#*0.99
    if freed_asset >= 0.1:

        #f.write("Close-->%s\n" %(close_price))
        #f.write("RSI: %s\n" %(round(latest_rsi, 2)))
        ##Check available asset:
        #asset_name = str(symb[:3])
        #bal_symbol = client.get_asset_balance(asset=asset_name)
        #asset_str = str((bal_symbol['free']))
        #freed_asset = (float(bal_symbol['free']))#*0.99
        locked_asset = float(bal_symbol['locked'])
        total_asset = locked_asset + freed_asset
        #print (asset_name,'Quantity:',total_asset)
        print ('Freed Asset: ', freed_asset)
        print (asset_name,'Price: $',close_price)
        f.write("%s Quantity: %s\n" %(asset_name, total_asset))
        f.write("Freed Asset:%s\n" %(freed_asset))
        f.write("%s Price: $ %s\n" %(asset_name,close_price))
        total_asset_val = close_price * total_asset
        total_freed_asset = close_price * freed_asset
        #if freed_asset >= 0.1:
        ##Current value price of available asset
        print ('Total Asset Value: $', total_asset_val)
        f.write("Total Asset Value: $%s\n" %(total_asset_val))

        ##[8] Get passed threading records
        fill_buy = []
        fill_sell = []
        data =[]
        filled_order = client.get_all_orders(symbol=symb, limit=3)
        filled_len = len(filled_order)
        #print 'Filled Orders:',filled_len
        if filled_len != 0:
            for x in range (filled_len-1,-1,-1):
                if filled_order[x]['status']== 'FILLED':
                    record_list = [(str(filled_order[x]['side'])),(float(filled_order[x]['executedQty'])),(float(filled_order[x]['cummulativeQuoteQty']))]
                    data.append(record_list)
            print (data)
            f.write(str(data))

            if data[0][0] == 'BUY':
                last_buy = (data[0][2]/data[0][1])
                profit = round((close_price / last_buy),2)
                if profit >= target_profit:
                    print ('profit =',profit)
                    f.write("\nprofit =%s\n" %(profit))
                    print ('execute sell now')
                    ticker_p = format(close_price, '.2f')
                    asset_name = str(symb[:3])
                    bal_symbol = client.get_asset_balance(asset=asset_name)
                    asset_str = str((bal_symbol['free']))
                    indx = (asset_str.index('.'))+3
                    ticker_q = float(asset_str[:indx])
                    #qtt_buy = float(format((capital/c_price), '.2f'))
                    if simulation != True:
                        order = client.order_limit_sell(
                            symbol=symb,
                            quantity=ticker_q,
                            price=ticker_p)
                else:
                    loss = total_asset_val - (data[0][2]*data[0][1])
                    loss = round(loss,2)
                    print ('loss =',loss)
                    f.write("loss =%s percent\n" %(loss))
                    print ('it is unprofitable to sell now..wait \n')
                    f.write("\nit is unprofitable to sell now..wait \n")

            else:
                print ('no history of buying any asset')
                f.write('no history of buying any asset\n')
    else:
        print ('no asset to sell at the moment')
        #f.write('no asset to sell at the moment\n')
            #os.system('say "no asset to sell at the moment"')
def sell2(symb,client,f,close_price,target_profit,simulation):
    asset_name = str(symb[:3])
    bal_symbol = client.get_asset_balance(asset=asset_name)
    #asset_str = str((bal_symbol['free']))
    freed_asset = (float(bal_symbol['free']))#*0.99
    if freed_asset >= 0.1:
        locked_asset = float(bal_symbol['locked'])
        total_asset = locked_asset + freed_asset
        #print (asset_name,'Quantity:',total_asset)
        print ('Freed Asset: ', freed_asset)
        print (asset_name,'Price: $',close_price)
        f.write("%s Quantity: %s\n" %(asset_name, total_asset))
        f.write("Freed Asset:%s\n" %(freed_asset))
        f.write("%s Price: $ %s\n" %(asset_name,close_price))
        total_asset_val = close_price * total_asset
        total_freed_asset = close_price * freed_asset
        #if freed_asset >= 0.1:
        ##Current value price of available asset
        print ('Total Asset Value: $', total_asset_val)
        f.write("Total Asset Value: $%s\n" %(total_asset_val))

        ##[8] Get passed threading records
        fill_buy = []
        fill_sell = []
        data =[]
        filled_order = client.get_all_orders(symbol=symb, limit=3)
        filled_len = len(filled_order)
        #print 'Filled Orders:',filled_len
        if filled_len != 0:
            for x in range (filled_len-1,-1,-1):
                if filled_order[x]['status']== 'FILLED':
                    record_list = [(str(filled_order[x]['side'])),(float(filled_order[x]['executedQty'])),(float(filled_order[x]['cummulativeQuoteQty']))]
                    data.append(record_list)
            print (data)
            f.write(str(data))

            if data[0][0] == 'BUY':
                last_buy = (data[0][2]/data[0][1])
                profit = round((close_price / last_buy),2)
                print ('profit =',profit)
                f.write("\nprofit =%s\n" %(profit))
                print ('execute sell now')
                ticker_p = format(close_price, '.2f')
                asset_name = str(symb[:3])
                bal_symbol = client.get_asset_balance(asset=asset_name)
                asset_str = str((bal_symbol['free']))
                indx = (asset_str.index('.'))+3
                ticker_q = float(asset_str[:indx])
                #qtt_buy = float(format((capital/c_price), '.2f'))
                if simulation != True:
                    order = client.order_limit_sell(
                        symbol=symb,
                        quantity=ticker_q,
                        price=ticker_p)


            else:
                print ('no history of buying any asset')
                f.write('no history of buying any asset\n')
    else:
        print ('no asset to sell at the moment')

def buy(f,client,symb,simulation,close_price):
    balance = client.get_asset_balance(asset='USDT')
    bal_usdt = (float(balance['free']))*0.999
    bal_usdt = float(format((bal_usdt),'.2f'))
    print ('USDT Balance: $',bal_usdt)
    #f.write("USDT Balance: $%s\n" %(bal_usdt))
    ##eth to buy:
    price_buy = float(format((close_price *.995),'.2f'))
    #.99 multiplication is to reduce buy price by 0.5% in search of lowest
    #not the best meth0d but we shall live with this for now
    #qtt_buy = buy_factor #*1.001#only buy 1 at a time, will increase in the future
    qtt_buy = bal_usdt/close_price#float(format((bal_usdt/close_price), '.2f'))
    qtt_buy = float(format((qtt_buy),'.2f'))
    buy_cost = price_buy * qtt_buy
    print ('Buy Cost: $',buy_cost)
    print (qtt_buy,price_buy)
    if bal_usdt >= buy_cost:
        if simulation != True:
            #os.system('say "buying execution now"')
            order = client.order_limit_buy(
                symbol=symb,
                quantity= qtt_buy,
                price= price_buy)
            print ('---------------------- ')
            print ('Bought',symb, 'at:', price_buy)
            print ('---------------------- ')
        f.write("\n----------------------\n")
        f.write("Bougtht %s at: %s\n" %(symb, price_buy))
        f.write("----------------------\n")
    else:
        print ('----->Insufficienct USDT<-----')
        f.write("----->Insufficienct USDT<-----\n")

def testing():
    print ('This is a test')
def interval_to_milliseconds(interval):
    ms = None
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60
    }
    unit = interval[-1]
    if unit in seconds_per_unit:
        try:
            ms = int(interval[:-1]) * seconds_per_unit[unit] * 1000
        except ValueError:
            pass
    return ms
def date_to_milliseconds(date_str):
    # get epoch value in UTC
    epoch = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
    # parse our date string
    d = dateparser.parse(date_str)
    # if the date is not timezone aware apply UTC timezone
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=pytz.utc)
    # return the difference in time
    return int((d - epoch).total_seconds() * 1000.0)

def get_historical_klines(symbol, interval, start_str, end_str=None):
    # create the Binance client, no need for api key
    client = Client("", "")
    # init our list
    output_data = []
    # setup the max limit
    limit = 500
    # convert interval to useful value in seconds
    timeframe = interval_to_milliseconds(interval)
    # convert our date strings to milliseconds
    start_ts = date_to_milliseconds(start_str)
    # if an end time was passed convert it
    end_ts = None
    if end_str:
        end_ts = date_to_milliseconds(end_str)
    idx = 0
    # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
    symbol_existed = False
    while True:
        # fetch the klines from start_ts up to max 500 entries or the end_ts if set
        temp_data = client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            startTime=start_ts,
            endTime=end_ts
        )
        # handle the case where our start date is before the symbol pair listed on Binance
        if not symbol_existed and len(temp_data):
            symbol_existed = True
        if symbol_existed:
            # append this loops data to our output data
            output_data += temp_data
            # update our start timestamp using the last value in the array and add the interval timeframe
            start_ts = temp_data[len(temp_data) - 1][0] + timeframe
        else:
            # it wasn't listed yet, increment our start date
            start_ts += timeframe
        idx += 1
        # check if we received less than the required limit and exit the loop
        if len(temp_data) < limit:
            # exit the while loop
            break
        # sleep after every 3rd call to be kind to the API
        if idx % 3 == 0:
            time.sleep(1)
    return output_data

def rsiFunc(prices, n=14):
    deltas = np.diff(prices)
    seed = deltas[:n+1]
    up = seed[seed>=0].sum()/n
    down = -seed[seed<0].sum()/n
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:n] = 100. - 100./(1.+rs)
    for i in range(n, len(prices)):
        delta = deltas[i-1] # cause the diff is 1 shorter
        if delta>0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        up = (up*(n-1) + upval)/n
        down = (down*(n-1) + downval)/n
        rs = up/down
        rsi[i] = 100. - 100./(1.+rs)
    return rsi
