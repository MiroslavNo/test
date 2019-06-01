#*********************************************#
#******	 EVERY STRATEGY HAS TO HAVE		******#
#*********************************************#
import traderFunctions
import traceback

# prefix "a_" stands for mandatory variables
# prefix "c_" stands for computed variables - during the strat these are non-existent in the dictionary
# prefix "u_" stands for variables which are updated before the start of the script, for example minQty
# client and strategy have no prefix ( DO NOT put one there, because you would need to edit the runner as well)
mandatoryInitVars = {
	"strategy": "NEVYPLNAS, bere automaticky z nazvu suboru",
	"client": "NEVYPLNAS, bere automaticky z nazvu suboru",
	"a_tradedSymbol": "BTCUSDT",
	"a_sensitivityForMinimalPriceChange": "percentualna hodnota v absolutnom cisle, ktora musi byt prekrocena, aby po zmene pozicie zacal uvazovat nad tym, ze zmeni poziciu zas (hodnota hovori ze sme dosiahli prvy climax od zmeny pozicie) - POUZIVAS AJ AKO PERCENTUALNU HODNOTU PRE DALSI STUPEN LADDERU. Hodnota ma tvar 0.005",
	"a_maxLoss": "percentualna hodnota v absolutnom cisle, ktora ked je dosiahnuta, tak sa rozhodne prejst na druhu stranu napriek tomu ze je v strate - pouziva sa iba v smere coin to defCoin",
	"c_ladderNextPriceLevel": "cena, ktora reprezentuje dalsi stupen na ladderi - pri starte noveho marketu sa nastavi na aktualnu cenu + krok",
	"c_ladderHighestReachedStep": "int value, nr. of steps which have been reached on the ladder. An init market has the value 0, a market where I entered but exited and deleted the entry has the value -1",
	"c_ladderBottomBoundary": "cena, ktora je pouzita pre ucely startovania marketu, ked je podlezena, tak prepocitam c_ladderNextPriceLevel - pouziva sa pri c_ladderHighestReachedStep = 0 alebo -1 (init alebo opakovany init) - pri starte marketu je nastavena na price - a_maxLoss",
	"c_uTs_sortAsc": "list of ascending sorted upper thresholds [{'uT':'102', 'step':2}, {'uT':'103', 'step':1}]",
	"c_lTs_sortDesc": "list of descending sorted lower thresholds [{'lT':'100', 'step':2}, {'uT':'99', 'step':1}]",
	"u_singleEntryAmounts": {
		"descr": "Qtity for buy in USDT (!!POZOR!! musis konvertovat do base amountu, napr.BTC ked vytvaras entry)- berie pred startom zo singleEntryAmounts_client v sharedPrefs. POZN: nema zmysel uz tuto upravovat ceny podla poziadaviek binance na cenu a qty, lebo toto sa stava iba malo krat a ostatne treba vzdy overit"
		"3": 33,
		"6": 50,
		"9": 75, 
		"12": 113,
		"15": 169,
		"18": 254
	},
	"u_PriceQtyReqs": {
		"minPrice": "minimal price - najnizsia mozna cena",
		"tickSize": "minimalna zmena ceny (cela cena delitelna tymto cislom)"
		"stepSize": "minimalna zmena volumu (cely volume delitelny tymto cislom)"
		"minQty": "minimalny volume v kupovanom assete (pri BTCUSDT je to BTC)"
		"minNotional": "minimalny volume v base assete (pri BTCUSDT je to USDT)"
	},
	"entries": {
		"#": "key to each entry is the ladder step int(!) c_ladderHighestReachedStep at the time of creation a new entry(json key can only be a string)"
		"1": {
			"entryType": "vals: limitBuy(ked je vytvoreny buy order), limitSell(detto), waitToBuy (ked sa predalo, a cakam kedy klesne cena o sensibility value aby som mohol zas vytvorit limitBuyOrder), waitToSell(detto)",
			"qty": "the volume which will be / is used in the order - THIS IS THE BASE QTY, so for example in BTCUSDT it is the amount of BTC",
			"lastExchangePrice_avg": 121.22,
			"uT": "stands for upperThreshold",
			"lT": "stands for lowerThreshold",
			"cumullativeLosses": "percentulna suma stratovych predajov, ktora ked prekroci 2*maxLoss, tak je entry vymazany z dict. Pri zarobkoch ide tato hodnota hore maximalne po 0.0"
			}
		"2": {
			"detto"
		}
	}
}

