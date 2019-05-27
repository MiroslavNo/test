import traderFunctions
from binance.websockets import BinanceSocketManager
from binance.enums import *

import json


######################################################
#############		GET CLIENTS			##############
######################################################
clients = traderFunctions.addClients()
client=clients['tibRick']

def getMinAndMaxPriceRatio(asset, hasUSDT):
	klines = client.get_historical_klines(asset + "BTC", interval, 1546297200000)

	min = 10000000.0
	max = 0.0

	l = len(klines) - 1

	for i in range (0, l):
		kline = klines[i]
		klinebtc = klinesbtc[i]

		kline2 = float(kline[2]) * float(klinebtc[2])
		kline3 = float(kline[3]) * float(klinebtc[3])
		
		if (kline2 > max):
			max = kline2
		if (kline2 < min):
			min = kline2
		if (kline3 > max):
			max = kline3
		if (kline3 < min):
			min = kline3

	print (asset + ";" + str(hasUSDT) + ";" + str(100*max/min))


getMinAndMaxPriceRatio("VET", True)
getMinAndMaxPriceRatio("WAVES", True)
getMinAndMaxPriceRatio("XLM", True)
getMinAndMaxPriceRatio("XMR", True)
getMinAndMaxPriceRatio("XRP", True)
getMinAndMaxPriceRatio("ZEC", True)
getMinAndMaxPriceRatio("ZIL", True)
getMinAndMaxPriceRatio("ZRX", True)
getMinAndMaxPriceRatio("BNB", True)
getMinAndMaxPriceRatio("ETH", True)

getMinAndMaxPriceRatio("AST", False)
getMinAndMaxPriceRatio("KNC", False)
getMinAndMaxPriceRatio("WTC", False)
getMinAndMaxPriceRatio("SNGLS", False)
getMinAndMaxPriceRatio("SNT", False)
getMinAndMaxPriceRatio("MCO", False)
getMinAndMaxPriceRatio("OAX", False)
getMinAndMaxPriceRatio("GAS", False)
getMinAndMaxPriceRatio("BQX", False)
getMinAndMaxPriceRatio("BNT", False)
getMinAndMaxPriceRatio("DNT", False)
getMinAndMaxPriceRatio("SNM", False)
getMinAndMaxPriceRatio("STRAT", False)
getMinAndMaxPriceRatio("FUN", False)
getMinAndMaxPriceRatio("XVG", False)
getMinAndMaxPriceRatio("ADX", False)
getMinAndMaxPriceRatio("AE", False)
getMinAndMaxPriceRatio("AGI", False)
getMinAndMaxPriceRatio("AION", False)
getMinAndMaxPriceRatio("AMB", False)
getMinAndMaxPriceRatio("APPC", False)
getMinAndMaxPriceRatio("ARDR", False)
getMinAndMaxPriceRatio("ARK", False)
getMinAndMaxPriceRatio("ARN", False)
getMinAndMaxPriceRatio("BCD", False)
getMinAndMaxPriceRatio("BCPT", False)
getMinAndMaxPriceRatio("BLZ", False)
getMinAndMaxPriceRatio("BRD", False)
getMinAndMaxPriceRatio("BTG", False)
getMinAndMaxPriceRatio("BTS", False)
getMinAndMaxPriceRatio("CDT", False)
getMinAndMaxPriceRatio("CMT", False)
getMinAndMaxPriceRatio("CND", False)
getMinAndMaxPriceRatio("CVC", False)
getMinAndMaxPriceRatio("DATA", False)
getMinAndMaxPriceRatio("DCR", False)
getMinAndMaxPriceRatio("DENT", False)
getMinAndMaxPriceRatio("DGD", False)
getMinAndMaxPriceRatio("DLT", False)
getMinAndMaxPriceRatio("DOCK", False)
getMinAndMaxPriceRatio("EDO", False)
getMinAndMaxPriceRatio("ELF", False)
getMinAndMaxPriceRatio("ENG", False)
getMinAndMaxPriceRatio("EVX", False)
getMinAndMaxPriceRatio("FUEL", False)
getMinAndMaxPriceRatio("GNT", False)
getMinAndMaxPriceRatio("GO", False)
getMinAndMaxPriceRatio("GRS", False)
getMinAndMaxPriceRatio("GTO", False)
getMinAndMaxPriceRatio("GVT", False)
getMinAndMaxPriceRatio("GXS", False)
getMinAndMaxPriceRatio("HC", False)
getMinAndMaxPriceRatio("INS", False)
getMinAndMaxPriceRatio("IOTX", False)
getMinAndMaxPriceRatio("KEY", False)
getMinAndMaxPriceRatio("KMD", False)
getMinAndMaxPriceRatio("LEND", False)
getMinAndMaxPriceRatio("LOOM", False)
getMinAndMaxPriceRatio("LRC", False)
getMinAndMaxPriceRatio("LSK", False)
getMinAndMaxPriceRatio("LUN", False)
getMinAndMaxPriceRatio("MANA", False)
getMinAndMaxPriceRatio("MDA", False)
getMinAndMaxPriceRatio("MFT", False)
getMinAndMaxPriceRatio("MTH", False)
getMinAndMaxPriceRatio("MTL", False)
getMinAndMaxPriceRatio("NAS", False)
getMinAndMaxPriceRatio("NAV", False)
getMinAndMaxPriceRatio("NCASH", False)
getMinAndMaxPriceRatio("NEBL", False)
getMinAndMaxPriceRatio("NPXS", False)
getMinAndMaxPriceRatio("NXS", False)
getMinAndMaxPriceRatio("OST", False)
getMinAndMaxPriceRatio("PHX", False)
getMinAndMaxPriceRatio("PIVX", False)
getMinAndMaxPriceRatio("POA", False)
getMinAndMaxPriceRatio("POE", False)
getMinAndMaxPriceRatio("POLY", False)
getMinAndMaxPriceRatio("POWR", False)
getMinAndMaxPriceRatio("PPT", False)
getMinAndMaxPriceRatio("QKC", False)
getMinAndMaxPriceRatio("QLC", False)
getMinAndMaxPriceRatio("QSP", False)
getMinAndMaxPriceRatio("RCN", False)
getMinAndMaxPriceRatio("RDN", False)
getMinAndMaxPriceRatio("REN", False)
getMinAndMaxPriceRatio("REP", False)
getMinAndMaxPriceRatio("REQ", False)
getMinAndMaxPriceRatio("RLC", False)
getMinAndMaxPriceRatio("RVN", False)
getMinAndMaxPriceRatio("SC", False)
getMinAndMaxPriceRatio("SKY", False)
getMinAndMaxPriceRatio("STEEM", False)
getMinAndMaxPriceRatio("STORJ", False)
getMinAndMaxPriceRatio("STORM", False)
getMinAndMaxPriceRatio("SYS", False)
getMinAndMaxPriceRatio("TNB", False)
getMinAndMaxPriceRatio("TNT", False)
getMinAndMaxPriceRatio("VIA", False)
getMinAndMaxPriceRatio("VIB", False)
getMinAndMaxPriceRatio("VIBE", False)
getMinAndMaxPriceRatio("WABI", False)
getMinAndMaxPriceRatio("WAN", False)
getMinAndMaxPriceRatio("WPR", False)
getMinAndMaxPriceRatio("XEM", False)
getMinAndMaxPriceRatio("XZC", False)
getMinAndMaxPriceRatio("YOYO", False)
getMinAndMaxPriceRatio("ZEN", False)