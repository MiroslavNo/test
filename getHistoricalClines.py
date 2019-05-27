import traderFunctions
from binance.websockets import BinanceSocketManager
from binance.enums import *

import json


######################################################
#############		GET CLIENTS			##############
######################################################
clients = traderFunctions.addClients()
client=clients['tibRick']

#CONSTANTS:
#KLINE_INTERVAL_1MINUTE = '1m'
#KLINE_INTERVAL_3MINUTE = '3m'
#KLINE_INTERVAL_5MINUTE = '5m'
#KLINE_INTERVAL_15MINUTE = '15m'
#KLINE_INTERVAL_30MINUTE = '30m'
#KLINE_INTERVAL_1HOUR = '1h'
#KLINE_INTERVAL_2HOUR = '2h'
#KLINE_INTERVAL_4HOUR = '4h'
#KLINE_INTERVAL_6HOUR = '6h'
#KLINE_INTERVAL_8HOUR = '8h'
#KLINE_INTERVAL_12HOUR = '12h'
#KLINE_INTERVAL_1DAY = '1d'
#KLINE_INTERVAL_3DAY = '3d'
#KLINE_INTERVAL_1WEEK = '1w'
#KLINE_INTERVAL_1MONTH = '1M'

def getHistoricalKlines(client, tradedSymbol, interval):
	# 1546297200000 stands for 01.01.2019 ( x 1000 because of the milliseconds)
	start = 1546297200000
	klines = client.get_historical_klines(tradedSymbol, interval, start)
	
	startDateStamp = traderFunctions.convertEpochToTimestamp(start, epochInMiliseconds=True, format='%Y-%m-%d')
	
	with open(r'D:\crpt_historicalKlines\\' + tradedSymbol + '_' + interval + '_' + startDateStamp + '.json', mode='w') as sharedPrefFile:
		json.dump(klines, sharedPrefFile, indent=3, sort_keys=True)
		sharedPrefFile.close()

getHistoricalKlines(client, "BNBUSDT", client.KLINE_INTERVAL_1MINUTE)
