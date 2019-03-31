import time
import datetime
import logging
import json
import sys, os


######################################################
#############		LOGGING				##############
######################################################
infoLogger = logging.getLogger('infoLogger')
errorLogger = logging.getLogger('errorLogger')

sharedPrefFileLastEmail = 'emailNotification_lastWarningEmailTime'

def startLoggers():
	global infoLogger
	global errorLogger
	
	formatter = logging.Formatter('%(asctime)s - %(message)s')

	infohandler = logging.FileHandler( getScriptLocationPath(1) + r'\ReportsAndLogs\traderLog.log')
	infohandler.setFormatter(formatter)
	infoLogger.setLevel(logging.INFO)
	infoLogger.addHandler(infohandler)

	errorHandler = logging.FileHandler( getScriptLocationPath(1) + r'\ReportsAndLogs\traderLogErr.log')
	errorHandler.setFormatter(formatter)
	errorLogger.setLevel(logging.INFO)
	errorLogger.addHandler(errorHandler)


#################  print loggers ################
def ploggerInfo(msg,toprint=False):
	infoLogger.info(msg)
	if toprint:
		print(str(datetime.datetime.now().strftime("%d.%m %H:%M:%S")) + ' - Info - ' + msg)
def ploggerWarn(msg, sendEmail=True):
	print(str(datetime.datetime.now().strftime("%d.%m %H:%M:%S")) + ' - Warn - ' + msg)
	errorLogger.warn('Warn - ' + msg)
	infoLogger.info('Warn - ' + msg)
	if(sendEmail):
		if not ( checkIfLastTimeOfThisEvenWasLately(sharedPrefFileLastEmail, 3600) ):
			send_email('TRADER - Logger WARN', msg)
			writeEventTimeInSharedPrefs(sharedPrefFileLastEmail)

def ploggerErr(msg):
	print(str(datetime.datetime.now().strftime("%d.%m %H:%M:%S")) + ' - Err - ' + msg)
	errorLogger.error('Err - ' + msg)
	infoLogger.info('Err - ' + msg)
	if not ( checkIfLastTimeOfThisEvenWasLately(sharedPrefFileLastEmail, 3600) ):
		send_email('TRADER - Logger ERR', msg)
		writeEventTimeInSharedPrefs(sharedPrefFileLastEmail)
	# todo - dopln mozno nejaku zvukovu signalizaciu, video o pipa alebo take nieco

#################		GET CLIENTS		#################
# @Tested
def addClients():
	from sharedPrefs import binan_config
	from binance.client import Client
	clientDictToBeFilled = {}
	for account, cred in binan_config.CREDS.items():
		clientDictToBeFilled[account] = Client(cred['pub'], cred['priv'])
	return clientDictToBeFilled
	
#################  CHECK EXCHANGE STATUS ################
def checkExchangeStatus(client_curr):
	#check the exchange status (0=OK, 1=MAINTANENCE)
	status = client_curr.get_system_status()
	if status.get('status', 'Key Not Found')==1:
		ploggerWarn('BINANCE IS UNDER MAINTANENCE (SYSTEM_STATUS = 1) - will try in 30 minutes again')
		#wait 30 mins
		time.sleep(30 * 60)
		checkExchangeStatus(client_curr)
	
#################  CHECK TIME SYNC ERR ################
def checkTimeSyncErrAndLoop(client_curr, maxNrOfLoops, sleepInSec):
	try:
		tibRick_BTC = getAccoutBalances(client_curr, 'BTC', 0.002, False)
	except:
		if (maxNrOfLoops == 0):
			ploggerErr('The TimeSyncError is persistant and not going away - Exiting the script')
			sys.exit()
		else:
			ploggerWarn('TimeSyncError appeared, will check again in ' + str(sleepInSec) + ' sec [No Email]', False)
			time.sleep(sleepInSec)
			checkTimeSyncErrAndLoop(client_curr, maxNrOfLoops - 1, sleepInSec)

