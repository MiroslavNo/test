#*********************************************#
#******	 EVERY STRATEGY HAS TO HAVE		******#
#*********************************************#
import traderFunctions

# prefix "a_" stands for mandatory variables
# prefix "u_" stands for variables which are updated before the start of the script, but ALSO MANDATORY
# prefix "c_" stands for computed variables - during the strat these are non-existent in the dictionary
# client and strategy have no prefix ( DO NOT put one there, because you would need to edit the runner as well)
# TODO_future a_maxLoss a a_cumulLoss_limit sprav ako nasobky a_sensitivity, lebo su od nej vlastne zavilste (zmen aj prefix na u_). V startovacom JSONe maj ale zu vypocitane hodnoty, aby si nespomaloval skript zbytocne
mandatoryInitVars = {
	"strategy": "NEVYPLNAS, bere automaticky z nazvu suboru",
	"client": "NEVYPLNAS, bere automaticky z nazvu suboru",
	"a_symbol": "BTCUSDT",
	"a_sensitivity": "float - percentualna hodnota v absolutnom cisle, ktora musi byt prekrocena, aby po zmene pozicie zacal uvazovat nad tym, ze zmeni poziciu zas (hodnota hovori ze sme dosiahli prvy climax od zmeny pozicie) - POUZIVAS AJ AKO PERCENTUALNU HODNOTU PRE DALSI STUPEN LADDERU. Hodnota ma tvar 0.005",
	"a_maxLoss": "float - percentualna hodnota v absolutnom cisle, ktora ked je dosiahnuta, tak sa rozhodne prejst na druhu stranu napriek tomu ze je v strate - pouziva sa iba v smere coin to defCoin",
	"a_cumulLoss_limit": "float - !! NEGATIVNA !! percentualna hodnota v absolutnom cisle (napr. -0.03), ktora ked je prekrocena, pri lTwaitToSell, tak vymaze entry - je to myslene ako maximalny loss na entry, a tento sa statva len ked je prekroceny lT v statuse wait to sell"
	}

#*********************************************#
#******	 			CONSTANTS			******#
#*********************************************#

A_SYMBOL = 'a_symbol'
A_SENSITIVITY = 'a_sensitivity'
A_MAX_LOSS = 'a_maxLoss'
A_CUMUL_LOSS_LIMIT = 'a_cumulLoss_limit'

# U_ means that it the variable updated before skript start, but is also mandatory for the start
U_SINGLE_ENTRY_AMOUNTS = 'u_singleEntryAmounts'
U_PRICE_QTY_REQS = 'u_PriceQtyReqs'

C_LADDER_NEXT_PRICE = 'c_ladderNextPrice'
C_LADDER_HIGHEST_REACHED_STEP = 'c_ladderHighestReachedStep'
C_LADDER_BOTTOM_BOUNDARY = 'c_ladderBottomBoundary'
C_UTS_SORTED_ASC = 'c_uTs_asc'
C_LTS_SORTED_DESC = 'c_lTs_desc'

# E_ means that it as a constant of an entry dictionary
ENTRIES = 'entries'
E_TYP = 'typ'
E_QTY = 'qty'
E_LAST_XCHANGE_PRICE = 'lastXchangePrice'
E_UPPER_TRESHOLD = 'uT'
E_LOWER_TRESHOLD = 'lT'
E_CUMUL_LOSS = 'cumulLoss'

# the following are directions as well the desired directions for calculateExchangePrice
WAIT_TO_SELL = 'waitToSell'
WAIT_TO_BUY = 'waitToBuy'
LIMIT_SELL = 'limitSell'
LIMIT_BUY = 'limitBuy'

# order response constants
STATUS = 'status'
EXEC_QTY = 'executedQty'
CUMUL_QTY = 'cummulativeQuoteQty'

# function names for the debug protocoll
UT_LIMIT_BUY = 'uTlimitBuy' 
UT_LIMIT_SELL = 'uTlimitSell'
UT_WAITTO_SELL = 'uTwaitToSell'
LT_LIMIT_BUY = 'lTlimitBuy'
LT_LIMIT_SELL = 'lTlimitSell'
LT_WAITTO_BUY = 'lTwaitToBuy'
LT_WAITTO_SELL = 'lTwaitToSell'

# OTHER CONSTANTS
# cislo, ktore je prilis vysoke na to aby bolo dosiahnute, pouzivane pri UT pre waitToBuy
i_OUTOFRANGE = 1000000
STEP_NR = 'step'

DEBUG = True


