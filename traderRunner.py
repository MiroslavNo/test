import pkgutil
import sys
import time
import traceback

import traderFunctions
import strat

from binance.websockets import BinanceSocketManager
from binance.enums import *

sys.setrecursionlimit(1500)

######################################################
#############		START LOGGING		##############
######################################################
traderFunctions.startLoggers()

######################################################
#############			GLOBALS			##############
######################################################
strats = {}
mandatoryInitVars = {}
sharedPrefFileSkipClbkMsgDueDelay = 'lastTimeAClbkMsgWasSkipepd'
stopFlagFileName = 'runnerSTOPFlag_anyContentWillStop.txt'
sharedPrefFileGuardian = 'guardian_lastClbkTime'
# 1,25 je bezpecnostny koef
guardian_loopTimeInSec = int(round((traderFunctions.getValFromSharedPrefFile('guardian_loopTimeInMin.json', 'guardian_loopTimeInMin')) * 60 / 1.25))
# pociatocna hodnota, hned pri prvom loope sa potom nastavi na spravnu
nextTimeForGuardianReport = 0
nextTimeForFlagCheck = 0
scriptLocationPath = traderFunctions.getScriptLocationPath(0)


######################################################
#############		GET CLIENTS			##############
######################################################
clients = traderFunctions.addClients()

# musi byt globalne, aby si mohol pouzit bm.close() pre restart websocketu
# TODO toto over ci nie je v rozpore s tym ked chces pouzivat viacero clientov
# TODO ked si overil a funguje, tak prehod vsetky administrativne ukony na mno
bm = BinanceSocketManager(clients['tibRick'])

######################################################
#############		PRE - CHECKS		##############
######################################################

traderFunctions.checkExchangeStatus(clients['mno'])
traderFunctions.checkTimeSyncErrAndLoop(clients['mno'], 20, 300)


######################################################
#############		HELPER FUNCTIONS	##############
######################################################		

def logJsonsWhichWillRun(dict):
	for k, d in globalVariablesDictionary.items():
		traderFunctions.ploggerInfo('The json with key ' + k + ' will run', True)

def updateJsons (dicsToBeUpdated):
	for k, v in dicsToBeUpdated.items():
		# pre nove dict automaticky vytvori novy file
		# toto mozes v buducnu zapnut, ked budes potrebovat tuto fcionalitu
		#if (v == 'INACTIVATE'):
		#	traderFunctions.moveJsonIntoInactiveOnes(k)
		#else:
		traderFunctions.dumpGlobalVariablesToJson(k, v, scriptLocationPath)
		traderFunctions.ploggerInfo( k + '.json updated' )

def checkIfStratAndClientFromEveryJsonExist(globalVariablesDictionary, strats, clients):
	tmp = list()
	for k, d in globalVariablesDictionary.items():
		s = strats.get(d['strategy'], 'NotFound')
		if (s == 'NotFound'):
			tmp.append(k)
			print ('ERR - In the json ' + str(k) + ' the following strategy could not be found: ' + d['strategy'] + ' - This json will be skipped [This is only a print]')
		c = clients.get(d['client'], 'NotFound')
		if (c == 'NotFound'):
			tmp.append(k)
			print ('ERR - In the json ' + str(k) + ' the following client could not be found: ' + d['client'] + ' - This json will be skipped [This is only a print]')

	for k in tmp:
		del globalVariablesDictionary[k]
	
	return globalVariablesDictionary

def printFirstClbkOccurence(startTimeInSec):
	while(True):
		if ( traderFunctions.checkIfLastTimeOfThisEventWasLately(sharedPrefFileGuardian, time.time() - startTimeInSec )):
			print('INFO - First clbk message processed')
			break
		else:
			print('INFO - First clbk message NOT YET processed')
			time.sleep(5)
			
def closeSocketAndRestartThisFile(boolRestart):
	traderFunctions.ploggerWarn('Closing the socket', False)
	bm.close()	
	from twisted.internet import reactor
	reactor.stop()
	
	if(boolRestart):
		# protection agains infinite looping / sleep for 60s
		time.sleep(60)
		traderFunctions.ploggerWarn("Restarting the Websocket")
		# restart file
		import os
		pathname = os.path.realpath(sys.argv[0])        
		# extract only the filename
		# pathList = pathname.split("\\")
		# fileName = pathList[len(pathList)-1]
		
		# executing this file again
		traderFunctions.ploggerInfo( 'Calling the following command on the cmd: ' + 'python ' + fileName)
		os.system('python "' + pathname + '"')
		traderFunctions.ploggerInfo( 'It should not come to this point, but as the previous execution failed, just checking ' )
	else:
		print('THIS BAT WINDOW CAN BE CLOSED [only a print]')