################# VARIABLES FROM JSON ################		
def checkIfInitVarHasValue(jsonName, dict, requiredInitialValuesDict):
	strategyName = dict['strategy']
	varsToCheck_names = requiredInitialValuesDict.get(strategyName, None)
	if ((varsToCheck_names == None) or (len(varsToCheck_names) == 0)):
		# iba printy - kedze sa jedna o inizializaciu runnera nepotrebujem log, ale hned uvidim print
		print('ERR - For the stragy with name ' + strategyName + ' there can not be found any vars in mandatoryInitVars dic - (or MORE PROBABLY the strategy does not exist)')
		print('ERR - The json trigger file with the name ' + jsonName + ' will be skipped')
		return False
	for k_varToCheck_name, v_varToCheck_descr in varsToCheck_names.items():
		if k_varToCheck_name.startswith('a_'):
			varToCheck_valueInJson = dict.get(k_varToCheck_name, None) 
			if (varToCheck_valueInJson == None):
				print('ERR - Trader(runner) - In the init file with name "' + jsonName + '" the var "'  + k_varToCheck_name + '" has None value')
				print('ERR - Trader(runner) - The json file ' + jsonName + ' will NOT run')
				return False
	return True

def getClientAndStrategyFromFileName(fileName):
	r = {}
	fileNameList = fileName.split("_")
	r['strategy'] = fileNameList[0]
	client = fileNameList[1]
	# in case the name of the json is only 'strategyName_client.json'
	if client.endswith('.json'):
		client = client[:-5]
	r['client'] = client
	return r

def loadAllInitJsons(requiredInitialValuesDict):
	sharedPrefRootFolder = getScriptLocationPath(0) + r"\jsonTriggerFiles"
	allJsonsDict = {}
	for file in os.listdir(sharedPrefRootFolder):
		if file.endswith('.json'):
			if ((not file.endswith('_template.json')) and (not file.endswith('_prefilled.json'))):
				with open(sharedPrefRootFolder + "\\" + file, mode='r') as sharedPrefFile:
					sharedPrefData = json.load(sharedPrefFile)
					clientAndStrategyNames = getClientAndStrategyFromFileName(file)
					sharedPrefData.update(clientAndStrategyNames)
					if ( checkIfInitVarHasValue( file, sharedPrefData, requiredInitialValuesDict ) ):
						allJsonsDict[file[:-5]] = sharedPrefData
					sharedPrefFile.close()
	return allJsonsDict
	
def dumpGlobalVariablesToJson(fileName, globalVariables, scriptLocationPath):
	# scriptLocationPath je tu ako param a nie ako getScriptLocationPath(), lebo sa tato metoda sa moze casto pouzivat
	sharedPrefRootFolder = scriptLocationPath + r"\jsonTriggerFiles"
	#ak ten file neexistuje, vytvori novy
	with open(sharedPrefRootFolder + "\\" + fileName + ".json", mode='w') as sharedPrefFile:
		json.dump(globalVariables, sharedPrefFile, indent=3, sort_keys=True)
		sharedPrefFile.close()

# @Tested
def moveJsonIntoInactiveOnes(fileName):
	from pathlib import Path
	sharedPrefRootFolder = getScriptLocationPath(0) + r"\jsonTriggerFiles\\"
	fullFilePath = sharedPrefRootFolder + fileName + ".json"
	if Path(fullFilePath).is_file():
		os.rename(fullFilePath, sharedPrefRootFolder + "inactive\\" + fileName + ".json")
	else:
		ploggerErr('Tried to move the json trigger file with name ' + fileName + '.json into the inactive folder, but it appears, that the file do no exist. Path of the file: ' + fullFilePath)

##########	Get script location path	#############
def getScriptLocationPath(numberOfFoldersToMoveUp=0):
	pathname = os.path.dirname(sys.argv[0])        
	fullPath = os.path.abspath(pathname)
	
	if numberOfFoldersToMoveUp==0:
		return fullPath
	else:
		pathList = fullPath.split("\\")
		pathListSize = len(pathList)

		if pathListSize > numberOfFoldersToMoveUp:
			lengthToTrim = 0
			for i in range (0, numberOfFoldersToMoveUp):
				lengthToTrim += (len(pathList[pathListSize - (i + 1)]) + 1)
			
			path = fullPath[ : -(lengthToTrim) ]
			return path
		else:
			return fullPath