def trade(client, jD, pricesFromTicker):

	# key stands for the name of the json
	# jD stands for jsonDictionary
	price = pricesFromTicker.get(jD[A_SYMBOL], 0)

	if (price==0):
		return None
	
	############## ZACIATOK SPAWNERA ##############
	
	# TODO_future skus prerobit na limit order s rezevervou (rozdielom medzi trigger a cena) - ten by vedel rychlejsie reagovat a mal by "poistku" ze nekupi prilis draho
	# spawner comes as first!
	if (price >= jD[C_LADDER_NEXT_PRICE]):
		# 1A, ked sa dany market startuje, tak bol C_LADDER_NEXT_PRICE nastaveny na aktualnu cenu + krok. C_LADDER_HIGHEST_REACHED_STEP je nastaveny na 0, resp. na -1 ak som uz vstupil ale mi to nevyslo - musel byt entry vymazany
		# 1B, ked je dany market uz nastartovany, tak pokracuje tak je to posledna (najvyssia) cena za ktoru som kupoval
		# - v oboch pripadoch, ked je cena dosiahnuta, vytvorim market order
		if DEBUG:
			traderFunctions.ploggerInfo(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + C_LADDER_NEXT_PRICE + '=' + str(jD[C_LADDER_NEXT_PRICE]) + ' was reached')
		return createMarketOrderForNewLadderEntry( client, jD, price )
		
	if (jD[C_LADDER_HIGHEST_REACHED_STEP] <= 0 and price < jD[C_LADDER_BOTTOM_BOUNDARY]):
		# ked je to cisto novy init
		if(jD[C_LADDER_HIGHEST_REACHED_STEP] == 0):
			# ked je to cisto novy init, tak posuvam hornu hranicu (A_SENSITIVITY) dole a vstupujem iba cez nu
			nextPriceLevel_moved = price * (1 + jD[A_SENSITIVITY] + jD[A_MAX_LOSS])
			if DEBUG:
				traderFunctions.ploggerInfo(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + C_LADDER_BOTTOM_BOUNDARY + '=' + str(jD[C_LADDER_BOTTOM_BOUNDARY]) + ' cena bola podlezena, kedze C_LADDER_HIGHEST_REACHED_STEP=0, ak iba nastavujem novy C_LADDER_NEXT_PRICE a C_LADDER_BOTTOM_BOUNDARY')
			jD[C_LADDER_NEXT_PRICE] = nextPriceLevel_moved + ((jD[C_LADDER_NEXT_PRICE] - nextPriceLevel_moved ) / 2)
			jD[C_LADDER_BOTTOM_BOUNDARY] = price
			if DEBUG:
				traderFunctions.ploggerInfo(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' this is the whole jD:\n' + traderFunctions.formatDictForPrint(jD))
			return jD
		# ked je to opakovany init, tak vstupujem aj cez spodnu hranicu, HORNA HRANICA OSTAVA AKO PREDTYM
		# nie je to sice sofistikovane, ale teoreticky, v pripade extremneho padu marketu, napr 50perc, by som tu spravil tych 25perc a pri najnizsej sume je pre vsetky coiny asi 2perc * 0,25 -> takze to necham asi tak ako to je
		elif(jD[C_LADDER_HIGHEST_REACHED_STEP] == -1):
			# POZN: skusal som radsej spravit jD update, ale kedze entries je nested, tak nevime update-nut aj nenestnute aj nestnute data v jednom kroku
			if DEBUG:
				traderFunctions.ploggerInfo(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + C_LADDER_BOTTOM_BOUNDARY + '=' + str(jD[C_LADDER_BOTTOM_BOUNDARY]) + ' cena bola podlezena, kedze C_LADDER_HIGHEST_REACHED_STEP=-1, vytvorim novy init ladder order')
			return createMarketOrderForNewLadderEntry( client, jD, price )
					
	############## KONIEC SPAWNERA ##############
	
	tmp = {}
	tmp_del = []

	list_uTs_sortAsc = jD[C_UTS_SORTED_ASC]
	list_lTs_sortDesc = jD[C_LTS_SORTED_DESC]
	
	# TODO_future pri niektorych fciach by si teoreticky nepotreboval if not (r is None):, lebo oni vzdy vracaju nieco, treba ale preverit casom, ked si budem isty a nebudem zabudovavat napr return None
	for i in range(len(list_uTs_sortAsc)):
		if (price > list_uTs_sortAsc[i][E_UPPER_TRESHOLD]):
			strLadderStep = str(list_uTs_sortAsc[i][STEP_NR])
			stepDic = jD[ENTRIES].get(strLadderStep, {E_TYP: None})
			if (stepDic[E_TYP]==LIMIT_BUY):
				if DEBUG:
					protocollFcionRun(UT_LIMIT_BUY, strLadderStep)
				r = uTlimitBuy(client, price, strLadderStep, stepDic, jD[U_PRICE_QTY_REQS], jD[A_SYMBOL], jD[A_SENSITIVITY], jD[A_MAX_LOSS])
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_TYP]==LIMIT_SELL):
				if DEBUG:
					protocollFcionRun(UT_LIMIT_SELL, strLadderStep)
				r = uTlimitSell(price, stepDic)
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_TYP]==WAIT_TO_SELL):
				if DEBUG:
					protocollFcionRun(UT_WAITTO_SELL, strLadderStep)
				r = uTwaitToSell(price, stepDic)
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_TYP] is None):
				traderFunctions.ploggerErr(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' the ladderStep Nr. ' + strLadderStep + ' from list_uTs_sortAsc could not be found in the jD[entries] dictionary - there must be a discrepancy in the data!')
			else:
				traderFunctions.ploggerErr(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' for the ladderStep Nr. ' + strLadderStep + ' was an unexpected ' + E_TYP + ' found: "' + stepDic[E_TYP] + '" - this was not expecpected!')
		else:
			break
			
	for j in range(len(list_lTs_sortDesc)):
		if (price < list_lTs_sortDesc[j][E_LOWER_TRESHOLD]):
			strLadderStep = str(list_lTs_sortDesc[j][STEP_NR])
			stepDic = jD[ENTRIES].get(strLadderStep, {E_TYP: None})
			if (stepDic[E_TYP]==LIMIT_BUY):
				if DEBUG:
					protocollFcionRun(LT_LIMIT_BUY, strLadderStep)
				r = lTlimitBuy(price, stepDic)
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_TYP]==LIMIT_SELL):
				if DEBUG:
					protocollFcionRun(LT_LIMIT_SELL, strLadderStep)
				r = lTlimitSell(client, price, strLadderStep, stepDic, jD[U_PRICE_QTY_REQS], jD[A_SYMBOL], jD[A_SENSITIVITY])
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_TYP]==WAIT_TO_BUY):
				if DEBUG:
					protocollFcionRun(LT_WAITTO_BUY, strLadderStep)
				r = lTwaitToBuy(price, stepDic)
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_TYP]==WAIT_TO_SELL):
				if DEBUG:
					protocollFcionRun(LT_WAITTO_SELL, strLadderStep)
				r = lTwaitToSell(client, price, strLadderStep, stepDic, jD[U_PRICE_QTY_REQS], jD[A_SYMBOL], jD[A_CUMUL_LOSS_LIMIT], jD[A_SENSITIVITY])
				if not (r is None):
					# the above if condition means that something happend
					if bool(r):
						# the above if condition was fulfilled -> a regular result with data was returned
						tmp[strLadderStep] = r
					else:
						# the above if condition was not fulfilled -> means that the result dic is empty -> THIS ENTRY IS TO BE DELETED
						tmp_del.append(strLadderStep)
						# adding the stepDic to tmp, so it will be recognized, that a change hapend -> adding the same value so it wont change anything
						tmp[strLadderStep] = stepDic
			elif (stepDic[E_TYP] is None):
				traderFunctions.ploggerErr(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' the ladderStep Nr. ' + strLadderStep + ' from list_lTs_sortDesc could not be found in the jD[entries] dictionary - there must be a discrepancy in the data!')
			else:
				traderFunctions.ploggerErr(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' for the ladderStep Nr. ' + strLadderStep + ' was an unexpected ' + E_TYP + ' found: "' + stepDic[E_TYP] + '" - this was not expecpected!')
		else:
			break

	
	if bool(tmp):
		jD[ENTRIES].update(tmp)
		jD.update(updateSortedListsOfTresholds(jD))

		for i in range(len(tmp_del)):
			# the pop method removes an entry and the second arg is the default return val if entry not found - otherwise it returns the removed entry
			removedEntry = jD["entries"].pop(tmp_del[i], None)
			if(removedEntry is None):
				traderFunctions.ploggerErr(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + 'Tried to pop(remove) the entry with the STEP_NR:' + str(tmp_del[i]) + '(the value is of the type: ' + type(tmp_del[i]) + ') but received an error, that it wasnt found in the jD')
			# check if any entries left
			if(len(jD["entries"].keys()) == 0):
				traderFunctions.ploggerInfo(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + 'ALL ENTRIES HAS BEEN DELETED, setting the ' + C_LADDER_HIGHEST_REACHED_STEP + ' to -1' )
				jD[C_LADDER_HIGHEST_REACHED_STEP] = -1
				# pri vymaze entry by mala byt nastavena spodna hranica na sumu znizenu o celkove percento ktore som prerobil
				# POZOR E_CUMUL_LOSS je zaporna hodnota, preto tam je 1.0 +
				jD[C_LADDER_BOTTOM_BOUNDARY] = price * ( 1.0 + (removedEntry.get(E_CUMUL_LOSS, (-2 * jD[A_MAX_LOSS]))))
				# jD[C_LADDER_NEXT_PRICE] ostava tak isto ako bolo, lebo ked som prerobil na tom useku, tak tamuz nebudem vstupovat skor
		
		if DEBUG:
			traderFunctions.ploggerInfo(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' the price which triggered the changes above and the folllowing jD was: ' + str(price))
			traderFunctions.ploggerInfo(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' this is the whole jD:\n' + traderFunctions.formatDictForPrint(jD))
		return jD
	
	else:
		return None