# sys.exit() crashuje, ale nie kvoli guardianov, kvoli niecomu inemu
# sys.exit() by si neporeboval, ak by si nemal guardiana
# po tomto uz len clbck fciu treba otestovat
# https://stackoverflow.com/questions/32053618/how-to-to-terminate-process-using-pythons-multiprocessing
# DAJ TO BEZ UPLNEHO TERMINATE - HALVNE JE ABY SI NEPRERUSIL CLBK FCIU -> a ta sa zastavi, ked zavolas stopIfFlag
def stopIfFlag(flagFileName):
	flagFileLocation = scriptLocationPath + r"\sharedPrefs\\" + flagFileName
	with open(flagFileLocation, mode='r') as f:
		content = f.read()
		f.close()
		if not (content == ''):
			traderFunctions.ploggerWarn('Found a flag in file ' + flagFileName + '. Will stop the socket', False)
			# wiping the content of the file
			fw = open(flagFileLocation, mode='w')
			fw.close()
			closeSocketAndRestartThisFile(False)
		
def getTimeFromClbkMsg(msg):
	try:
		gotTime = msg[0].get('E', 'Null')
	except (IndexError):
		return None
	
	try:
		timeInt = int(gotTime)
	except (ValueError):
		return None
	
	return timeInt
	

######################################################
#############		CALLBACK			##############
######################################################
def trader_callbck(msg):
	global globalVariablesDictionary
	global nextTimeForGuardianReport
	global nextTimeForFlagCheck

	if (type(msg) == 'dict'):
		traderFunctions.ploggerErr('The message from the websocket is a dictionary, but should be a list - maybe an error appeared')
		if (msg['e'] == 'error'):
			traderFunctions.ploggerErr('Websocket returned the following error:\n ' + msg['m'])
			closeSocketAndRestartThisFile(True)
			# making sure this file will not continue to run (should not get to this point anyway)
			traderFunctions.ploggerErr('Have got to a point where I should not be')
			sys.exit()
			return
	
	timeFromClbkMsg = getTimeFromClbkMsg(msg)
	if (timeFromClbkMsg is None):
		traderFunctions.ploggerWarn('There could be no time found in the ClbkMsg. Will put the whole msg into the Info log file', False)
		traderFunctions.ploggerInfo(msg)
		return
	
	# skip if time difference is bigger than 2sec (2000 mSec) - since it can happen, that my clbk processing will be slower than the interval of the clbks (1 sec)
	currTimeInSec = time.time()
	if( (1000 * currTimeInSec - timeFromClbkMsg) > 1750 ):
		traderFunctions.ploggerInfo('Warn - Websocket - delay is ' + str(1000 * currTimeInSec - timeFromClbkMsg) + ' miliSec', True)
		# but skip only if you did not skip in the last 2 sec (in case the msgs would be coming with a delay)
		if not ( traderFunctions.checkIfLastTimeOfThisEventWasLately(sharedPrefFileSkipClbkMsgDueDelay, 2) ):
			traderFunctions.writeEventTimeInSharedPrefs(sharedPrefFileSkipClbkMsgDueDelay)
			return
	
	pricesFromTicker = traderFunctions.getPricesFromClbkMsg(msg)
		
	tmp = {}
	# TODO_future malo by to tak fungovat lepsie, ze traderFunctions by si prerobil na classu a dictionary spolu s clientom by boli member variables - tym padom by si nemusel volat funkciu s parametrami, ale vzdy by si iba zavolal metodu trade na danom objecte 
	for k, singleJsonDic in globalVariablesDictionary.items():
		try:
			r = strats[singleJsonDic['strategy']](clients[singleJsonDic['client']], singleJsonDic, pricesFromTicker)
			if not (r is None):
				tmp[k] = r
		except Exception:
			traderFunctions.ploggerErr('Following traceback error came from the strategy module:\n ' + traceback.format_exc())
			# kym som si neni isty chybami, takradsej stompem skript
			closeSocketAndRestartThisFile(False)

	#Empty dictionaries evaluate to False in Python
	if bool(tmp):
		globalVariablesDictionary.update(tmp)
		updateJsons(tmp)
	
	if ( nextTimeForGuardianReport < currTimeInSec ):
		traderFunctions.writeEventTimeInSharedPrefs(sharedPrefFileGuardian)
		nextTimeForGuardianReport = currTimeInSec + guardian_loopTimeInSec
	
	# running the check for stopping the script every 90s
	if ( nextTimeForFlagCheck < currTimeInSec ):
		stopIfFlag(stopFlagFileName)
		nextTimeForFlagCheck = currTimeInSec + 90

