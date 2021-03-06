import traderFunctions
import time
import datetime
import re
import socket
import os
import sys
from collections import Counter

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
			traderFunctions.ploggerInfo('GUARDIAN - Last Restart was lately, therefore going to wait and check again in a minute')
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

def writeTimeIntoReportHTML(clientName):
	htmlFilePath = traderFunctions.getScriptLocationPath(1) + r'\ReportsAndLogs\report_' + clientName + '.html'
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

def getAccountsBalance(clientName):
	htmlBalanceFilePath = traderFunctions.getScriptLocationPath(1) + r'\ReportsAndLogs\report_' + clientName + '.html'
	htmlFile = open(htmlBalanceFilePath, 'r')
	htmlContent = htmlFile.read()
	htmlFile.close()

	lastRunDate = htmlContent[13:19]
	# GET BALANCES
	tibRick_BTC = traderFunctions.getAccoutBalances(clients[clientName], 'BTC', 0.001, False)
	mno_BTC = traderFunctions.getAccoutBalances(clients['mno'], 'BTC', 0.001, False)
	
	btcUsdtPrice = traderFunctions.getLastPrice(clients[clientName], 'BTC', 'USDT')
	bnbBtcPrice = traderFunctions.getLastPrice(clients[clientName], 'BNB', 'BTC')
	
	sumBalances = Counter(tibRick_BTC) + Counter(mno_BTC)

	total_BTC = float(sumBalances.get('total'))
	total_USDT = round(total_BTC * btcUsdtPrice)
	total_BTC_tibRick = float(tibRick_BTC.get('total'))
	total_BNB_mno = float(mno_BTC.get('total')) / bnbBtcPrice

	# CALCULATE THE REST
	# calculateInterest
	EURUSD = 1.14
	vlozenePeniaze = 114199.0
	vlozenePeniaze_pozicane = 20500 + 24000 + 22000
	urokDenny = 460/30
	zaciatokPocitaniaUroku = datetime.date(2018, 5, 1)
	pocetDni = int(str(datetime.date.today() - zaciatokPocitaniaUroku)[0:3])
	urok = float(pocetDni) * urokDenny
	spoluPozicane = vlozenePeniaze_pozicane + urok
	spoluVlozene = vlozenePeniaze + urok
	spoluPozicane_USD = round(spoluPozicane * EURUSD, -2)
	spoluVlozene_USD = round(spoluVlozene * EURUSD, -2)

	runToday = False
	# testing if already run today
	if (lastRunDate == time.strftime("%d.%m.")):
		runToday = True
		regex = re.compile("\['" + time.strftime("%d.%m") + "', .*\n")
		htmlContent = re.sub(regex, '', htmlContent)
	
	lineBreak = '\n'

	#replace time
	plchldr = 'Report from: '
	#timePlchldr_end = '</p></b>'
	regex = re.compile("Report from: .*")
	htmlContent = re.sub(regex, plchldr + time.strftime("%d.%m.%Y %H:%M:%S"), htmlContent)

	#replace Investovane / Pozicane
	plchldr = '<br><b>I/P:</b><br>'
	regex = re.compile(plchldr + ".*")
	htmlContent = re.sub(regex, plchldr + str(round(spoluVlozene_USD / 1000, 1)) + ' / ' + str(round(spoluPozicane_USD / 1000, 1)), htmlContent)

	#extend USD chart
	plchldr = '//$$DATACHART_USD$$'
	htmlContent = htmlContent.replace(plchldr, "['" + time.strftime("%d.%m") + "', " + str(round(total_USDT, -2)) + "]," + lineBreak + plchldr)

	#extend BTC_tibRick chart
	plchldr = '//$$DATACHART_BTC_tibRick$$'
	htmlContent = htmlContent.replace(plchldr, "['" + time.strftime("%d.%m") + "', " + str(round(total_BTC_tibRick, 2)) + "]," + lineBreak + plchldr)

	#extend BNB_mno chart
	plchldr = '//$$DATACHART_BNB_mno$$'
	htmlContent = htmlContent.replace(plchldr, "['" + time.strftime("%d.%m") + "', " + str(round(total_BNB_mno, 0)) + "]," + lineBreak + plchldr)
	
	#portfolio chart data
	portfolioChartData = 'USDT' + "', " + str(round(sumBalances.get('USDT') * btcUsdtPrice, 0)) + ", '" + str(int(round(sumBalances.get('USDT') / sumBalances.get('total') , 0) * 100)) + "%' ],['"
	for key, item in sorted(sumBalances.items()):
		if not key in ['total', 'USDT']:
			portfolioChartData = portfolioChartData + key + "', " + str(round(sumBalances.get(key) * btcUsdtPrice, 0)) + ", '" + str(int(round(sumBalances.get(key) / sumBalances.get('total'), 0) * 100)) + "%' ],['"

	plchldr_begin = "var data_Portfolio = google"
	plchldr_end = "]);"
	regexPlchldr = re.compile(plchldr_begin + ".*")
	plchldr_begin = plchldr_begin + r".visualization.arrayToDataTable([['Element', 'ValInUSD', { role: 'annotation' } ],['"
	htmlContent = re.sub(regexPlchldr, plchldr_begin + portfolioChartData[:-3] + plchldr_end, htmlContent)

	#write the output
	htmlFile = open(htmlBalanceFilePath, 'w')
	htmlFile.write(htmlContent)
	htmlFile.close()

def runGuardian():
	counter=0
	counterCycleForBNBUpdate = round (bnbUpdate_loopTimeInMin / guardian_loopTimeInMin)
	counterCycleForBalanceUpdate = round (balanceUpdate_loopTimeInMin / guardian_loopTimeInMin)
	
	while (True):
		time.sleep(guardian_loopTimeInMin * 60)
		traderFunctions.ploggerInfo('GUARDIAN - checking if websocket alive', True)
		
		if ( traderFunctions.checkIfLastTimeOfThisEventWasLately(sharedPrefFileGuardian_lastClbkTime, int(round(guardian_loopTimeInMin*60))) ):
			# confirm that everything OK
			for k, client in clients.items():
				if (k !=  'mno'):
					writeTimeIntoReportHTML(k)
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
							sys.exit()
			if(counter % counterCycleForBalanceUpdate == 0):
				for k, client in clients.items():
					# TODO_future the report now is suitable only for tibRick
					if (k !=  'mno'):
						getAccountsBalance(k)
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
	sys.exit()
runGuardian()
traderFunctions.ploggerErr ('ERROR - THE GUARDIAN HAS STOPPED')
	
