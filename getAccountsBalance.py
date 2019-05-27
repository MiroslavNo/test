import time
import re
import datetime
from collections import Counter

import traderFunctions

from binance.enums import *

######################################################
#############		START LOGGING			##########
######################################################
#musi byt, lebo niektore metody z traderFunctions maju implementovany logging
traderFunctions.startLoggers()

######################################################
#############		GET CLIENT			##############
######################################################
clients = traderFunctions.addClients()

######################################################
######			check for time sync error		 #####
######################################################
traderFunctions.checkTimeSyncErrAndLoop(clients['tibRick'], 13, 300)

######################################################
######		Check if already run today		##########
######################################################
htmlFilePath = traderFunctions.getScriptLocationPath(1) + r'\ReportsAndLogs\report.html'
htmlFile = open(htmlFilePath, 'r')
htmlContent = htmlFile.read()
htmlFile.close()

lastRunDate = htmlContent[9:15]

#######################################################
##############		GET BALANCES		##############
#######################################################
tibRick_BTC = traderFunctions.getAccoutBalances(clients['tibRick'], 'BTC', 0.002, False)
mno_BTC = traderFunctions.getAccoutBalances(clients['mno'], 'BTC', 0.002, False)

detailedBalanceSheets_tibRick=''
detailedBalanceSheets_mno=''
for key in sorted(tibRick_BTC.keys()):
	if (tibRick_BTC.get(key) > 0.01):
		detailedBalanceSheets_tibRick = detailedBalanceSheets_tibRick + ' / ' + key + ':' + str(round(tibRick_BTC.get(key), 2))
for key in sorted(mno_BTC.keys()):
	if (mno_BTC.get(key) > 0.01):
		detailedBalanceSheets_mno = detailedBalanceSheets_mno + ' / ' + key + ':' + str(round(mno_BTC.get(key), 2))

sumBalances = Counter(tibRick_BTC) + Counter(mno_BTC)

total_BTC = float(sumBalances.get('total'))
total_USDT = total_BTC * traderFunctions.getLastPrice(clients['tibRick'], 'BTC', 'USDT')
total_BTC_tibRick = float(tibRick_BTC.get('total'))
total_BNB_mno = float(mno_BTC.get('total')) / traderFunctions.getLastPrice(clients['tibRick'], 'BNB', 'BTC')

#######################################################
##############		CALCULATE THE REST	##############
#######################################################

#calculateInterest
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



#######################################################
##############		FILL HTML		##############
#######################################################

def removeDataFromToday(htmlContent, *plchldrs):
	regexDataFromToday = re.compile("\['" + time.strftime("%d.%m") + "', .*\n")
	htmlContent = re.sub(regexDataFromToday, '', htmlContent)
	return htmlContent

# testing if already run today
if (lastRunDate == time.strftime("%d.%m.")):
	htmlContent = removeDataFromToday(htmlContent)

lineBreak = '\n'

#replace time
timePlchldr_begin = 'LastRun: '
#timePlchldr_end = '</p></b>'
regexTimePlchldr = re.compile("LastRun: .*")
htmlContent = re.sub(regexTimePlchldr, timePlchldr_begin + time.strftime("%d.%m.%Y %H:%M:%S"), htmlContent)

#replace DetailedBalanceSheets
plchldr_begin = 'TibRick Balances: '
regexPlchldr = re.compile(plchldr_begin + ".*")
htmlContent = re.sub(regexPlchldr, plchldr_begin + detailedBalanceSheets_tibRick, htmlContent)
plchldr_begin = 'Mno Balances: '
regexPlchldr = re.compile(plchldr_begin + ".*")
htmlContent = re.sub(regexPlchldr, plchldr_begin + detailedBalanceSheets_mno, htmlContent)

#extend USD chart
plchldr = '//$$DATACHART_USD$$'
htmlContent = htmlContent.replace(plchldr, "['" + time.strftime("%d.%m") + "', " + str(round(total_USDT, -2)) +", "+ str(spoluVlozene_USD) +", "+ str(spoluPozicane_USD) + "]," + lineBreak + plchldr)

#extend BTC chart
plchldr = '//$$DATACHART_BTC$$'
htmlContent = htmlContent.replace(plchldr, "['" + time.strftime("%d.%m") + "', " + str(round(total_BTC, 2)) + "]," + lineBreak + plchldr)

#extend BTC_tibRick chart
plchldr = '//$$DATACHART_BTC_tibRick$$'
htmlContent = htmlContent.replace(plchldr, "['" + time.strftime("%d.%m") + "', " + str(round(total_BTC_tibRick, 2)) + "]," + lineBreak + plchldr)

#extend BNB_mno chart
plchldr = '//$$DATACHART_BNB_mno$$'
htmlContent = htmlContent.replace(plchldr, "['" + time.strftime("%d.%m") + "', " + str(round(total_BNB_mno, 0)) + "]," + lineBreak + plchldr)

#portfolio chart data
portfolioChartData = ''
for key in sorted(sumBalances.keys()):
	if key != 'total':
		portfolioChartData = portfolioChartData + key + "', " + str(round(sumBalances.get(key), 2)) + ", '" + str(int(round(sumBalances.get(key) / sumBalances.get('total') , 2) * 100)) + "%' ],['"

plchldr_begin = "var data_Portfolio = google"
plchldr_end = "]);"
regexPlchldr = re.compile(plchldr_begin + ".*")
plchldr_begin = plchldr_begin + r".visualization.arrayToDataTable([['Element', 'ValInUSD', { role: 'annotation' } ],['"
htmlContent = re.sub(regexPlchldr, plchldr_begin + portfolioChartData[:-3] + plchldr_end, htmlContent)

#write the output
htmlFile = open(htmlFilePath, 'w')
htmlFile.write(htmlContent)
htmlFile.close()