######################################################
#############		WEBSOCKET			##############
######################################################	
def startTraderSocket():
	conn_key = bm.start_ticker_socket(trader_callbck)
	
	# then start the socket manager
	traderFunctions.ploggerInfo ('Trader(runner) - Starting the websocket', True)
	bm.start()



######################################################
#############		LAUNCH			##############
######################################################

traderFunctions.ploggerInfo ('\n')
traderFunctions.ploggerInfo ('Trade Runner started')
# Gather all strategies and all mandatoryInitVars
traderFunctions.ploggerInfo ('Gathering all strategies and all mandatoryInitVars')

# making sure stopIfFlagFile is empty
fw = open(scriptLocationPath + r"\sharedPrefs\\" + stopFlagFileName, mode='w')
fw.close()

for importer, modname, ispkg in pkgutil.iter_modules(strat.__path__, strat.__name__ + "."):
	module = __import__(modname, fromlist="dummy")
	#modname[len(strat.__name__) + 1 : ] ti vrati nazov modulu bez package a prefix (nazov foldra)
	traderFunctions.ploggerInfo ('Found the strategy "' + modname + '". It will be accesible under the key "' + modname[len(strat.__name__) + 1 : ] + '"', True)
	strats[modname[len(strat.__name__) + 1 : ]] = getattr(module,'trade')
	mandatoryInitVars[modname[len(strat.__name__) + 1 : ]] = getattr(module,'mandatoryInitVars')
	
	# POZN:
	# HLAVNA METODA KAZDEJ STRATGIE = trade():
	# MANDATORY INIT VARS = mandatoryInitVars

traderFunctions.updatePriceAndQtyReqsInAllJsons(clients['mno'], 'u_PriceQtyReqs')
# TODO v buducnu daj viac genericku fciu, kde budes vediet davat nazvy strategii ako filter, lebo pri inych strategiach by tieto hodnoty boli nechcene. A takisto filter pre clientov, lebo na kazdom ucte su ine sumy a to ma tiez vplyv v urcitych pripadoch
traderFunctions.updateJsonTriggerFiles('u_singleEntryAmounts', traderFunctions.getValFromSharedPrefFile('u_singleEntryAmounts_tibRick.json', 'u_singleEntryAmounts'))

globalVariablesDictionary = traderFunctions.loadAllInitJsons(mandatoryInitVars)
globalVariablesDictionary = checkIfStratAndClientFromEveryJsonExist(globalVariablesDictionary, strats, clients)
logJsonsWhichWillRun(globalVariablesDictionary)

# TODO following checks for pumpTheRightCoin before startup:
# 1, grouping of close entries in the jsons
#	- interate from top to bottom and if 2 with the price closer as 0,1% merge them, the break the loop and loop again (with tis you will have a clean logic how to do it)
# 2, with client.get_all_orders check if all orders are documented in jsons, if not, then send a err email
# 3, check if in the meantime are orders which got fillfiled - adjust the jsons accordingly
# 4, count the amount which should be owned of a coin according to the jsons and compare with the actuall amount of the coin - should not do anything in small discrepancies, because it can be, that an order just got filled, or small discrepancies because of partially filled roders etc.
# 5, update price requirements for all jsons (u_ variables)
# 5, pre kazdy ucet budes mat array s velkostou Qty pre jednotlive nakupy, pri starte skritu updatenes aj tieto hodnoty
# 6, convert small amounts to BNB
startTraderSocket()
printFirstClbkOccurence(time.time() - 5)