#################  CONVERT BINANCE TIMESTAMPT TO READABLE DATE ################
def convertEpochToTimestamp(ts_epoch, epochInMiliseconds=True, format='%Y-%m-%d %H:%M:%S'):
	if (epochInMiliseconds):
		timeInt = int(ts_epoch) / 1000
	else:
		timeInt = int(ts_epoch)
	ts = datetime.datetime.fromtimestamp(timeInt).strftime(format)
	return ts

#################  PART OF THE GUARDIAN FUNCTIONALITY ################
def setclbkCounterForGuardian(loopingTimeInMin):
	# 1,05 je bezpecnostny koef
	writingTimeInSec = int(round(loopingTimeInMin * 60 / 1.05))
	return writingTimeInSec
	
#################  SYTEM TIME ################
#prints the server time difference
def getBinanceTimeDifference(client, iLoops, boolPrint):
	diffTotal = 0
	for i in range(0, iLoops):
		local_time1 = int(time.time() * 1000)
		server_time = client.get_server_time()
		diff = server_time['serverTime'] - local_time1
		diffTotal = diffTotal + diff
		if boolPrint:
			print("local:%s server:%s diff:%s" % (local_time1, server_time['serverTime'], diff))
		time.sleep(1)
	diffAvg = diffTotal/iLoops
	if boolPrint:
		print ("diffAvg: %s" % (diffAvg))
	return int(diffAvg)
	
def syncSystemTime(client, maxDev_milisec=3000, minDev_milisec=500):
	import win32api
	devInMilisec = getBinanceTimeDifference(client, 2, False)
	dt = datetime.datetime.utcnow()
	dt = dt + datetime.timedelta(milliseconds=devInMilisec)
	dayOfWeek = int(datetime.datetime.utcnow().isocalendar()[2])
	print('the calculated time deviance was: ' + str(devInMilisec))
	#win32api.SetSystemTime(year, month, dayOfWeek, day, hour, minute, second, millisecond)
	if ((devInMilisec < maxDev_milisec) and (abs(devInMilisec) > minDev_milisec)):
		print('changing system time')
		#win32api.SetSystemTime (int(dt.year), int(dt.month), dayOfWeek, int(dt.day), int(dt.hour), int(dt.minute), int(dt.second), int(dt.microsecond/1000))
	#else throw exception

	
#################  EXTRACT PRICES FROM CALLBACK MSG ################
def getPricesFromClbkMsg(tickerDict):
	# OBJECTS IN A 24hrTicker - important ones: c, b, a, q
	# If there was NO movement, the SYMBOL will be NOT in the ticker
	#"e": "24hrTicker",  // Event type
	#"E": 123456789,     // Event time - epoch time
	#"s": "BNBBTC",      // Symbol
	#"p": "0.0015",      // Price change - absolutna zmena 24h
	#"P": "250.00",      // Price change percent - zmena ktoru ukazuje v tickery 24h
	#"w": "0.0018",      // Weighted average price - vazeny priemer trade-ov za posl 24h
	#"x": "0.0009",      // First trade(F)-1 price (first trade before the 24hr rolling window)
	#"c": "0.0025",      // Last price - posledny trade
	#"Q": "10",          // Last quantity - Qty posledneho trade-u
	#"b": "0.0024",      // Best bid price - prvy bid v orderbooku
	#"B": "10",          // Best bid quantity - Qty pre prvy bid v orderbooku
	#"a": "0.0026",      // Best ask price - prvy ask v orderbooku
	#"A": "100",         // Best ask quantity - Qty pre prvy ask v orderbooku
	#"o": "0.0010",      // Open price - na 24h candle ALE candle ktory je 24h spat od TERAZ - tj. nie to co ukazuje graf
	#"h": "0.0025",      // High price - analogia k "o" (Open price)
	#"l": "0.0010",      // Low price - analogia k "o" (Open price)
	#"v": "10000",       // Total traded base asset volume - volume ktory ti ukazuje v tickery (24h) v hodnote base asset,napr pre BTCUSDT by to bolo BTC
	#"q": "18",          // Total traded quote asset volume - volume ktory ti ukazuje v tickery (24h) v hodnote quote asset,napr pre BTCUSDT by to bolo USDT
	#"O": 0,             // Statistics open time - open cas v epoch pre 24h candle z predch metrik 
	#"C": 86400000,      // Statistics close time - close cas v epoch pre 24h candle z predch metrik
	#"F": 0,             // First trade ID
	#"L": 18150,         // Last trade Id
	#"n": 18151          // Total number of trades
	
	result = {}
	clbkType = tickerDict[0].get('e')
	
	if (clbkType == '24hrTicker'):
		#iterate through LIST
		for dict in tickerDict:
			symbol = dict.get('s', 'key not found')
			if ( (symbol.upper().endswith('BTC')) or (symbol.upper().endswith('USDT')) ):
				result[symbol] = {'c': float(dict.get('c', 0)), 'b': float(dict.get('b', 0)), 'a': float(dict.get('a', 0)), 'q': float(dict.get('q', 0))}
		return result
	else:
		traderFunctions.ploggerErr ('Unknown callback message type')

