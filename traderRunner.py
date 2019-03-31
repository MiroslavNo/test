import pkgutil
import sys
import time

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
sharedPrefFileGuardian = 'guardian_lastClbkTime'
sharedPrefFileSkipClbkMsgDueDelay = 'lastTimeAClbkMsgWasSkipepd'
stopFlagFileName = 'runnerSTOPFlag_anyContentWillStop.txt'
# daj pozor aky mas max limit pri sys.setrecursionlimit(), pre 1500 rekurzii pri 20min loope to vystaci na 20 dni
guardianLoopingTimeInMin = 10
clbkCounterForGuardian = traderFunctions.setclbkCounterForGuardian(guardianLoopingTimeInMin)
scriptLocationPath = traderFunctions.getScriptLocationPath(0)


######################################################
#############		GET CLIENTS			##############
######################################################
clients = traderFunctions.addClients()

# musi byt globalne, aby si mohol pouzit bm.close() pre restart websocketu
bm = BinanceSocketManager(clients['tibRick'])

######################################################
#############		PRE - CHECKS		##############
######################################################

traderFunctions.checkExchangeStatus(clients['tibRick'])
traderFunctions.checkTimeSyncErrAndLoop(clients['tibRick'], 20, 300)


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
		pathList = pathname.split("\\")
		fileName = pathList[len(pathList)-1]
		
		traderFunctions.ploggerErr( 'Restarting the websocket' )
		# executing this file again
		os.system('python ' + fileName)

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
			fw = open(flagFileLocation, mode='w')
			fw.close()
			closeSocketAndRestartThisFile(False)

def runGuardian(sharedPrefFileName, sleepTimeInMin):
	time.sleep(sleepTimeInMin * 60)
	traderFunctions.ploggerInfo('Guardian is checking if the the websocket is still alive')
	
	#check if the clbk fcion did write in the last sleepTimeInMin
	if not ( traderFunctions.checkIfLastTimeOfThisEvenWasLately(sharedPrefFileName, int(round(sleepTimeInMin*60))) ):
		# if did not write, that means the clbk is not running
		traderFunctions.ploggerErr ('Trader not running, Last registered Clbk was more than ' + str(sleepTimeInMin) + ' minutes ago. Will try to restart the socket')
		closeSocketAndRestartThisFile(True)
	else:
		runGuardian(sharedPrefFileName, sleepTimeInMin)
		
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
	global clbkCounterForGuardian
	
	# musi byt tu, lebo inak pri skippovani nezarata tento loop
	clbkCounterForGuardian -= 1

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
	if( (1000 * time.time() - timeFromClbkMsg) > 1500 ):
		traderFunctions.ploggerInfo('Warn - Websocket - The timestamp in the clbk msg is in the past. The difference is ' + str(1000 * time.time() - timeFromClbkMsg) + ' miliSec', False)
		# but skip only if you did not skip in the last 2 sec (in case the msgs would be coming with a delay)
		if not ( traderFunctions.checkIfLastTimeOfThisEvenWasLately(sharedPrefFileSkipClbkMsgDueDelay, 2) ):
			traderFunctions.ploggerInfo('Warn - Websocket - Did NOT skip a clbk msg in the last 2 seconds, so skipping this one', False)
			traderFunctions.writeEventTimeInSharedPrefs(sharedPrefFileSkipClbkMsgDueDelay)
			return
		else:
			traderFunctions.ploggerInfo('Warn - Websocket - Did skip a clbk msg in the last 2 seconds, so NOT skipping this one', False)
	
	symbolPricesFromTicker = traderFunctions.getPricesFromClbkMsg(msg)
		
	tmp = {}
	for k, singleJsonDic in globalVariablesDictionary.items():
		r = strats[singleJsonDic['strategy']](clients[singleJsonDic['client']], symbolPricesFromTicker, singleJsonDic)
		if not (r is None):
			tmp[k] = r

	#Empty dictionaries evaluate to False in Python
	if bool(tmp):
		globalVariablesDictionary.update(tmp)
		updateJsons(tmp)
	
	if ( clbkCounterForGuardian < 1 ):
		traderFunctions.writeEventTimeInSharedPrefs(sharedPrefFileGuardian)
		clbkCounterForGuardian = traderFunctions.setclbkCounterForGuardian(guardianLoopingTimeInMin)
	
	# running the check for stopping the script every 90s
	if(clbkCounterForGuardian % 90 == 0):
		stopIfFlag(stopFlagFileName)


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

traderFunctions.ploggerInfo ('Trade Runner started')
# Gather all strategies and all mandatoryInitVars
traderFunctions.ploggerInfo ('Gathering all strategies and all mandatoryInitVars')

for importer, modname, ispkg in pkgutil.iter_modules(strat.__path__, strat.__name__ + "."):
	module = __import__(modname, fromlist="dummy")
	#modname[len(strat.__name__) + 1 : ] ti vrati nazov modulu bez package a prefix (nazov foldra)
	traderFunctions.ploggerInfo ('Found the strategy "' + modname + '". It will be accesible under the key "' + modname[len(strat.__name__) + 1 : ] + '"', True)
	strats[modname[len(strat.__name__) + 1 : ]] = getattr(module,'trade')
	mandatoryInitVars[modname[len(strat.__name__) + 1 : ]] = getattr(module,'mandatoryInitVars')
	
	# POZN:
	# HLAVNA METODA KAZDEJ STRATGIE = trade():
	# MANDATORY INIT VARS = mandatoryInitVars

globalVariablesDictionary = traderFunctions.loadAllInitJsons(mandatoryInitVars)
globalVariablesDictionary = checkIfStratAndClientFromEveryJsonExist(globalVariablesDictionary, strats, clients)
logJsonsWhichWillRun(globalVariablesDictionary)
# write the epoch time for the independent check, if the script is running
traderFunctions.writeEventTimeInSharedPrefs(sharedPrefFileGuardian)

startTraderSocket()
runGuardian(sharedPrefFileGuardian, guardianLoopingTimeInMin)