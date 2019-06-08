import time
import datetime
import logging
import json
import sys, os
from decimal import Decimal

######################################################
#############		LOGGING				##############
######################################################
infoLogger = logging.getLogger('infoLogger')
errorLogger = logging.getLogger('errorLogger')
tradesLogger = logging.getLogger('tradesLogger')

sharedPrefFileLastEmail = 'emailNotification_lastWarningEmailTime'

SEP = ';'
DOT = '.'
COMMA = ','
INFO = ' - INFO - '
WARN = ' - WARN - '
ERR = ' - ERR - '
TIMESTAMP_FORMAT = '%d.%m %H:%M:%S'
TRADE_CAT = ' - TRADE - '


def startLoggers():
	from pathlib import Path
	global infoLogger
	global errorLogger
	global tradesLogger
	
	# rolling infoLogger sa vyriesil tak, ze pri kazdom starte sa stary subor premenuje s time stamp-om ak vacsi nez 7,5 Mb
	pathInfoLogger = Path(getScriptLocationPath(1) + r'\ReportsAndLogs\traderLog.log')
	if pathInfoLogger.is_file():
		if(os.path.getsize(pathInfoLogger) > 7500000):
			pathInfoLogger.rename(Path(getScriptLocationPath(1) + r'\ReportsAndLogs\traderLog_' + str(datetime.datetime.now().strftime("%Y%d%m_%H%M")) + '.log'))
	
	formatter = logging.Formatter('%(asctime)s - %(message)s')

	infohandler = logging.FileHandler( pathInfoLogger )
	infohandler.setFormatter(formatter)
	infoLogger.setLevel(logging.INFO)
	infoLogger.addHandler(infohandler)

	# errorLogger sa nerolluje, ale vymazava manualne, aby som vzdy videl ake errory su tam, okrem toho vsetky tieto udaje su aj v infologgerovi
	errorHandler = logging.FileHandler( getScriptLocationPath(1) + r'\ReportsAndLogs\traderLogErr.log')
	errorHandler.setFormatter(formatter)
	errorLogger.setLevel(logging.INFO)
	errorLogger.addHandler(errorHandler)
	
	# TODO_future toto by muselo byt rozdielne pre rozne ucty
	tradesHandler = logging.FileHandler( getScriptLocationPath(1) + r'\ReportsAndLogs\trades.csv')
	tradesHandler.setFormatter(formatter)
	tradesLogger.setLevel(logging.INFO)
	tradesLogger.addHandler(tradesHandler)


#################  print loggers ################
# TODO infor, warn a err stringy daj ako konstanty, tiez format casu
def ploggerInfo(msg,toprint=False):
	infoLogger.info(msg)
	if toprint:
		print(str(datetime.datetime.now().strftime(TIMESTAMP_FORMAT)) + INFO + msg)
def ploggerWarn(msg, sendEmail=True):
	print(str(datetime.datetime.now().strftime(TIMESTAMP_FORMAT)) + WARN + msg)
	errorLogger.warn(WARN[3:] + msg)
	infoLogger.info(WARN[3:] + msg)
	if(sendEmail):
		if not ( checkIfLastTimeOfThisEventWasLately(sharedPrefFileLastEmail, 3600) ):
			send_email('TRADER - Logger WARN', msg)
			writeEventTimeInSharedPrefs(sharedPrefFileLastEmail)

def ploggerErr(msg):
	# the msg should be printed automatically but it does not happen always
	print(str(datetime.datetime.now().strftime(TIMESTAMP_FORMAT)) + ERR + msg)
	errorLogger.error(ERR[3:] + msg)
	infoLogger.info(ERR[3:] + msg)
	if not ( checkIfLastTimeOfThisEventWasLately(sharedPrefFileLastEmail, 3600) ):
		send_email('TRADER - Logger ERR', msg)
		writeEventTimeInSharedPrefs(sharedPrefFileLastEmail)

def ploggerTrades(symbol, stepNr, entryType, price, diffTriggPriceVsExecPrice, gain, amount):
	"""
	 # entryType can be also START and EXIT ( if step was created / removed )
	 # diffTriggPriceVsExecPrice is difference in percentage of the planned price and the price which was reached in the market oreder: a negative value means that the difference is against me, a positive value would mean that I got lucky and even got a better price than planned
	 # gain is a percentage which describes how much I could earn in relation to the last trade: a negative value means that the trade made a loss - here the weight of the entry is not condidered
	"""
	msg = SEP + symbol + SEP + str(stepNr).replace(DOT, COMMA) + SEP + entryType + SEP + str(price).replace(DOT, COMMA) + SEP + str(diffTriggPriceVsExecPrice).replace(DOT, COMMA) + SEP + str(gain).replace(DOT, COMMA) + SEP + str(amount).replace(DOT, COMMA)
	tradesLogger.info(msg)
	print(str(datetime.datetime.now().strftime(TIMESTAMP_FORMAT)) + TRADE_CAT + msg)