#################  GET BALANCES ################
def getAccoutBalances(client, defCoin, minAmountReq, bPrint):
	account_info = client.get_account()
	balances=account_info.get('balances', 'Key Not Found')
	balances_inDefCoin = {}
	sumInDefCoin = 0.0
	for balance in balances:
		amount = float(balance.get('free')) + float(balance.get('locked'))
		if(amount > 0):
			assetName = balance.get('asset')
			if(assetName != defCoin):
				#exception for PAX, because there is also an old pair PAXBTC still listening
				if(assetName == "PAX"):
					lastPrice = 1/getLastPrice(client, defCoin, str(assetName))
				else:
					lastPrice = getLastPrice(client, str(assetName), defCoin)
			else:
				lastPrice = 1
			valInDefCoin = lastPrice * amount
			#if defcoin val is GRT than minAmountReq
			if(valInDefCoin > minAmountReq):
				sumInDefCoin = sumInDefCoin + valInDefCoin
				balances_inDefCoin[assetName] = valInDefCoin
									   
				if(bPrint):
					print ('_________________')
					print (assetName)
					print (amount)
					print (valInDefCoin)
	
	balances_inDefCoin['total'] = sumInDefCoin
	if(bPrint):			
		print ('_________________')
		print (sumInDefCoin)
	return balances_inDefCoin
	
#################  GET AVAILABLE AMOUNT ################
def	getAvailableAmount(client, coin, roundDigits=2):
	coinAmount = float(client.get_asset_balance(asset=coin).get('free'))
	coinAmonutRounded = round(coinAmount, roundDigits)
	return coinAmonutRounded
	
	
################  GET LAST PRICE ################
def getLastPrice(client, pair_coin1, pair_coin2):
	try:
		trades = client.get_recent_trades(symbol=(pair_coin1 + pair_coin2), limit=5)
		lastTrade = trades[4]
		lastTradePrice = float(lastTrade['price'])
		return lastTradePrice
	except:
		#try if reverse parameter, i.e. if defCoin
		try:
			trades = client.get_recent_trades(symbol=(pair_coin2 + pair_coin1), limit=5)
			lastTrade = trades[4]
			lastTradePrice = 1/float(lastTrade['price'])
			return lastTradePrice
		except:
			return 0
	
################  GET FIRST ENTRY IN ORDERBOOK ################
def getFirstEntryInOrderBook(client, sellOrBuy, pair):
	# lowest possible number of trades to get is 5
	depth = client.get_order_book(symbol=pair, limit=5)
	if(sellOrBuy.lower()=='sell'):
		return float(depth['asks'][0][0])
	elif(sellOrBuy.lower()=='buy'):
		return float(depth['bids'][0][0])