def uTlimitBuy(client, currPrice, strLadderStep, stepDic, priceQtyReqs, tradedSymbol, sensitivity, maxLoss):
	# cena za ktoru si chcel kupit - ak prekrocena, vytvoris market buy
	calcQty = traderFunctions.validQty(priceQtyReqs, currPrice, stepDic[E_QTY])
	marketOrderStats = client.order_market_buy(symbol=tradedSymbol, quantity=calcQty)
	if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
		fillQty = float(marketOrderStats[EXEC_QTY])
		fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		# calc gain (result is inkl. fees)
		gain = calcGain(stepDic[E_LAST_XCHANGE_PRICE], fillPrice, LIMIT_BUY )
		# calc market order difference (result is inkl. fees)
		diff_TriggPriceVsExecPrice = calcGain(currPrice, fillPrice, LIMIT_BUY )
		# calc the cumulLosses
		cumulLoss = stepDic[E_CUMUL_LOSS] + gain
		if (cumulLoss > 0.0):
			cumulLoss = 0.0
		
		traderFunctions.ploggerTrades(tradedSymbol, strLadderStep, LIMIT_BUY, fillPrice, diff_TriggPriceVsExecPrice, gain, fillQty)
		
		# update stepDic, goig to be a waitToSell
		stepDic[E_TYP] = WAIT_TO_SELL
		stepDic[E_LAST_XCHANGE_PRICE] = fillPrice
		stepDic[E_QTY] = fillQty
		stepDic[E_CUMUL_LOSS] = cumulLoss
		# calculate the uT and lT for the new waitToSell entry
		# upper treshold bude avgExchangePrice + sensitivity, ked je prekrocena, vytvori limitSell
		stepDic[E_UPPER_TRESHOLD] = fillPrice * (1.0 + sensitivity)
		# lower treshold bude avgExchangePrice minus maxLoss kde bude cakat stopLimitOrder na predaj so stratou
		stepDic[E_LOWER_TRESHOLD] = fillPrice * (1.0 - maxLoss)
	else:
		traderFunctions.ploggerErr(__name__ + ' / ' + tradedSymbol +  ' - ' + ' unexpected situation, the market order from uTlimitBuy had a different status then ' + client.ORDER_STATUS_FILLED + '. Here is the whole response:\n' + marketOrderStats)
		return None

	return stepDic