def formatDictForPrint(d):
	return json.dumps(d, indent=2)

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
	sleepInMin=15
	#check the exchange status (0=OK, 1=MAINTANENCE)
	status = client_curr.get_system_status()
	while(status.get('status', 'Key Not Found')==1):
		#if status.get('status', 'Key Not Found')==1:
		ploggerWarn('BINANCE IS UNDER MAINTANENCE (SYSTEM_STATUS = 1) - will try in {} minutes again'.format(str(sleepInMin)))
		#wait
		time.sleep(sleepInMin * 60)
		status = client_curr.get_system_status()
	
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
		if (k_varToCheck_name.startswith('a_') or k_varToCheck_name.startswith('u_')):
			varToCheck_valueInJson = dict.get(k_varToCheck_name, None) 
			if (varToCheck_valueInJson == None):
				print('ERR - Trader(runner) - In the init file with name "' + jsonName + '" the var "'  + k_varToCheck_name + '" has None value')
				print('ERR - Trader(runner) - The json file ' + jsonName + ' will NOT run')
				return False
	return True

def getClientAndStrategyFromFileName(fileName):
	"""
		it is required, that the strategy is the first on the filename and the client the last, otherwise wont work
	"""
	r = {}
	fileNameList = fileName.split("_")
	r['strategy'] = fileNameList[0]
	client = fileNameList[len(fileNameList)-1]
	# in case the name of the json is only 'strategyName_client.json'
	if client.endswith('.json'):
		client = client[:-5]
	r['client'] = client
	return r

def isInitJsonNotTeplate(name):
	return ( name.endswith('.json') and (not name.endswith('_template.json')) and (not name.endswith('_prefilled.json')) )	

def loadAllInitJsons(requiredInitialValuesDict):
	sharedPrefRootFolder = getScriptLocationPath(0) + r"\jsonTriggerFiles"
	allJsonsDict = {}
	for file in os.listdir(sharedPrefRootFolder):
		if (isInitJsonNotTeplate(file)):
			with open(sharedPrefRootFolder + "\\" + file, mode='r') as sharedPrefFile:
				sharedPrefData = json.load(sharedPrefFile)
				clientAndStrategyNames = getClientAndStrategyFromFileName(file)
				sharedPrefData.update(clientAndStrategyNames)
				if ( (requiredInitialValuesDict is None) or (checkIfInitVarHasValue( file, sharedPrefData, requiredInitialValuesDict )) ):
					allJsonsDict[file[:-5]] = sharedPrefData
				sharedPrefFile.close()
	return allJsonsDict
	
def dumpGlobalVariablesToJson(fileName, globalVariables, scriptLocationPath):
	# scriptLocationPath je tu ako param a nie ako getScriptLocationPath(), aby sa tato metoda nepouzivala casto
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

def convertTimestampToEpoch(timestamp_str, epochInMiliseconds=True, timeStampFormat='%Y%m%d%H%M'):
	# for the timeStampFormat="%Y%m%d%H%M" a call would look like: convertTimestampToEpoch('201906071000', False)
	utc_time = datetime.datetime.strptime(timestamp_str, timeStampFormat)
	epoch_time = (utc_time - datetime.datetime(1970, 1, 1)).total_seconds()
	if (epochInMiliseconds):
		epoch_time = epoch_time * 1000

	return epoch_time


#################  PART OF THE GUARDIAN FUNCTIONALITY ################
def setclbkCounterForGuardian(loopingTimeInMin):
	# 1,25 je bezpecnostny koef
	writingTimeInSec = int(round(loopingTimeInMin * 60 / 1.25))
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
			# if ( (symbol.upper().endswith('BTC')) or (symbol.upper().endswith('USDT')) ):
			if (symbol.upper().endswith('USDT')):
				# TODO_future these other data might be usefull in the future but not now, so taking only the 'c' 
				# result[symbol] = {'c': float(dict.get('c', 0)), 'b': float(dict.get('b', 0)), 'a': float(dict.get('a', 0)), 'q': float(dict.get('q', 0))}
				result[symbol] = float(dict.get('c', 0))
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

