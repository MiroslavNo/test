import traderFunctions
import time
import datetime
import re
import socket
import os

# musi byt, lebo niektore metody z traderFunctions maju implementovany logging
traderFunctions.startLoggers()
# budes potrebovat pre getBalance a ensureBNB
clients = traderFunctions.addClients()

sharedPrefFileGuardian_lastClbkTime = 'guardian_lastClbkTime'
sharedPrefFileGuardian_lastRestart = 'guardian_lastRestart'
fileWithLoopTimesForGuardian = 'guardian_loopTimeInMin.json'
guardian_loopTimeInMin = (traderFunctions.getValFromSharedPrefFile(fileWithLoopTimesForGuardian, 'guardian_loopTimeInMin'))
bnbUpdate_loopTimeInMin = (traderFunctions.getValFromSharedPrefFile(fileWithLoopTimesForGuardian, 'bnbUpdate_loopTimeInMin'))
balanceUpdate_loopTimeInMin = (traderFunctions.getValFromSharedPrefFile(fileWithLoopTimesForGuardian, 'balanceUpdate_loopTimeInMin'))
guardian_maxRestartFrequencyInMin = (traderFunctions.getValFromSharedPrefFile(fileWithLoopTimesForGuardian, 'guardian_maxRestartFrequencyInMin'))

restartBatPath = (traderFunctions.getScriptLocationPath(1) + r'\batch\03_RESTART tradeRunner.bat')
restartBatCmd = 'start cmd /k "' + restartBatPath + '" ' + str(datetime.datetime.now().strftime("%Y%d%m_%H%M"))

######################################################
#############		FUNCTIONS			##############
######################################################	

def restartSystem():
	while(True):
		# restart only if not restarted lately
		if not ( traderFunctions.checkIfLastTimeOfThisEventWasLately(sharedPrefFileGuardian_lastRestart, int(round(guardian_maxRestartFrequencyInMin*60))) ):
			traderFunctions.writeEventTimeInSharedPrefs(sharedPrefFileGuardian_lastRestart)
			os.system(restartBatCmd)
			break
		else:
			# if the time is not right, wait for 60s and check again
			ploggerInfo('GUARDIAN - Last Restart was lately, therefore going to wait and check again in a minute')
			time.sleep(60)

def hasInternet(host="8.8.8.8", port=53, timeout=3):
  """
  Host: 8.8.8.8 (google-public-dns-a.google.com)
  OpenPort: 53/tcp
  Service: domain (DNS/TCP)
  """
  try:
    socket.setdefaulttimeout(timeout)
    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
    return True
  except Exception as ex:
    return False

def loopWhileNoInternet():
	while (True):
		time.sleep(guardian_loopTimeInMin * 60)
		if ( hasInternet() ):
			traderFunctions.ploggerInfo('internet connection working -> restarting with command {}'.format(restartBatCmd))
			restartSystem()
			break
		else:
			traderFunctions.ploggerWarn('still no internet, waiting for another {} minutes'.format(str(guardian_loopTimeInMin)), False)

# TODO mozno budes musiet odstranit, ked PC nebude mat wifi kartu
def reconnect(SSIDs):
	# a call of this function looks like: reconnect(['KDG-DDEBE', 'FRITZ!Box 7490'])
	for SSID in SSIDs:
		os.system('netsh wlan connect ssid="' + SSID + '" name="' + SSID + '"')
		time.sleep(15)
		if(hasInternet()):
			return True
	# trying one more time
	for SSID in SSIDs:
		os.system('netsh wlan connect ssid="' + SSID + '" name="' + SSID + '"')
		time.sleep(15)
		if(hasInternet()):
			return True
	return False