def uTlimitSell(currPrice, stepDic):
	# toto je hodnota climaxu, ked je prekrocena, tak prepocitas cenu za ktoru chces predat'
	stepDic[E_UPPER_TRESHOLD] = float(currPrice)
	# zaokruhlenie podla pravidiel na minPrice atd je potom ked vytvaras order, aby si optimalizoval pocetnost
	stepDic[E_LOWER_TRESHOLD] = calculateExchangePrice(float(stepDic[E_LAST_XCHANGE_PRICE]), currPrice, LIMIT_SELL)
	return stepDic

def uTwaitToBuy(currPrice, stepDic):
	traderFunctions.ploggerErr(__name__ + ' / ' +  ' - ' + 'code was not supposed to come to uTwaitToBuy')
	# nerobis minusovy obchod v tomto smere (defCoin to Coin), to znamena, ze ta nezaujima upperTreshold ked cakas na kupu, jedina moznost na ozivenie je ked cena klesne pod exchangePrice minus sensitivity
	# tato funkcia NIE JE VOLANA, je tu iba ako POZNAMKA
	# TODO_future, mohol by si v buducnosti spravi nejake pocitadlo, na tento pripade (mimo sensitivity area), aby si vedel kolko dead orderov mas
	return None

def uTwaitToSell(currPrice, stepDic):
	# hodnota avgExchangePrice + sensitivity, bola prekrocena, takze vytvoris limitSell
	stepDic[E_TYP] = LIMIT_SELL
	# nove lT, uT
	stepDic[E_UPPER_TRESHOLD] = currPrice
	# uT, bude polovica medzi tym co si predal a terajsou cenou
	stepDic[E_LOWER_TRESHOLD] = calculateExchangePrice(float(stepDic[E_LAST_XCHANGE_PRICE]), currPrice, LIMIT_SELL)
	# POZN: v calculateExchangePrice keby sa dostal prvy argument ako None, tak chcem aby to crashlo, lebo to potom znamena, ze mam niekde nezrovnalosti
	
	return stepDic