#*********************************************#
#******	 			CONSTANTS			******#
#*********************************************#

# the following are directions as well the desired directions for calculateExchangePrice
WAIT_TO_SELL = 'waitToSell'
WAIT_TO_BUY = 'waitToBuy'
LIMIT_SELL = 'limitSell'
LIMIT_BUY = 'limitBuy'

STATUS = 'status'
EXEC_QTY = 'executedQty'
CUMUL_QTY = 'cummulativeQuoteQty'
ENTRIES = 'entries'
# E_ means that it as a constant of an entry dictionary
E_ENTRY_TYPE = 'entryType'
E_QTY = 'entryQty'
E_LAST_EXCHANGE_PRICE = 'lastExchangePrice_avg'
E_UPPER_TRESHOLD = 'uT'
E_LOWER_TRESHOLD = 'lT'
E_CUMUL_LOSSES = 'cumullativeLosses'
# U_ means that it the variable updated before skript start
U_PRICE_QTY_REQS = 'u_PriceQtyReqs'
# cislo, ktore je prilis vysoke na to aby bolo dosiahnute, pouzivane pri UT pre waitToBuy
i_OUTOFRANGE = 1000000


def trade(client, key, jD, pricesFromTicker, backTest=False):
	
	#*********************************************#
	#* 					NOTES					**#
	#*********************************************#	
	
	# key stands for the name of the json
	#
	# jD stands for jsonDictionary
	# prefix 'a_' stands for mandatory variables
	# prefix 'c_' stands for computed variables
	# prefix 'u_' stands for variables which are updated before the start of the script, for example minQty
	# all variables from jD have a prefix (except 'strategy' and 'client') - these need to be !! updated !! in the jD
	# !!! variables without prefix are NOT updated in the jD !!!
	#
	#
	#
	#
	#
	#
	#
	#
	#
	#
	#
	#*********************************************#
	#*********************************************#
	#*********************************************#

	price = pricesFromTicker.get(jD['a_tradedSymbol'], 0)
	if (price==0):
		return None
	
	############## ZACIATOK SPAWNERA ##############
	
	# TODO v buducnu skus prerobit na limit order s rezevervou (rozdielom medzi trigger a cena) - ten by vedel rychlejsie reagovat a mal by "poistku" ze nekupi prilis draho
	# TODO v buducnu vytiahni casti z tohto spawnera ktore maju za ulohu init, alebo opakovany init kvoli efektivite skriptu
	# spawner comes as first!
	
	ladderNextPriceLevel = jD.get(jD['c_ladderNextPriceLevel'], 0.0)
	# ked je 0.0 tak je to uplne novy init
	if(ladderNextPriceLevel == 0.0):
		jD['c_ladderNextPriceLevel'] = price * ( 1.0 + jD['a_sensitivityForMinimalPriceChange'] )
		jD['c_ladderBottomBoundary'] = price * ( 1.0 - jD['a_maxLoss'] )
		jD['c_ladderHighestReachedStep'] = 0
		return jD
		
	if (price >= jD['c_ladderNextPriceLevel']):
		# 1A, ked sa dany market startuje, tak bol c_ladderNextPriceLevel nastaveny na aktualnu cenu + krok. c_ladderHighestReachedStep je nastaveny na 0, resp. na -1 ak som uz vstupil ale mi to nevyslo - musel byt entry vymazany
		# 1B, ked je dany market uz nastartovany, tak pokracuje tak je to posledna (najvyssia) cena za ktoru som kupoval
		
		# ked je cena dosiahnuta, vytvorim market order
		return createMarketOrderForNewLadderEntry( client, jD, price )
	
	# TODO c_ladderBottomBoundary a c_ladderHighestReachedStep sa musia nastavit vtedy, ked budem vymazavat posledny entry a nebude tam uz ziadny iny
	if (jD['c_ladderHighestReachedStep'] <= 0 and price < jD['c_ladderBottomBoundary']):
		# ked je to cisto novy init
		if(jD['c_ladderHighestReachedStep'] == 0):
			# ked je to cisto novy init, tak posuvam hornu hranicu (a_sensitivityForMinimalPriceChange) dole a vstupujem iba cez nu
			oldNextPriceLevel_moved = price * (1 + jD['a_sensitivityForMinimalPriceChange'] + jD['a_maxLoss'])
			jD['c_ladderNextPriceLevel'] = oldNextPriceLevel_moved + ((jD['c_ladderNextPriceLevel'] - oldNextPriceLevel_moved ) / 2)
			jD['c_ladderBottomBoundary'] = price
			return jD
		# ked je to opakovany init, tak vstupujem aj cez spodnu hranicu, hornu hranicu nemenim 
		# TODO (neskor ponechaj ako vysvetlivku) (pri vymaze entry by mala byt nastavena spodna hranica na sumu znizenu o celkove percento ktore som prerobil )
		# TODO i ked je to len najnizsia suma, neskor by si mohol vymysliet nieco viac sofistikovane pre pripad extremneho padu marketu
		elif(jD['c_ladderHighestReachedStep'] == -1):
			return createMarketOrderForNewLadderEntry( client, jD, price )
		
	############## KONIEC SPAWNERA ##############
	
	tmp = {}

	list_uTs_sortAsc = jD['c_uTs_sortAsc']
	list_lTs_sortDesc = jD['c_lTs_sortDesc']
	
	for i in range(len(list_uTs_sortAsc)):
		if (price > list_uTs_sortAsc[i][E_UPPER_TRESHOLD]):
			strLadderStep = str(list_uTs_sortAsc[i]['step'])
			stepDic = jD[ENTRIES].get(strLadderStep, {E_ENTRY_TYPE: None})
			if (stepDic[E_ENTRY_TYPE]==LIMIT_BUY):
				r = uTlimitBuy(client, price, stepDic, jD['u_PriceQtyReqs'], jD['a_tradedSymbol'])
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_ENTRY_TYPE]==LIMIT_SELL):
				r = uTlimitSell(price, stepDic)
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_ENTRY_TYPE]==WAIT_TO_SELL):
				r = uTwaitToSell(price, stepDic)
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_ENTRY_TYPE] is None):
				traderFunctions.ploggerErr(__name__ + ' / ' + jD['a_tradedSymbol'] +  ' - ' + ' the ladderStep Nr. ' + strLadderStep + ' from list_uTs_sortAsc could not be found in the jD[entries] dictionary - there must be a discrepancy in the data!')
			else:
				traderFunctions.ploggerErr(__name__ + ' / ' + jD['a_tradedSymbol'] +  ' - ' + ' for the ladderStep Nr. ' + strLadderStep + ' was an unexpected ' + E_ENTRY_TYPE + ' found: "' + stepDic[E_ENTRY_TYPE] + '" - this was not expecpected!')
		else:
			break
			
	for j in range(len(list_lTs_sortDesc)):
		if (price < list_lTs_sortDesc[j][E_LOWER_TRESHOLD]):
			strLadderStep = str(list_lTs_sortDesc[j]['step'])
			stepDic = jD[ENTRIES].get(strLadderStep, {E_ENTRY_TYPE: None})
			if (stepDic[E_ENTRY_TYPE]==LIMIT_BUY):
				r = lTlimitBuy(price, stepDic)
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_ENTRY_TYPE]==LIMIT_SELL):
				r = lTlimitSell(client, price, stepDic, jD['u_PriceQtyReqs'], jD['a_tradedSymbol'])
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_ENTRY_TYPE]==WAIT_TO_BUY):
				r = lTwaitToBuy(price, stepDic)
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_ENTRY_TYPE]==WAIT_TO_SELL):
				r = lTwaitToSell(client, price, stepDic, jD['u_PriceQtyReqs'], jD['a_tradedSymbol'])
				if not (r is None):
					tmp[strLadderStep] = r
			elif (stepDic[E_ENTRY_TYPE] is None):
				traderFunctions.ploggerErr(__name__ + ' / ' + jD['a_tradedSymbol'] +  ' - ' + ' the ladderStep Nr. ' + strLadderStep + ' from list_lTs_sortDesc could not be found in the jD[entries] dictionary - there must be a discrepancy in the data!')
			else:
				traderFunctions.ploggerErr(__name__ + ' / ' + jD['a_tradedSymbol'] +  ' - ' + ' for the ladderStep Nr. ' + strLadderStep + ' was an unexpected ' + E_ENTRY_TYPE + ' found: "' + stepDic[E_ENTRY_TYPE] + '" - this was not expecpected!')
		else:
			break

	
	if bool(tmp):
		jD[ENTRIES].update(tmp)
		jD.update(updateSortedListsOfTresholds(jD))
		return jD
	else:
		return None


