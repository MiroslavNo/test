import traderFunctions
import time
import re
import socket
import os

sharedPrefFileGuardian = 'guardian_lastClbkTime'
fileWithLoopTimesForGuardian = 'guardian_loopTimeInMin.json'
guardian_loopTimeInMin = (traderFunctions.getValFromSharedPrefFile(fileWithLoopTimesForGuardian, 'guardian_loopTimeInMin'))
bnbUpdate_loopTimeInMin = (traderFunctions.getValFromSharedPrefFile(fileWithLoopTimesForGuardian, 'bnbUpdate_loopTimeInMin'))
balanceUpdate_loopTimeInMin = (traderFunctions.getValFromSharedPrefFile(fileWithLoopTimesForGuardian, 'balanceUpdate_loopTimeInMin'))


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
				# TODO
				# starting as a separate process in case the guardian should be stopped manually
				# os.system('ensureBNBforFees.py')
				pass
			if(counter % counterCycleForBalanceUpdate == 0):
				# starting as a separate process in case the guardian should be stopped manually
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
					try:
						traderFunctions.ploggerErr (errMsgToBeSent)
					except:
						pass
						
					while (True):
						time.sleep(sleepTimeInMin * 60)
						if ( hasInternet ):
							os.system('"' + restartBatPath + '"')
							break


# TODO_future daj sleepTimeInMin do sharedPrefFile-u aby si to aj runner mohol odtail stiahnut

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

runGuardian(sharedPrefFileGuardian, guardian_loopTimeInMin)
traderFunctions.ploggerErr ('ERROR - THE GUARDIAN HAS STOPPED')
	