def lTlimitBuy(currPrice, stepDic):
	# - je to climax, po ktoreho prekroceni vyratas novu hodnotu limit orderu
	stepDic[E_LOWER_TRESHOLD] = float(currPrice)
	# zaokruhlenie podla pravidiel na minPrice atd je potom ked vytvaras order, aby si optimalizoval pocetnost
	stepDic[E_UPPER_TRESHOLD] = calculateExchangePrice(float(stepDic[E_LAST_XCHANGE_PRICE]), currPrice, LIMIT_BUY)
	
	return stepDic

def lTlimitSell(client, currPrice, strLadderStep, stepDic, priceQtyReqs, tradedSymbol, sensitivity):
	# cena za ktoru si chcel predat - ak prekrocena, vytvoris market sell
	calcQty = traderFunctions.validQty(priceQtyReqs, currPrice, stepDic[E_QTY])
	marketOrderStats = client.order_market_sell(symbol=tradedSymbol, quantity=calcQty)
	if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
		fillQty = float(marketOrderStats[EXEC_QTY])
		fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		# calc gain (result is inkl. fees)
		gain = calcGain(stepDic[E_LAST_XCHANGE_PRICE], fillPrice, LIMIT_SELL )
		# calc market order difference (result is inkl. fees)
		diff_TriggPriceVsExecPrice = calcGain(currPrice, fillPrice, LIMIT_SELL )
		# calc the cumulLosses
		cumulLoss = stepDic[E_CUMUL_LOSS] + gain
		if (cumulLoss > 0.0):
			cumulLoss = 0.0
		
		traderFunctions.ploggerTrades(tradedSymbol, strLadderStep, LIMIT_SELL, fillPrice, diff_TriggPriceVsExecPrice, gain, fillQty)
		
		# update stepDic, going to be a waitToBuy
		stepDic[E_TYP] = WAIT_TO_BUY
		stepDic[E_LAST_XCHANGE_PRICE] = fillPrice
		stepDic[E_QTY] = fillQty
		stepDic[E_CUMUL_LOSS] = cumulLoss
		# calculate the uT and lT for the new waitToBuy entry
		# upper treshold bude i_OUTOFRANGE kedze nikdy nechem aby som robil minusovy obchod
		stepDic[E_UPPER_TRESHOLD] = i_OUTOFRANGE
		# lower treshold bude avgExchangePrice minus sensitivity
		stepDic[E_LOWER_TRESHOLD] = fillPrice * (1.0 - sensitivity)
	else:
		traderFunctions.ploggerErr(__name__ + ' / ' + tradedSymbol +  ' - ' + ' unexpected situation, the market order from uTlimitBuy had a different status then ' + client.ORDER_STATUS_FILLED + '. Here is the whole response:\n' + marketOrderStats)
		return None

	return stepDic	


def lTwaitToBuy(currPrice, stepDic):
	# hodnota avgExchangePrice minus sensitivity, ked je prekrocena, vytvoris limitBuy
	stepDic[E_TYP] = LIMIT_BUY
	# nove lT, uT
	stepDic[E_LOWER_TRESHOLD] = currPrice
	# uT, bude polovica medzi tym co si predal a terajsou cenou
	stepDic[E_UPPER_TRESHOLD] = calculateExchangePrice(float(stepDic[E_LAST_XCHANGE_PRICE]), currPrice, LIMIT_BUY)
	
	return stepDic