# ESTE TREBA RAZ PREJST ASI VSETKY
def uTlimitBuy(client, currPrice, stepDic, priceQtyReqs, tradedSymbol):
	# cena za ktoru si chcel kupit - ak prekrocena, vytvoris market buy
	calcQty = traderFunctions.validQty(priceQtyReqs, currPrice, stepDic[E_QTY])
	marketOrderStats = client.order_market_buy(symbol=tradedSymbol, quantity=calcQty)
	if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
		fillQty = float(marketOrderStats[EXEC_QTY])
		fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		# update stepDic, goig to be a waitToSell
		stepDic[E_ENTRY_TYPE] = WAIT_TO_SELL
		stepDic[E_LAST_EXCHANGE_PRICE] = fillPrice
		stepDic[E_QTY] = fillQty
		# calculate the uT and lT for the new waitToSell entry
		# upper treshold bude avgExchangePrice + sensitivity, ked je prekrocena, vytvori limitSell
		stepDic[E_UPPER_TRESHOLD] = fillPrice * (1.0 + sensitivity)
		# lower treshold bude avgExchangePrice minus maxLoss kde bude cakat stopLimitOrder na predaj so stratou
		stepDic[E_LOWER_TRESHOLD] = fillPrice * (1.0 - maxLoss)
	else:
		traderFunctions.ploggerErr(__name__ + ' / ' + tradedSymbol +  ' - ' + ' unexpected situation, the market order from uTlimitBuy had a different status then ' + client.ORDER_STATUS_FILLED + '. Here is the whole response:\n' + marketOrderStats)
		return None

	return stepDic