def reconnectAndLoopWhileNoInternet():
	errMsgToBeSent = 'GUARDIAN - Internet is NOT working, will try to reconnect to the wifi\n'
	if(reconnect(['KDG-DDEBE', 'FRITZ!Box 7490'])):
		errMsgToBeSent = errMsgToBeSent + 'GUARDIAN - Reconnect successful, will try to restart the programm\n'
		traderFunctions.ploggerErr (errMsgToBeSent)
		restartSystem()
	else:
		errMsgToBeSent = errMsgToBeSent + 'GUARDIAN - Reconnect was not working, will check every ' + str(guardian_loopTimeInMin) + ' minutes, and if there will be connection, will restart the runner'
		# aj ked nie je internet, nepotrebujem try catch, lebo the je uz v metode, ktora posiela maily
		try:
			traderFunctions.ploggerErr (errMsgToBeSent)
		except:
			pass
		loopWhileNoInternet()

def writeTimeIntoReportHTML():
	htmlFilePath = traderFunctions.getScriptLocationPath(1) + r'\ReportsAndLogs\report.html'
	htmlFile = open(htmlFilePath, 'r')
	htmlContent = htmlFile.read()
	htmlFile.close()

	timePlchldr_begin = 'Last Guardian Check: '
	regexTimePlchldr = re.compile("Last Guardian Check: .*")
	htmlContent = re.sub(regexTimePlchldr, timePlchldr_begin + time.strftime("%d.%m.%Y %H:%M:%S"), htmlContent)
	
	#write the output
	htmlFile = open(htmlFilePath, 'w')
	htmlFile.write(htmlContent)
	htmlFile.close()

def ensureBNBforFees(client, amountOfFundsInUSDT):
	BNB = 'BNB'
	USDT = 'USDT'
	BNBUSDT = BNB + USDT
	
	traderFunctions.ploggerInfo('GUARDIAN - running ensureBNBforFees')
	binanceFeePerc = 0.001
	
	desiredAmountOfBNB_inUSDT = round(amountOfFundsInUSDT * binanceFeePerc)
	lastPrice = traderFunctions.getLastPrice(client, BNB, USDT)
	desiredAmountOfBNB_inBNB = round(desiredAmountOfBNB_inUSDT / lastPrice, 2)
	# TODO tuto v buducnosti daj len to mnozstvo, ktore nie je dokumentovane v jsone pre BNBUSDT market
	currentAmountOfBNB_inBNB = traderFunctions.getAvailableAmount(client, BNB, roundDigits=2)
	
	if(currentAmountOfBNB_inBNB > desiredAmountOfBNB_inBNB):
		traderFunctions.ploggerInfo('ensureBNBforFees - there is enough BNB ( currentAmountOfBNB_inBNB=' + str(currentAmountOfBNB_inBNB) + ', desiredAmountOfBNB_inBNB=' + str(desiredAmountOfBNB_inBNB)) 
	else:
		traderFunctions.ploggerInfo('ensureBNBforFees - there is NOT enough BNB ( currentAmountOfBNB_inBNB=' + str(currentAmountOfBNB_inBNB) + ', desiredAmountOfBNB_inBNB=' + str(desiredAmountOfBNB_inBNB))
		# buying 3 times the amount so it dont have to happen all the time (max would be for 3 *0.1 perc of all funds which for 50k is 150dollars, which is fine)
		calcQty_inBNB = 3 * (desiredAmountOfBNB_inBNB - currentAmountOfBNB_inBNB)
		# check if enough USDT for buying BNB (safety coef of 1.1)
		if not (traderFunctions.hasAvailableAmount(client, USDT, (1.1 * calcQty_inBNB * lastPrice))):
			traderFunctions.ploggerWarn('There is not enough USDT for buying BNB for fees. Free USDT=' + str(traderFunctions.getAvailableAmount(client, USDT, roundDigits=0)) + ' / USDT required to buy BNB=' + str(1.1 * calcQty_inBNB * lastPrice), False)
		else:
			# get valid amount
			calcQty_inBNB = traderFunctions.validQty(traderFunctions.getPriceAndQtyReqs(BNBUSDT, client), lastPrice, calcQty_inBNB)
			# create order
			traderFunctions.ploggerInfo('ensureBNBforFees - creating a market order for ' + str(calcQty_inBNB) + ' BNBs')
			client.order_market_buy(symbol=BNBUSDT, quantity=calcQty_inBNB)