def lTwaitToSell(client, currPrice, strLadderStep, stepDic, priceQtyReqs, tradedSymbol, cumulLossLimit, sensitivity):
	# dosiahol si cenu ktora je ako keby taky stop loss po tom ako si vstupil do lTwaitToSell
	calcQty = traderFunctions.validQty(priceQtyReqs, currPrice, stepDic[E_QTY])
	marketOrderStats = client.order_market_sell(symbol=tradedSymbol, quantity=calcQty)
	if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
		fillQty = float(marketOrderStats[EXEC_QTY])
		fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		# calc gain (result is inkl. fees)
		gain = calcGain(stepDic[E_LAST_XCHANGE_PRICE], fillPrice, WAIT_TO_SELL )
		# calc market order difference (result is inkl. fees)
		diff_TriggPriceVsExecPrice = calcGain(currPrice, fillPrice, WAIT_TO_SELL )
		# calc the cumulLosses
		cumulLoss = stepDic[E_CUMUL_LOSS] + gain
		
		# pozn: the cumulLosses are negative numbers
		if( cumulLoss < cumulLossLimit ):
			# delete this entry - because of the absence ofthe kStepNr here, the log will be on the for loop
			traderFunctions.ploggerInfo(__name__ + ' / ' + tradedSymbol +  ' - ' + 'The STEP_NR: ' + strLadderStep + ' will be deleted, cumulLoss(' + str(cumulLoss) + ') is higher than cumulLossLimit(' + str(cumulLossLimit) + ')')
			traderFunctions.ploggerTrades(tradedSymbol, strLadderStep, 'EXIT-' + WAIT_TO_SELL, fillPrice, diff_TriggPriceVsExecPrice, gain, fillQty)
			return {}
		else:	
			traderFunctions.ploggerTrades(tradedSymbol, strLadderStep, WAIT_TO_SELL, fillPrice, diff_TriggPriceVsExecPrice, gain, fillQty)
			if (cumulLoss > 0.0):
				cumulLoss = 0.0
			
			# update stepDic, going to be a waitToBuy
			stepDic[E_TYP] = WAIT_TO_BUY
			stepDic[E_LAST_XCHANGE_PRICE] = fillPrice
			stepDic[E_QTY] = fillQty
			stepDic[E_CUMUL_LOSS]= cumulLoss
			# calculate the uT and lT for the new waitToBuy entry
			# upper treshold bude i_OUTOFRANGE kedze nikdy nechem aby som robil minusovy obchod
			stepDic[E_UPPER_TRESHOLD] = i_OUTOFRANGE
			# lower treshold by za normalnych okolnosti bol avgExchangePrice minus sensitivity, ale tu som sa rozhodol daj predchadzajucu stratu, ak je vacsia ako sensitivity
			stepDic[E_LOWER_TRESHOLD] = fillPrice * (1.0 - max(sensitivity, abs(gain)))
	else:
		traderFunctions.ploggerErr(__name__ + ' / ' + tradedSymbol +  ' - ' + ' unexpected situation, the market order from uTlimitBuy had a different status then ' + client.ORDER_STATUS_FILLED + '. Here is the whole response:\n' + marketOrderStats)
		return None

	return stepDic


def getAmountForNewLadderStep(amountsDic, stepNo):
	highestAppliableStep_helper = i_OUTOFRANGE
	highestAmount = 0
	result = 0
	
	for stepLimit, amount in amountsDic.items():
		if( highestAmount < amount):
			highestAmount = amount
		if ( (stepNo <= int(stepLimit)) and (int(stepLimit) < highestAppliableStep_helper) ):
			result = amount
			highestAppliableStep_helper = int(stepLimit)
	
	if (result == 0):
		result = highestAmount
	
	return result		

def createMarketOrderForNewLadderEntry( client, jD, priceFromTicker ):
	ladderHighestReachedStep = jD[C_LADDER_HIGHEST_REACHED_STEP] + 1
	# correction because of the possible value -1 in C_LADDER_HIGHEST_REACHED_STEP
	if ( ladderHighestReachedStep < 1):
		ladderHighestReachedStep = 1
	
	# get Qty - step 1 (get USDT amount from U_SINGLE_ENTRY_AMOUNTS)
	calcQty = getAmountForNewLadderStep(jD[U_SINGLE_ENTRY_AMOUNTS], ladderHighestReachedStep)
	traderFunctions.ploggerInfo(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' Creating the new ladder entry nr: ' + str(ladderHighestReachedStep) + ' - single entry amount in USDT is: ' + str(calcQty))
	# get Qty - step 2 (convert the USDT to coin amount based on the price from the ticker)
	calcQty = calcQty / priceFromTicker
	# get Qty - step 3 (run the calculated Qty throught the Qty validator)
	calcQty = traderFunctions.validQty(jD[U_PRICE_QTY_REQS], priceFromTicker, calcQty)		
	
	marketOrderStats = client.order_market_buy(symbol=jD[A_SYMBOL], quantity=calcQty)
	if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
		fillQty = float(marketOrderStats[EXEC_QTY])
		fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		# update dics
		jD[C_LADDER_HIGHEST_REACHED_STEP] = ladderHighestReachedStep	
		jD[C_LADDER_NEXT_PRICE] = fillPrice * (1.0 + jD[A_SENSITIVITY])
		jD[ENTRIES][str(ladderHighestReachedStep)] = {E_TYP: WAIT_TO_SELL,
														E_QTY: fillQty,
														E_LAST_XCHANGE_PRICE: fillPrice,
														E_UPPER_TRESHOLD: fillPrice * (1.0 + jD[A_SENSITIVITY]),
														E_LOWER_TRESHOLD: fillPrice * (1.0 - jD[A_MAX_LOSS]),
														E_CUMUL_LOSS: 0.0
													}
		traderFunctions.ploggerTrades(jD[A_SYMBOL], ladderHighestReachedStep, 'NEW_ENTRY', fillPrice, 0, 0, fillQty)
		jD.update(updateSortedListsOfTresholds(jD))
	else:
		traderFunctions.ploggerErr(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' unexpected situation, the market order had a different status then ' + client.ORDER_STATUS_FILLED + '. Here is the whole response:\n' + marketOrderStats)
		return None
	
	if DEBUG:
		traderFunctions.ploggerInfo(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' this is the whole jD:\n' + traderFunctions.formatDictForPrint(jD))
	
	return jD

	