# DONE
def uTlimitSell(currPrice, stepDic):
	# toto je hodnota climaxu, ked je prekrocena, tak prepocitas cenu za ktoru chces predat'
	stepDic[E_UPPER_TRESHOLD] = float(currPrice)
	# zaokruhlenie podla pravidiel na minPrice atd je potom ked vytvaras order, aby si optimalizoval pocetnost
	stepDic[E_LOWER_TRESHOLD] = calculateExchangePrice(float(stepDic[E_LAST_EXCHANGE_PRICE]), currPrice, LIMIT_SELL)
	return stepDic

# DONE
def uTwaitToBuy(currPrice, stepDic):
	# nerobis minusovy obchod v tomto smere (defCoin to Coin), to znamena, ze ta nezaujima upperTreshold ked cakas na kupu, jedina moznost na ozivenie je ked cena klesne pod exchangePrice minus sensitivity
	# tato funkcia NIE JE VOLANA, je tu iba ako POZNAMKA
	# TODO_future, mohol by si v buducnosti spravi nejake pocitadlo, na tento pripade (mimo sensitivity area), aby si vedel kolko dead orderov mas
	return None


# DONE
def uTwaitToSell(currPrice, stepDic):
	# hodnota avgExchangePrice + sensitivity, bola prekrocena, takze vytvoris limitSell
	stepDic[E_ENTRY_TYPE] = LIMIT_SELL
	# nove lT, uT
	stepDic[E_UPPER_TRESHOLD] = currPrice
	# uT, bude polovica medzi tym co si predal a terajsou cenou
	stepDic[E_LOWER_TRESHOLD] = calculateExchangePrice(float(stepDic[E_LAST_EXCHANGE_PRICE]), currPrice, LIMIT_SELL)
	# POZN: v calculateExchangePrice keby sa dostal prvy argument ako None, tak chcem aby to crashlo, lebo to potom znamena, ze mam niekde nezrovnalosti
	
	return stepDic

# DONE
def lTlimitBuy(currPrice, stepDic):
	# - je to climax, po ktoreho prekroceni vyratas novu hodnotu limit orderu
	stepDic[E_LOWER_TRESHOLD] = float(currPrice)
	# zaokruhlenie podla pravidiel na minPrice atd je potom ked vytvaras order, aby si optimalizoval pocetnost
	stepDic[E_UPPER_TRESHOLD] = calculateExchangePrice(float(stepDic[E_LAST_EXCHANGE_PRICE]), currPrice, LIMIT_BUY)
	
	return stepDic
	
