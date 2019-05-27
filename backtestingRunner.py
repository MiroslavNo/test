import traderFunctions
from binance.websockets import BinanceSocketManager
from binance.enums import *

import json

##############################################
#			ADJUSTING AREA
##############################################

from strat.devArea_notSeenByTradeRunner import pumpTheRightCoin_backtest
tradedSymbol = "BNBUSDT"
fileEnding = tradedSymbol + "_12h_2019-01-01.json"
inputFile = r"D:\crpt_historicalKlines\\" + fileEnding
##############################################
#			adjusting area END
##############################################

def backTest(strategy, inputFile, tradedSymbol):
	with open(inputFile, mode='r') as f:
		klines = json.load(f)
		for i in range (len(klines)):
			# time = float(klines[i][0])
			# avg price from candle = (float(klines[i][2]) + float(klines[i][3]))/2
			# CALLING strategy(time, price)
			strategy(int(klines[i][0]), (float(klines[i][2]) + float(klines[i][3]))/2)

backTest(pumpTheRightCoin_backtest.test, inputFile, tradedSymbol)