def updateSortedListsOfTresholds(jD):
	entries = jD.get(ENTRIES, {})
	if not bool(entries):
		traderFunctions.ploggerErr(__name__ + ' / ' + jD[A_SYMBOL] +  ' - ' + ' THIS WAS NOT SUPPOSED TO HAPPEN - no dictionary for entries found. Here is the whole jD:\n' + jD)
		return jD
	
	list_to_be_sorted = list()
	for ladderStep, ladderStepDic in entries.items():
		# TODO_future the C_UTS_SORTED_ASC could have only the uTs, and C_LTS_SORTED_DESC only lTs. Also maybe lists instead of dics would be faster
		list_to_be_sorted.append({STEP_NR: ladderStep, E_LOWER_TRESHOLD: ladderStepDic[E_LOWER_TRESHOLD], E_UPPER_TRESHOLD: ladderStepDic[E_UPPER_TRESHOLD]})

	return{C_UTS_SORTED_ASC: sorted(list_to_be_sorted, key=lambda k: k[E_UPPER_TRESHOLD]),	C_LTS_SORTED_DESC: sorted(list_to_be_sorted, key=lambda k: k[E_LOWER_TRESHOLD], reverse=True)}
	

def calculateExchangePrice(lastXchangePrice, newPriceClimax, desiredDirection, startingTargetRatio=0.5, maxTargetRatio=0.8):
	# startingTargetRatio = inicialna hodnota pomeru s ktorym zacne pocitat ked dosiahne minimalny posun v cene
	# maxTargetRatio = maximal target ratio value
	
	if (desiredDirection == LIMIT_BUY):
		if (lastXchangePrice > newPriceClimax):
			#((3000 - 2000) / 2000) / 2 + 0,5
			newTargetRatio = ((lastXchangePrice - newPriceClimax) / newPriceClimax) / 2 + startingTargetRatio
		else:
			newTargetRatio = startingTargetRatio
			# we are on the wrong side - using 1.004 as the half of it is 0.2 % and that is the minimum trade diff which is making profit
			traderFunctions.ploggerWarn(__name__ + 'In the function calculateExchangePrice the lastXchangePrice="' + str(lastXchangePrice) + '" was smaller then newPriceClimax="' + str(newPriceClimax) + '" for the direction ' + desiredDirection + '. This was not expected, please investigate', False)
			newPriceClimax = lastXchangePrice * 1.004
		if (newTargetRatio > maxTargetRatio):
			newTargetRatio = maxTargetRatio
		newTargetPrice = lastXchangePrice - ((lastXchangePrice - newPriceClimax) * newTargetRatio)
		
	if (desiredDirection == LIMIT_SELL):
		if (lastXchangePrice < newPriceClimax):
			# ((4000 - 3000) / 3000) / 2 + 0,5
			newTargetRatio = ((newPriceClimax - lastXchangePrice) / lastXchangePrice) / 2 + startingTargetRatio
		else:
			newTargetRatio = startingTargetRatio
			# we are on the wrong side - using 0.996 as the half of it is 0.2 % and that is the minimum trade diff which is making profit
			traderFunctions.ploggerWarn(__name__ + 'In the function calculateExchangePrice the newPriceClimax="' + str(newPriceClimax) + '" was smaller then lastXchangePrice="' + str(lastXchangePrice) + '" for the direction ' + desiredDirection + '. This was not expected, please investigate', False)
			newPriceClimax = lastXchangePrice * 0.996
		if (newTargetRatio > maxTargetRatio):
			newTargetRatio = maxTargetRatio
		newTargetPrice = ((newPriceClimax - lastXchangePrice) * newTargetRatio) + lastXchangePrice
	
	return newTargetPrice