def getCoinStocs(client, defCoin='USDT', includeZeroValues=False):
	r={}
	account_info = client.get_account()
	balances=account_info.get('balances', 'Key Not Found')
	for balance in balances:
		amount = float(balance.get('free')) + float(balance.get('locked'))
		if (includeZeroValues or (amount > 0)):
			assetName = balance.get('asset')
			if(assetName != defCoin):
				r[assetName] = amount
	return r
		
#################  GET AVAILABLE AMOUNT ################
def	getAvailableAmount(client, coin, roundDigits=2):
	coinAmount = float(client.get_asset_balance(asset=coin).get('free'))
	coinAmonutRounded = round(coinAmount, roundDigits)
	return coinAmonutRounded

def hasAvailableAmount(client, coin, reqAmount):
	coinAmount = float(client.get_asset_balance(asset=coin).get('free'))
	return ( reqAmount <= coinAmount)
	
################  GET LAST PRICE ################
def getLastPrice(client, pair_coin1, pair_coin2=None):
	"""
		compatible for coins as well as markets as argument
	"""
	if(pair_coin2 is None):
		try:
			trades = client.get_recent_trades(symbol=(pair_coin1), limit=5)
			lastTrade = trades[4]
			lastTradePrice = float(lastTrade['price'])
			return lastTradePrice
		except:
			return 0
		
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
	from sharedPrefs import email_config
	emailDic=email_config.EMAILS['notif']
	subject = subject + '_{}'.format(str(datetime.datetime.now().strftime("%H:%M")))
	
	ploggerInfo('Will send an email with the subject: ' +  subject)
	try:
		import smtplib
		# creates SMTP session 
		# mozne servre pre tuto schranku najdes na:
		# https://admin.websupport.sk/sk/email/mailbox/loginInformation/874582?domainId=174657&mailboxId=394385&domain=volebnyprieskum.sk
		# TODO_future prerob na sifrovane spojenie
		s = smtplib.SMTP('smtp.websupport.sk', 25)
		# start TLS for security 
		s.starttls()
		s.login(emailDic['address'], emailDic['pw'])
		#all email attributes such as subject etc is just text
		message =  "From: " + emailDic['address'] + "\nSubject: " + subject + "\n" + msg
		s.sendmail(emailDic['address'], "novosad.miroslav@gmail.com", message) 
		s.quit()
	except:
		#here goes a warning without email, so we wont cause an infinite loop
		ploggerWarn('Could not send the email out', False)

################  Check Last Occurence ################
def checkIfLastTimeOfThisEventWasLately(sharedPrefFileName, timeLimitInSec):
	sharedPrefFileLocation = r"sharedPrefs\\" + sharedPrefFileName + '.json'
	# DEBUG
	# ploggerInfo('Testing if event in the file ' + sharedPrefFileName + ' was less than ' + str(timeLimitInSec) + ' seconds ago' )
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


def getPriceAndQtyReqs(tradedSymbol, client):
	infos = client.get_symbol_info(tradedSymbol)
	filters = infos.get("filters", None)
	r = {}
	
	if (filters is not None):
		for filter in filters:
			if(filter.get("filterType", None) == "PRICE_FILTER"):
				tickSize = str(filter.get("tickSize", 0.0))
				minPrice = str(filter.get("minPrice", 0.0))
				r["tickSize"] = tickSize
				r["minPrice"] = minPrice
			if(filter.get("filterType", None) == "LOT_SIZE"):
				minQty = str(filter.get("minQty", 0.0))
				stepSize = str(filter.get("stepSize", 0.0))
				r["stepSize"] = stepSize
				r["minQty"] = minQty
			if(filter.get("filterType", None) == "MIN_NOTIONAL"):
				applyToMarket = bool(filter.get("applyToMarket", False))
				if(applyToMarket):
					minNotional = str(filter.get("minNotional", 0.0))
					r["minNotional"] = minNotional

	return r

def updatePriceAndQtyReqsInAllJsons(client, keyToBeUpdated, strategyFilter=None):
	sharedPrefRootFolder = getScriptLocationPath(0) + r"\jsonTriggerFiles"
	for file in os.listdir(sharedPrefRootFolder):
		if (isInitJsonNotTeplate(file)):
			if ((strategyFilter is None) or ((strategyFilter + '_') in file)):
				with open(sharedPrefRootFolder + "\\" + file, mode='r') as sharedPrefFile:
					sharedPrefData = json.load(sharedPrefFile)
					tradedSymbol = sharedPrefData.get('a_tradedSymbol', '')
					if (tradedSymbol != ''):
						priceReqs_new = getPriceAndQtyReqs(tradedSymbol, client)
						priceReqs_old = sharedPrefData.get(keyToBeUpdated, '')
						if (priceReqs_new != priceReqs_old):
							ploggerInfo('Detected a change in the price and quantity requirements for the symbol ' + tradedSymbol + ' therefore updating the file with the name ' + file + ' now')
							sharedPrefData[keyToBeUpdated] = priceReqs_new
							dumpGlobalVariablesToJson(file[:-5], sharedPrefData, getScriptLocationPath(0))