################  SEND EMAIL ################
def send_email(subject, msg):
	ploggerInfo('Will send an email with the subject: ' +  subject)
	try:
		import smtplib
		# creates SMTP session 
		# mozne servre pre tuto schranku najdes na:
		# https://admin.websupport.sk/sk/email/mailbox/loginInformation/874582?domainId=174657&mailboxId=394385&domain=volebnyprieskum.sk
		s = smtplib.SMTP('smtp.websupport.sk', 25)
		# start TLS for security 
		s.starttls()
		s.login("notifications@volebnyprieskum.sk", "Bue5BoL9beF3")
		#all email attributes such as subject etc is just text
		message =  "From: notifications@volebnyprieskum.sk\nSubject: " + subject + "\n" + msg
		s.sendmail("notifications@volebnyprieskum.sk", "novosad.miroslav@gmail.com", message) 
		s.quit()
	except:
		#here goes a warning without email, so we wont cause an infinite loop
		ploggerWarn('Could not send the email out', False)

################  Check Last Occurence ################
def checkIfLastTimeOfThisEvenWasLately(sharedPrefFileName, timeLimitInSec):
	sharedPrefFileLocation = r"sharedPrefs\\" + sharedPrefFileName + '.json'
	ploggerInfo('Testing if event in the file ' + sharedPrefFileName + ' was less than ' + str(timeLimitInSec) + ' seconds ago' )
	with open(getScriptLocationPath(0) + "\\" + sharedPrefFileLocation, mode='r') as sharedPrefFile:
		sharedPrefData = json.load(sharedPrefFile)
		sharedPrefFile.close()
	lastTime = sharedPrefData.get(sharedPrefFileName)
	# if fulfilled the even happend lately (in the given timeLimitInSec)
	if ( ( int(time.time()) - lastTime ) < timeLimitInSec ):
		ploggerInfo('The event in the file ' + sharedPrefFileName + ' was less than ' + str(timeLimitInSec) + ' seconds ago' )
		return True
	else:
		ploggerInfo('The event in the file ' + sharedPrefFileName + ' was NOT less than ' + str(timeLimitInSec) + ' seconds ago' )
		return False

def writeEventTimeInSharedPrefs(sharedPrefFileName):
	sharedPrefFileLocation = r"sharedPrefs\\" + sharedPrefFileName + '.json'
	with open(getScriptLocationPath(0) + "\\" + sharedPrefFileLocation, mode='w') as sharedPrefFileW:
		json.dump({sharedPrefFileName: int(time.time()), sharedPrefFileName + '_humanTime': convertEpochToTimestamp(time.time(), False)}, sharedPrefFileW)
		sharedPrefFileW.close()

		
################  CALCULATES THE StDEV OF A PAIR FOR A GIVEN TIMEFRAME ################
#REMMIROdef getAverageDeviationOfLastPriceMovements(pair, client_curr, period, interval):
#REMMIRO	import statistics
#REMMIRO	priceRanges = []
#REMMIRO	#checkni ci ten Cliet by nemal byt tvoj specificky client - funguje to ale vo file trader.py
#REMMIRO	klines = client_curr.get_historical_klines(pair, interval, period)
#REMMIRO	#get priceRanges from klines
#REMMIRO	for j in range (len(klines)):
#REMMIRO		kline = klines[j]
#REMMIRO		priceRange = float(kline[2]) - float(kline[3])
#REMMIRO		priceRanges.append(priceRange)
#REMMIRO	
#REMMIRO	return float(statistics.stdev(priceRanges))
#REMMIRO	