def lTlimitSell(client, currPrice, stepDic, priceQtyReqs, tradedSymbol):
	# cena za ktoru si chcel predat - ak prekrocena, vytvoris market sell
	calcQty = traderFunctions.validQty(priceQtyReqs, currPrice, stepDic[E_QTY])
	marketOrderStats = client.order_market_sell(symbol=tradedSymbol, quantity=calcQty)
	if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
		fillQty = float(marketOrderStats[EXEC_QTY])
		fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		# update stepDic, going to be a waitToBuy
		stepDic[E_ENTRY_TYPE] = WAIT_TO_BUY
		stepDic[E_LAST_EXCHANGE_PRICE] = fillPrice
		stepDic[E_QTY] = fillQty
		# calculate the uT and lT for the new waitToBuy entry
		# upper treshold bude i_OUTOFRANGE kedze nikdy nechem aby som robil minusovy obchod
		stepDic[E_UPPER_TRESHOLD] = i_OUTOFRANGE
		# lower treshold bude avgExchangePrice minus sensitivity
		stepDic[E_LOWER_TRESHOLD] = fillPrice * (1.0 - sensitivity)
	else:
		traderFunctions.ploggerErr(__name__ + ' / ' + tradedSymbol +  ' - ' + ' unexpected situation, the market order from uTlimitBuy had a different status then ' + client.ORDER_STATUS_FILLED + '. Here is the whole response:\n' + marketOrderStats)
		return None

	return stepDic	


# DONE
def lTwaitToBuy(currPrice, stepDic):
	# hodnota avgExchangePrice minus sensitivity, ked je prekrocena, vytvoris limitBuy
	stepDic[E_ENTRY_TYPE] = LIMIT_BUY
	# nove lT, uT
	stepDic[E_LOWER_TRESHOLD] = currPrice
	# uT, bude polovica medzi tym co si predal a terajsou cenou
	stepDic[E_UPPER_TRESHOLD] = calculateExchangePrice(float(stepDic[E_LAST_EXCHANGE_PRICE]), currPrice, LIMIT_BUY)
	
	return stepDic

def lTwaitToSell(client, currPrice, stepDic, priceQtyReqs, tradedSymbol):
	# cena ktora je ako keby taky stop loss po tom ako si vstupil do lTwaitToSell
	calcQty = traderFunctions.validQty(jpriceQtyReqs, currPrice, stepDic[E_QTY])
	marketOrderStats = client.order_market_sell(symbol=tradedSymbol, quantity=calcQty)
	if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
		fillQty = float(marketOrderStats[EXEC_QTY])
		fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		# update stepDic, going to be a waitToBuy
		stepDic[E_ENTRY_TYPE] = WAIT_TO_BUY
		stepDic[E_LAST_EXCHANGE_PRICE] = fillPrice
		stepDic[E_QTY] = fillQty
		# calculate the uT and lT for the new waitToBuy entry
		# upper treshold bude i_OUTOFRANGE kedze nikdy nechem aby som robil minusovy obchod
		stepDic[E_UPPER_TRESHOLD] = i_OUTOFRANGE
		# lower treshold bude avgExchangePrice minus sensitivity
		stepDic[E_LOWER_TRESHOLD] = fillPrice * (1.0 - sensitivity)
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
	ladderHighestReachedStep = jD['c_ladderHighestReachedStep'] + 1
	# correction because of the possible value -1 in c_ladderHighestReachedStep
	if ( ladderHighestReachedStep < 1):
		ladderHighestReachedStep = 1
	jD['c_ladderHighestReachedStep'] = ladderHighestReachedStep	
	
	# get Qty - step 1 (get USDT amount from u_singleEntryAmounts)
	calcQty = getAmountForNewLadderStep(jD['u_singleEntryAmounts'], ladderHighestReachedStep)
	# get Qty - step 2 (convert the USDT to coin amount based on the price from the ticker)
	calcQty = calcQty / priceFromTicker
	# get Qty - step 3 (run the calculated Qty throught the Qty validator)
	calcQty = traderFunctions.validQty(jD['u_PriceQtyReqs'], priceFromTicker, calcQty)
	
	marketOrderStats = client.order_market_buy(symbol=jD['a_tradedSymbol'], quantity=calcQty)
	if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
		fillQty = float(marketOrderStats[EXEC_QTY])
		fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		# update dics
		jD['c_ladderNextPriceLevel'] = fillPrice * (1.0 + jD['a_sensitivityForMinimalPriceChange'])
		jD[ENTRIES][str(ladderHighestReachedStep)] = {E_ENTRY_TYPE: WAIT_TO_SELL,
														E_QTY: fillQty,
														E_LAST_EXCHANGE_PRICE: fillPrice,
														E_UPPER_TRESHOLD: fillPrice * (1.0 + jD['a_sensitivityForMinimalPriceChange']),
														E_LOWER_TRESHOLD: fillPrice * (1.0 - jD['a_maxLoss'])
													}
	else:
		traderFunctions.ploggerErr(__name__ + ' / ' + jD['a_tradedSymbol'] +  ' - ' + ' unexpected situation, the market order had a different status then ' + client.ORDER_STATUS_FILLED + '. Here is the whole response:\n' + marketOrderStats)
		return None

	return jD

	