# TODO_future v buducnu by si mozno mohol priamo zadat z ktoreho pref fiel to ma zobrat, teda mat sourceFileNamenamiesto valToBeUpdated
# def updateJsonTriggerFiles(keyToBeUpdated, sourceFileName, strategyFilter=None, clientName=None):
def updateJsonTriggerFiles(keyToBeUpdated, valToBeUpdated, strategyFilter=None, clientFilter=None):
	sharedPrefRootFolder = getScriptLocationPath(0) + r"\jsonTriggerFiles"
	for file in os.listdir(sharedPrefRootFolder):
		if (isInitJsonNotTeplate(file)):
			stratAndClient = getClientAndStrategyFromFileName(file)
			if ( ((strategyFilter is None) or (stratAndClient['strategy'] == strategyFilter)) and ((clientFilter is None) or (stratAndClient['client'] == clientFilter)) ):
				with open(sharedPrefRootFolder + "\\" + file, mode='r') as sharedPrefFile:
					sharedPrefData = json.load(sharedPrefFile)
					dic_old = sharedPrefData.get(keyToBeUpdated, '')
					if (valToBeUpdated != dic_old):
						ploggerInfo('Detected a change in ' + file + ' therefore updating the key ' + keyToBeUpdated + ' now')
						sharedPrefData[keyToBeUpdated] = valToBeUpdated
						dumpGlobalVariablesToJson(file[:-5], sharedPrefData, getScriptLocationPath(0))

# TODO_future v buducnu by tieto 2 fcie mohli byt priamo v binance module a mohol by si mat custom metody napr: order_market_buy_valid			
def validPrice(reqDic, desiredPrice):
	#price >= minPrice
	#(price-minPrice) % tickSize == 0
	
	minPrice = Decimal(str(reqDic['minPrice']))
	tickSize = Decimal(str(reqDic['tickSize']))
	desiredPriceDec = Decimal(str(desiredPrice))
	
	if (desiredPriceDec < minPrice):
		desiredPriceDec = minPrice
		# according to the docs the price should be string - but both are working
		return str(desiredPriceDec)

	if not ( (desiredPriceDec - minPrice) % tickSize == 0 ):
		desiredPriceDec = ( round( (desiredPriceDec - minPrice) / tickSize ) * tickSize) + minPrice
	# according to the docs the price should be string - but both are working
	return str(desiredPriceDec)

def validQty(reqDic, desiredPrice, desiredQty, minNotionalSafeCoef = 1.03):
	""" 
		-the min notional safe coef is designed for market orders where the price can change
			-the value can theoretically only be used at the beginning of the ladder
	"""
	
	minNotional = Decimal(str(reqDic['minNotional']))
	minQty = Decimal(str(reqDic['minQty']))
	stepSize = Decimal(str(reqDic['stepSize']))
	
	desiredPriceDec = Decimal(str(desiredPrice))
	desiredQtyDec = Decimal(str(desiredQty))
	minNotionalSafeCoefDec = Decimal(str(minNotionalSafeCoef))
	
	# v podmienke nezalezi na minNotionalSafeCoef ale pri vypocte desiredQtyDec uz pozivam radsej Decimal
	if ( desiredPriceDec * desiredQtyDec < minNotional * minNotionalSafeCoefDec):
		desiredQtyDec = ( minNotional / desiredPriceDec ) * minNotionalSafeCoefDec
	
	if (desiredQtyDec < minQty):
		desiredQtyDec = minQty
		return desiredQtyDec
	if not ( ( desiredQtyDec - minQty ) % stepSize == 0 ):
		desiredQtyDec = ( round( ( desiredQtyDec - minQty ) / stepSize ) * stepSize ) + minQty 
	
	return desiredQtyDec


def validPriceAndQty(reqDic, symbol, desiredPrice, desiredQty):
	return {'symbol': symbol, 'price': validPrice(reqDic, desiredPrice) , 'quantity': validQty(reqDic, desiredPrice, desiredQty)}
	
def validLimitPriceAndQty(reqDic, symbol, desiredPrice, desiredQty, limitKoef):
	tmp = validPriceAndQty(reqDic, symbol, desiredPrice, desiredQty)
	tmp.update({'stopPrice': validPrice(reqDic, desiredPrice*limitKoef)})
	return tmp