# OBSOLETE FCION AS THE 24hrTicker already contains the information of the trading volume from last 24h
#def hasMinTradingVolume(pair, client_curr, minTradingVolPerDay_BTC=0, minTradingVolPerDay_ETH=0, minTradingVolPerDay_BNB=0, minTradingVolPerDay_USDT=0):
#	#get trading volume for last day
#	#if BTC traiding pair
#	if pair[-3:]=="BTC":
#		if trVol > minTradingVolPerDay_BTC:
#			return True
#	elif pair[-3:]=="ETH":
#		if trVol > minTradingVolPerDay_ETH:
#			return True
#	elif pair[-3:]=="BNB":
#		if trVol > minTradingVolPerDay_BNB:
#			return True
#	elif pair[-4:]=="USDT":
#		if trVol > minTradingVolPerDay_USDT:
#			return True
#	
#	return False


#REMMIROdef findBestAverageDeviation(minTradeVol_BTC, client_curr, printBest_No=0, period="2 day ago UTC", interval=Client.KLINE_INTERVAL_30MINUTE):
#REMMIRO	allTickers = client_curr.get_all_tickers()
#REMMIRO	
#REMMIRO	minTradeVol_ETH = minTradeVol_BTC / getLastPrice("ETH", "BTC", client_curr)
#REMMIRO	minTradeVol_BNB = minTradeVol_BTC / getLastPrice("BNB", "BTC", client_curr)
#REMMIRO	minTradeVol_USDT = minTradeVol_BTC * getLastPrice("ETH", "BTC", client_curr)
#REMMIRO	
#REMMIRO	for ticker in tickers:
#REMMIRO		if hasMinTradingVolume(pair, minTradeVol_BTC, minTradeVol_ETH, minTradeVol_BNB, minTradeVol_USDT, client_curr):
#REMMIRO			avgdevs_list = getAverageDeviationOfLastPriceMovements(pair, client_curr, period, interval)
#REMMIRO		
#REMMIRO		if printBest_No > 0:
#REMMIRO			#sort list entries
#REMMIRO			#print printBest_No
#REMMIRO	
#REMMIRO	#return the best
#REMMIRO
#REMMIROdef findBestGainers(minTradingVolumeInBTC, client_curr, printBest_No=5, period="90 day ago UTC"):
#REMMIRO	#loop all assets
#REMMIRO		if hasMinTradingVolume(pair, minTradingVolumeInBTC, client_curr):
#REMMIRO			#get daily candle chart
#REMMIRO				#loop through
#REMMIRO					#note the minimum an maximum
#REMMIRO			#note percentege diff
#REMMIRO	
#REMMIRO	#print best gainers
#REMMIRO	#return something


#REM def sellForTheCurrentPrice(client, pair, amount):
	#check aka bola rychlost za posledne nejake kratke obdobie, ak rychla predavaj rychlo, ak pomala, predavaj pomaly
	
#REM def protectInvestmentAndTakeProfit(params):
#REM 	clientParam = params.get('client', 'not found')
#REM 	pair_coin1_param = params.get('', 'not found')
#REM 	pair_coin2_param = params.get('', 'not found')
#REM 	buyPrice_param = float(params.get('', 'not found'))
#REM 	NEJAKYTRESHOLD = float(params.get('', 'not found'))
#REM 	NEJAKYMAXIMALNYPREPAD  = float(params.get('', 'not found'))
#REM 	NEJAKYMAXPULLBACK  = float(params.get('', 'not found'))
#REM 	maxPrice_sysParam = float(params.get('', 'not found'))
#REM 	lastPrice=getLastPrice()
#REM 	
#REM 	targetPriceProximity = 1,0021
#REM 	
#REM 	if ((maxPrice_sysParam/buyPrice_param) > (1+NEJAKYTRESHOLD)):
#REM 		#toto je mode pre take profit, lebo z dosiahol minimalnu sadzbu
#REM 		if ((lastPrice/maxPrice_sysParam) < ((1-NEJAKYMAXPULLBACK)* targetPriceProximity):
#REM 	else:
#REM 		#toto je mode protect money, lebo este nedosiahol minimalny zisk, cize chranis pred nahlim prepadom
#REM 		if (lastPrice/buyPrice_param) < ((1-NEJAKYMAXIMALNYPREPAD)* targetPriceProximity):
#REM 			#musis predavat
#REM 		#else:
#REM 			#cakas