import traderFunctions
import time
import re
import socket
import os

# musi byt, lebo niektore metody z traderFunctions maju implementovany logging
traderFunctions.startLoggers()
# budes potrebovat pre getBalance a ensureBNB
clients = traderFunctions.addClients()

sharedPrefFileGuardian = 'guardian_lastClbkTime'
fileWithLoopTimesForGuardian = 'guardian_loopTimeInMin.json'
guardian_loopTimeInMin = (traderFunctions.getValFromSharedPrefFile(fileWithLoopTimesForGuardian, 'guardian_loopTimeInMin'))
bnbUpdate_loopTimeInMin = (traderFunctions.getValFromSharedPrefFile(fileWithLoopTimesForGuardian, 'bnbUpdate_loopTimeInMin'))
balanceUpdate_loopTimeInMin = (traderFunctions.getValFromSharedPrefFile(fileWithLoopTimesForGuardian, 'balanceUpdate_loopTimeInMin'))


######################################################
#############		FUNCTIONS			##############
######################################################	

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

def reconnect(SSIDs):
	# a call of this function looks like: reconnect(['KDG-DDEBE', 'FRITZ!Box 7490'])
	for SSID in SSIDs:
		os.system('netsh wlan connect ssid="' + SSID + '" name="' + SSID + '"')
		time.sleep(15)
		if(hasInternet):
			return True
	# trying one more time
	for SSID in SSIDs:
		os.system('netsh wlan connect ssid="' + SSID + '" name="' + SSID + '"')
		time.sleep(15)
		if(hasInternet):
			return True
	return False

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
			traderFunctions.ploggerWarn('There is not enough USDT for buying BNB for fees. Free USDT=' + str(traderFunctions.traderFunctions.getAvailableAmount(client, USDT, roundDigits=0)) + ' / USDT required to buy BNB=' + str(1.1 * calcQty_inBNB * lastPrice), False)
		else:
			# get valid amount
			calcQty_inBNB = traderFunctions.validQty(traderFunctions.getPriceAndQtyReqs(BNBUSDT, client), lastPrice, calcQty_inBNB)
			# create order
			traderFunctions.ploggerInfo('ensureBNBforFees - creating a market order for ' + str(calcQty_inBNB) + ' BNBs')
			client.order_market_buy(symbol=BNBUSDT, quantity=calcQty_inBNB)

def runGuardian(sharedPrefFileName, sleepTimeInMin):
	counter=0
	counterCycleForBNBUpdate = round (intervalInMinForBNBUpdate / sleepTimeInMin)
	counterCycleForBalanceUpdate = round (intervalInMinForBalanceUpdate / sleepTimeInMin)
	traderFunctions.ploggerInfo('GUARDIAN - START', True)
	
	while (True):
		time.sleep(sleepTimeInMin * 60)
		traderFunctions.ploggerInfo('GUARDIAN - checking if websocket alive', True)
		
		if ( traderFunctions.checkIfLastTimeOfThisEvenWasLately(sharedPrefFileName, int(round(sleepTimeInMin*60))) ):
			# confirm that everything OK
			writeTimeIntoReportHTML()
			counter=+1
			if(counter % counterCycleForBNBUpdate == 0):
				# TODO_future make more generic with the amount
				for k, client in clients.items():
					if (k != 'mno'):
						ensureBNBforFees(client, 50000)
			if(counter % counterCycleForBalanceUpdate == 0):
				# TODO prerob v buducnu, aj tak getAccountsBalance bude treba viac zgeneralizovat
				os.system('getAccountsBalance.py')
		else:
			# resetting the counter just to be sure the wont be interference between get BNB or get BALANCE
			counter=0
			#getting the path for the restart batch
			restartBatPath = (traderFunctions.getScriptLocationPath(1) + r'\batch\03_RESTART tradeRunner.bat')
			errMsgToBeSent = 'GUARDIAN - Trader not running, Last registered Clbk was more than ' + str(sleepTimeInMin) + ' minutes ago.\n'

			if ( hasInternet ):
				# restart the programm - this bat will restart only the runner, NOT THE GUARDIAN
				errMsgToBeSent = errMsgToBeSent + 'GUARDIAN - Internet is working, will try to restart the programm\n'
				traderFunctions.ploggerErr (errMsgToBeSent)
				os.system('"' + restartBatPath + '"')
			else:
				errMsgToBeSent = errMsgToBeSent + 'GUARDIAN - Internet is NOT working, will try to reconnect to the wifi\n'
				if(reconnect(['KDG-DDEBE', 'FRITZ!Box 7490'])):
					errMsgToBeSent = errMsgToBeSent + 'GUARDIAN - Reconnect successful, will try to restart the programm\n'
					traderFunctions.ploggerErr (errMsgToBeSent)
					os.system('"' + restartBatPath + '"')
				else:
					errMsgToBeSent = errMsgToBeSent + 'GUARDIAN - Reconnect was not working, will check every ' + str(sleepTimeInMin) + ' minutes, and if there will be connection, will restart the runner'
					# aj ked nie je internet, nepotrebujem try catch, lebo the je uz v metode, ktora posiela maily
					traderFunctions.ploggerErr (errMsgToBeSent)
						
					while (True):
						time.sleep(sleepTimeInMin * 60)
						if ( hasInternet ):
							os.system('"' + restartBatPath + '"')
							break




######################################################
#############				MAIN		##############
######################################################	

# TODO - tento main je mysleny tak, ze ked buem vediet restartovat PC, kym to vsak nerobim, staci uplne obycajny call na guardina
##############################	MAIN	####################################
# if(hasInternet()):
# 	runGuardian(sharedPrefFileGuardian, guardian_loopTimeInMin)
# else:
# 	if(reconnect(['KDG-DDEBE', 'FRITZ!Box 7490'])):
# 		runGuardian(sharedPrefFileGuardian, guardian_loopTimeInMin)
# 	else:
# 		try:
# 			traderFunctions.ploggerErr ('GUARDIAN - NO INTERNET')
# 		except:
# 			# just because of the err coming from unsuccesful email
# 			pass

# pre checks
traderFunctions.checkExchangeStatus(clients['mno'])
traderFunctions.checkTimeSyncErrAndLoop(clients['mno'], 20, 300)
# ensureBNBforFees at the beginning as well, because if trades happen at the very beggining
ensureBNBforFees(clients['tibTick'], 50000)
runGuardian(sharedPrefFileGuardian, guardian_loopTimeInMin)
traderFunctions.ploggerErr ('ERROR - THE GUARDIAN HAS STOPPED')
	