def getValFromSharedPrefFile(fileNameWithExtention, varName):
	"""
	 retuns None for non-existent variables or non-existent files
	"""
	from pathlib import Path
	sharedPrefFile = getScriptLocationPath(0) + r"\sharedPrefs\\" + fileNameWithExtention
	if not Path(sharedPrefFile).is_file():
		ploggerWarn('Following path of a shared file was not found: ' + getScriptLocationPath(0) + r"\sharedPrefs\\" + fileNameWithExtention)
		return None
	with open(sharedPrefFile, mode='r') as sharedPrefFile:
		sharedPrefData = json.load(sharedPrefFile)
		r = sharedPrefData.get(varName, None)
		if r is None:
			ploggerWarn('The variable ' + varName + ' could not be found in the shared file with following path: ' + getScriptLocationPath(0) + r"\sharedPrefs\\" + fileNameWithExtention, False)
		return r 

# TODO_future
def convertDustToBNB(client, clientName):
	pass

# TODO currently is in the guardian, but maybe should be in pumTheRightCon because of the constants which are beeing used here - also wanted to move use the spawner in the runner so this is kinda the same
def diffRealAndExpectCoinStocks(client, clientName, defCoin='USDT', tolerancyInDefCoin=10):
	"""
		looping through trigger jsons, counting what amout of stocks I should have and comparing with the real numbers
		not taking care of jsons which would have a coin in the which no longer exists -> in such case the whole json would crash
	"""
	r = False
	jsonStocks = {}
	
	initJsons = loadAllInitJsons(None)
	for k, intiJson in initJsons.items():
		# TODO dopln filter if key obsahuje danu strategiu - zatial ale nie je kriticke
		if(clientName in k):
			coin = intiJson['a_symbol']
			if(coin.endswith(defCoin)):
				coin = coin[:-4]
			else:
				ploggerWarn('diffRealAndExpectCoinStocks - a NON-USDT market was found in the int jsons - this was not expected!', False)

			entries = intiJson['entries']
			totalStock_json_SellPositions = 0
			lastXchangePrice = 0
			
			for stepNr, entry in entries.items():
				if(entry['typ'] in ['waitToSell', 'limitSell']):
					totalStock_json_SellPositions = totalStock_json_SellPositions + entry['qty']
					# lastXchangePrice = entry['lastXchangePrice']
			
			jsonStocks[coin] = totalStock_json_SellPositions
	realStocks = getCoinStocs(client, defCoin, True)
	
	for coinName, realStock in realStocks.items():
		if(coinName==defCoin):
			continue
		jsonStock = jsonStocks.get(coinName, 0.0)
		# if at least 1 of them not 0
		if((realStock + jsonStock) > 0.0):
			# check the diff in USDT - checkig the diff in the coin itself is useless, because there will be always a discprepancy of some sort
			lastPrice = getLastPrice(client, coinName, defCoin)
			if (lastPrice == 0):
				# can calculate the value in USDT - in future try combination with BTC
				if(realStock != jsonStock):
					ploggerWarn('diffRealAndExpectCoinStocks - discrepancy of Unknown {} amount found in the stock of coin {}. jsonStock={} / realStock={}'.format(defCoin, coinName, str(jsonStock), str(realStock)))
					r = True

			discrepancy = round((jsonStock - realStock) * lastPrice)
			# TODO by now just hardcoding 50 USDT - bude to naviazane na sumukde skript kupuje bnb na poplatky
			BNBtolerance = 900
			if(coinName=='BNB'):
				if (discrepancy > 0):
					discrepancy = max(discrepancy - BNBtolerance, 0)
				elif (discrepancy < 0):
					discrepancy = min(discrepancy + BNBtolerance, 0)
					
			# if discrepancy a positive number -> more in json than in reality
			if( discrepancy > tolerancyInDefCoin):
				ploggerWarn('diffRealAndExpectCoinStocks - discrepancy of {} {} found in the stock of coin {}. jsonStock={} > realStock={}'.format(str(discrepancy), defCoin, coinName, str(jsonStock), str(realStock)))
				r = True
			elif (discrepancy < (-1.0 * tolerancyInDefCoin)):
				ploggerErr('diffRealAndExpectCoinStocks - FIX NEEDED discrepancy of {} {} found in the stock of coin {}. jsonStock={} < realStock={}'.format(str(abs(discrepancy)), defCoin, coinName, str(jsonStock), str(realStock)))
				r = True
	return r
	
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