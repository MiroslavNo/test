import traderFunctions
import json
import time
import datetime
from binance.enums import *

clients = traderFunctions.addClients()

def getSpecifiedAvgPrice():

	# POZOR tu je epochtime o 3 nuly dlhsi ako ten z tejto stranky:
	# https://www.epochconverter.com/
	# Monday, 18. March 2019 06:20:00
	epochStartAcumulation = 1552890000000


	tradesTibRick = clients['tibRick'].get_my_trades(symbol='BNBUSDT')
	sumQty = 0
	qtyTimesPrice = 0

	for dic in tradesTibRick:
		if (int(dic['time']) > epochStartAcumulation):
			sumQty += float(dic['qty'])
			qtyTimesPrice += (float(dic['qty']) * float(dic['price']))
		
	print ('Tibrick bought ' + str (sumQty) + ' coins for the avg price ' + str(qtyTimesPrice / sumQty))
	return sumQty, float(qtyTimesPrice / sumQty)


	#tradesmno= clients['mno'].get_my_trades(symbol='BNBUSDT')
	#sumQty = 0
	#qtyTimesPrice = 0
    #
	#for dic in tradesmno:
	#	if (int(dic['time']) > epochStartAcumulation):
	#		sumQty += float(dic['qty'])
	#		qtyTimesPrice += (float(dic['qty']) * float(dic['price']))
	#	
	#print ('MNO bought ' + str (sumQty) + ' coins for the avg price ' + str(qtyTimesPrice / sumQty))