def runGuardian():
	counter=0
	counterCycleForBNBUpdate = round (bnbUpdate_loopTimeInMin / guardian_loopTimeInMin)
	counterCycleForBalanceUpdate = round (balanceUpdate_loopTimeInMin / guardian_loopTimeInMin)
	
	while (True):
		time.sleep(guardian_loopTimeInMin * 60)
		traderFunctions.ploggerInfo('GUARDIAN - checking if websocket alive', True)
		
		if ( traderFunctions.checkIfLastTimeOfThisEventWasLately(sharedPrefFileGuardian_lastClbkTime, int(round(guardian_loopTimeInMin*60))) ):
			# confirm that everything OK
			writeTimeIntoReportHTML()
			counter=+1
			if(counter % counterCycleForBNBUpdate == 0):
				# TODO_future make more generic with the amount
				for k, client in clients.items():
					if (k != 'mno'):
						ensureBNBforFees(client, 50000)
						if(traderFunctions.diffRealAndExpectCoinStocks(clients[k], k)):
							# TODO only in the testing phase, to prevent further damage
							# TODO neskor to asi odstran, elbo by sa mohlo stat ze akurat medzi json a skutocnostou prebehne nejaky sell, v podstate mas v tej metode aj logovanie, takze by stacilo keby si to zavola bez if
							traderFunctions.ploggerErr ('Found a discrepancy in the stocks, going to stop the script')
							os.system('"' + traderFunctions.getScriptLocationPath(1) + r'\batch\02_STOP tradeRunner.bat"')
			if(counter % counterCycleForBalanceUpdate == 0):
				# TODO prerob v buducnu, aj tak getAccountsBalance bude treba viac zgeneralizovat
				# nemal by si to mat takto, lebo to nechava otvoreny connection a po case dosiahne limit poctu pripojeni
				os.system('getAccountsBalance.py')
		else:
			# resetting the counter just to be sure the wont be interference between get BNB or get BALANCE
			counter=0

			if ( hasInternet() ):
				# restart the programm - this bat will restart only the runner, NOT THE GUARDIAN
				traderFunctions.ploggerErr ('GUARDIAN - Trader not running, Last registered Clbk was more than ' + str(guardian_loopTimeInMin) + ' minutes ago.\nInternet is working, will try to restart the programm')
				restartSystem()
			else:
				reconnectAndLoopWhileNoInternet()




######################################################
#############				MAIN		##############
######################################################	

# pre checks
# note: in the runner no internet check is needed, if no internet the runner will crash -> the idea is to handle the situation in the runner and once there is internet the runner will be restarted. Also, as it is trying to reconnect, internet should be checked only from 1 place
if not hasInternet():
	reconnectAndLoopWhileNoInternet()
	
traderFunctions.checkExchangeStatus(clients['mno'])
traderFunctions.checkTimeSyncErrAndLoop(clients['mno'], 20, 300)
traderFunctions.ploggerInfo('GUARDIAN - START', True)
# ensureBNBforFees at the beginning as well, because if trades happen at the very beggining
ensureBNBforFees(clients['tibRick'], 50000)
# TODO toto by malo ist na prvy krat do trade runnera (ked vrati false tak prerusit skript) a potom pri opakovackach by malo byt tuto v guardianovi
if(traderFunctions.diffRealAndExpectCoinStocks(clients['tibRick'], 'tibRick')):
	# TODO only in the testing phase, to prevent further damage
	traderFunctions.ploggerErr ('Found a discrepancy in the stocks, going to stop the script')
	os.system('"' + traderFunctions.getScriptLocationPath(1) + r'\batch\02_STOP tradeRunner.bat"')
runGuardian()
traderFunctions.ploggerErr ('ERROR - THE GUARDIAN HAS STOPPED')
	