def calcGain(previousAvgXchange, currAvgXchange, direction ):
	"""
		the order dependency of previousAvgXchange / currAvgXchange in relation to the direction has been tested
	"""
	if((direction == LIMIT_BUY) or (direction == WAIT_TO_BUY)):
		return round(((previousAvgXchange / currAvgXchange) - 1), 4)
	elif((direction == LIMIT_SELL) or (direction == WAIT_TO_SELL)):
		return round(((currAvgXchange / previousAvgXchange) - 1), 4)
	else:
		traderFunctions.ploggerErr(__name__ + ' - ' + 'Unexpected direction in the fction calcCumulLoss: ' + direction)
		return 0

def protocollFcionRun(fname, strStepNr):
	# for debug purposes
	# can see which functions run, and the jD before and after (so the values as well) - this should be enough for investigation
	traderFunctions.ploggerInfo(__name__ + '.' + fname + ' called for the stepNr ' + strStepNr +', whole jD will follow')
	

# without u_ vars - would require the client 
# and without strategy and client var, those get filled on the stratup of the trade runner
def startNewMarket(clientName, client, market, scriptLocationPath, mandatoryParamsFromJsonKey=None, currPrice=None, ):
	"""
		scriptLocationPath - is only the math to the script, not to the folder jsonTriggerFiles where the json will be stored - the dumpGlobalVariablesToJson takes care of that
	"""
	traderFunctions.ploggerInfo(__name__ + ' - Starting a new market: ' + market)
	from pathlib import Path
		
	strategyName = str(__name__).split('.')[-1:][0]
	resultJsonFileName = '{}_{}_{}'.format(strategyName, market, clientName)
	
	if Path(scriptLocationPath + r'\jsonTriggerFiles\\' + resultJsonFileName + '.json').is_file():
		traderFunctions.ploggerErr(__name__ + '.startNewMarket - was supposed to create a starting trigger json with the path {} but detected that it already exists - ABORTING this creation'.format(scriptLocationPath + r'\jsonTriggerFiles\\' + resultJsonFileName + '.json'))
		return None

	sharedPrefFileName = "pumpTheRightCoin_mandatoryParams_marketSpecific.json"
	
	# if not specified that it should be eg. NEW_MARKET, searching for the key with name of the market - should it not be found, will take the default vals 
	if mandatoryParamsFromJsonKey is None:
		mandatoryParamsFromJsonKey = market
	
	r = traderFunctions.getValFromSharedPrefFile(sharedPrefFileName, mandatoryParamsFromJsonKey)
	if r is None:
		# taking the default value
		r = traderFunctions.getValFromSharedPrefFile(sharedPrefFileName, 'default')
		if r is None:
			traderFunctions.ploggerErr(__name__ + ' - ' + 'nor the default or a specific params were found in the shared pref file: ' + sharedPrefFileName)
			return None

	if currPrice is None:
		currPrice = traderFunctions.getLastPrice(client, market)
	
	r[A_SYMBOL] = market
	
	r[C_LADDER_NEXT_PRICE] = currPrice * ( 1.0 + r[A_SENSITIVITY] )
	r[C_LADDER_BOTTOM_BOUNDARY] = currPrice * ( 1.0 - r[A_MAX_LOSS] )
	r[C_LADDER_HIGHEST_REACHED_STEP] = 0
	
	# get price reqs
	r[U_PRICE_QTY_REQS] = (traderFunctions.getPriceAndQtyReqs(market, client))
	# get single entry amounts
	r[U_SINGLE_ENTRY_AMOUNTS] = (traderFunctions.getValFromSharedPrefFile(U_SINGLE_ENTRY_AMOUNTS + '_' + clientName + '.json', U_SINGLE_ENTRY_AMOUNTS))
	r[ENTRIES]={}
	r[C_UTS_SORTED_ASC]=[]
	r[C_LTS_SORTED_DESC]=[]
	
	r['strategy'] = strategyName
	r['client'] = clientName
	
	traderFunctions.dumpGlobalVariablesToJson(resultJsonFileName, r, scriptLocationPath)
	
	return r


# TODO_future, najprv by som chcel vidiet ako spravaju jednotlive entries a okrem toho to nie je MVP
def mergeAndDeleteEntries(jD):
	pass