def updateSortedListsOfTresholds(jD):
	entries = jD.get(ENTRIES, {})
	if not bool(entries):
		traderFunctions.ploggerErr(__name__ + ' / ' + jD['a_tradedSymbol'] +  ' - ' + ' THIS WAS NOT SUPPOSED TO HAPPEN - no dictionary for entries found. Here is the whole jD:\n' + jD)
		return jD
	
	list_to_be_sorted = list()
	for ladderStep, ladderStepDic in entries.items():
		# TODO_future the c_uTs_sortAsc could have only the uTs, and c_lTs_sortDesc only lTs. Also maybe lists instead of dics would be faster
		list_to_be_sorted.append({"step": ladderStep, E_LOWER_TRESHOLD: ladderStepDic[E_LOWER_TRESHOLD], E_UPPER_TRESHOLD: ladderStepDic[E_UPPER_TRESHOLD]})

	return{'c_uTs_sortAsc': sorted(list_to_be_sorted, key=lambda k: k[E_UPPER_TRESHOLD]),	'c_lTs_sortDesc': sorted(list_to_be_sorted, key=lambda k: k[E_LOWER_TRESHOLD], reverse=True)}
	


# TODO_future, najprv by som chcel vidiet ako spravaju jednotlive entries a okrem toho to nie je MVP
def mergeAndDeleteEntries(jD):
	pass


def calculateExchangePrice(lastExchangePrice_avg, newPriceClimax, desiredDirection, startingTargetRatio=0.5, maxTargetRatio=0.8):
	# startingTargetRatio = inicialna hodnota pomeru s ktorym zacne pocitat ked dosiahne minimalny posun v cene
	# maxTargetRatio = maximal target ratio value
	
	if (desiredDirection == LIMIT_BUY):
		if (lastExchangePrice_avg > newPriceClimax):
			#((3000 - 2000) / 2000) / 2 + 0,5
			newTargetRatio = ((lastExchangePrice_avg - newPriceClimax) / newPriceClimax) / 2 + startingTargetRatio
		else:
			newTargetRatio = startingTargetRatio
			# we are on the wrong side - using 1.004 as the half of it is 0.2 % and that is the minimum trade diff which is making profit
			traderFunctions.ploggerWarn(__name__ + 'In the function calculateExchangePrice the lastExchangePrice_avg="' + str(lastExchangePrice_avg) + '" was smaller then newPriceClimax="' + str(newPriceClimax) + '" for the direction ' + desiredDirection + '. This was not expected, please investigate', False)
			newPriceClimax = lastExchangePrice_avg * 1.004
		if (newTargetRatio > maxTargetRatio):
			newTargetRatio = maxTargetRatio
		print('am here, values are: lastExchangePrice_avg=' + str(lastExchangePrice_avg) + ' newPriceClimax=' + str(newPriceClimax) + 'newTargetRatio=' + str(newTargetRatio))
		newTargetPrice = lastExchangePrice_avg - ((lastExchangePrice_avg - newPriceClimax) * newTargetRatio)
		
	if (desiredDirection == LIMIT_SELL):
		if (lastExchangePrice_avg < newPriceClimax):
			# ((4000 - 3000) / 3000) / 2 + 0,5
			newTargetRatio = ((newPriceClimax - lastExchangePrice_avg) / lastExchangePrice_avg) / 2 + startingTargetRatio
		else:
			newTargetRatio = startingTargetRatio
			# we are on the wrong side - using 0.996 as the half of it is 0.2 % and that is the minimum trade diff which is making profit
			traderFunctions.ploggerWarn(__name__ + 'In the function calculateExchangePrice the newPriceClimax="' + str(newPriceClimax) + '" was smaller then lastExchangePrice_avg="' + str(lastExchangePrice_avg) + '" for the direction ' + desiredDirection + '. This was not expected, please investigate', False)
			newPriceClimax = lastExchangePrice_avg * 0.996
		if (newTargetRatio > maxTargetRatio):
			newTargetRatio = maxTargetRatio
		newTargetPrice = ((newPriceClimax - lastExchangePrice_avg) * newTargetRatio) + lastExchangePrice_avg
	
	return newTargetPrice