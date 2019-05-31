#*********************************************#
#******	 EVERY STRATEGY HAS TO HAVE		******#
#*********************************************#
import traderFunctions
import strategyFunctions
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
	"a_maxSlippage": "percentualna hodnota v absolutnom cisle, ktora udava kedy sa nenaplneni order, cez ktore hodnotu trh preletel nma naplnit market orderom",
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
			"orderId": "123456 ked je 0, znamena ze k entry nie je vytvoreny order | None neviem velmi pouzit, v .js je to null",
			"orderPrice": "the price which will be / is used in the order",
			"orderQty": "the volume which will be / is used in the order - THIS IS THE BASE QTY, so for example in BTCUSDT it is the amount of BTC",
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

# TODO tieto kostanty by mohli byt aj v samotnej fcii podla mna
# NIE - pravdepodobne sa to inicializuje iba raz, keby to bolo vo fcii, tak sa to robi zakazdym
# OTESTUJ to, daj sem print a uvidis, ci ti bude zakazdym printovat

#*********************************************#
#******	 			CONSTANTS			******#
#*********************************************#

# the following are directions as well the desired directions for calculateExchangePrice
WAIT_TO_SELL = 'waitToSell'
WAIT_TO_BUY = 'waitToBuy'
LIMIT_SELL = 'limitSell'
LIMIT_BUY = 'limitBuy'

# this one is for entries which are to be deleted
DELETED = 'del'

STATUS = 'status'
EXEC_QTY = 'executedQty'
CUMUL_QTY = 'cummulativeQuoteQty'
# E_ means that it as a constant of an entry dictionary
E_ENTRY_TYPE = 'entryType'
E_ORDER_ID = 'orderId'
E_ORDER_PRICE = 'orderPrice'
E_ORDER_QTY = 'orderQty'
E_LAST_EXCHANGE_PRICE = 'lastExchangePrice_avg'
E_UPPER_TRESHOLD = 'uT'
E_LOWER_TRESHOLD = 'lT'
E_CUMUL_LOSSES = 'cumullativeLosses'
# U_ means that it the variable updated before skript start
U_PRICE_QTY_REQS = 'u_PriceQtyReqs'
# cislo, ktore je prilis vysoke na to aby bolo dosiahnute, pouzivane pri UT pre waitToBuy
i_OUTOFRANGE = 1000000

API_ERR_TOO_LATE = 'APIError(code=-2010): Order would trigger immediately.'

def trade(client, key, jD, pricesFromTicker, backTest=False):
	
	#*********************************************#
	#* 					NOTES					**#
	#*********************************************#	
	cf = False
	
	# key stands for the name of the json
	#
	# jD stands for jsonDictionary
	# prefix 'a_' stands for mandatory variables
	# prefix 'c_' stands for computed variables
	# prefix 'u_' stands for variables which are updated before the start of the script, for example minQty
	# all variables from jD have a prefix (except 'strategy' and 'client') - these need to be !! updated !! in the jD
	# !!! variables without prefix are NOT updated in the jD !!!
	#
	# cf stands for the change flag
	#
	# if the value a_currentState was updated than write:
	#		a_currentState = 'sellingNow'
	#		jD['a_currentState'], cf = a_currentState, True
	#
	# kazdy RETURN musis napisat nasledovne
	# return (jD if cf else None)	
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
	
	# todo dopln argumenty ked budes mat hotove jednotlive fcie - alebo posli cely jD
	for i in range(len(list_uTs_sortAsc)):
		if (price > list_uTs_sortAsc[i][E_UPPER_TRESHOLD]):
			ladderStep = list_uTs_sortAsc[i]['step']
			stepDic = jD['entries'].get(ladderStep, {E_ENTRY_TYPE: None})
			if (stepDic[E_ENTRY_TYPE]==LIMIT_BUY):
				r = uTlimitBuy(stepDic, price, jD['a_maxSlippage'])
				if not (r is None):
					tmp[ladderStep] = r
			elif (stepDic[E_ENTRY_TYPE]==LIMIT_SELL):
				r = uTlimitSell(stepDic, price)
				if not (r is None):
					tmp[ladderStep] = r
			elif (stepDic[E_ENTRY_TYPE]==WAIT_TO_SELL):
				r = uTwaitToSell(stepDic, price)
				if not (r is None):
					tmp[ladderStep] = r
			# TODO dorob warning e je nezrovnalost v ladderStepoch - aj do lT loopu to dorob
			# elif (stepDic[E_ENTRY_TYPE]==None):
		else:
			break
			
	for j in range(len(list_lTs_sortDesc)):
		if (price < list_lTs_sortDesc[j][E_LOWER_TRESHOLD]):
			ladderStep = list_lTs_sortDesc[j]['step']
			stepDic = jD['entries'].get(ladderStep, {E_ENTRY_TYPE: None})
			if (stepDic[E_ENTRY_TYPE]==LIMIT_BUY):
				r = lTlimitBuy(stepDic, price)
				if not (r is None):
					tmp[ladderStep] = r
			elif (stepDic[E_ENTRY_TYPE]==LIMIT_SELL):
				r = lTlimitSell(stepDic, price, jD['a_maxSlippage'])
				if not (r is None):
					tmp[ladderStep] = r
			elif (stepDic[E_ENTRY_TYPE]==WAIT_TO_BUY):
				r = lTwaitToBuy(stepDic, price)
				if not (r is None):
					tmp[ladderStep] = r
			elif (stepDic[E_ENTRY_TYPE]==WAIT_TO_SELL):
				r = lTwaitToSell(stepDic, price, jD['a_maxSlippage'])
				if not (r is None):
					tmp[ladderStep] = r
		else:
			break

	
	if bool(tmp):
		# reset orders
		jD['entries'].update(tmp)
		return resetOrdersAfterChangesInLadder(jD)
	else:
		return None




def uTlimitBuy(client, tradedSymbol, stepDic, currPrice, maxSlippage, maxLoss, sensitivity):
	# cena za ktoru si chcel kupit - ak prekrocena, pozeras 2 veci: 
	# - ci sa naplnil order, ak ano, tak vytvoris waitToSell
	# - ci sa prekrocil maxSlippage, vteda vytvoris marketorder v objeme nanaplnenej casti orderu a z neho hned waitToSell
	cf = False
	fillQty = 0
	fillPrice = 0
	orderId = stepDic.get(E_ORDER_ID, None)
	
	if(orderId is None):
		# ak nebol vytoreny ORDER, lebo napr TRADER nebezal - kedze je cena vyssia mal by si kupit?
		cf = True
		# todo log co sa stalo
		# mohol by som tu este rozlisovat medzi tym ci presiel cez maxSlippage, ale to by bolo velmi narocne na logiku s listom kde mas zoradel upper tresholds, kedze tento je uz cez
		
		marketOrderStats = client.order_market_buy(tradedSymbol, quantity=float(stepDic[E_ORDER_QTY]))
		if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
			fillQty = float(marketOrderStats[EXEC_QTY])
			fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		else:
			# TODO log error, zapis cely marketOrderStats, lebo ten response by mal byt filled (testoval som to)
			pass
	else:	
		orderStats = client.get_order(tradedSymbol, orderId)
		
		if(orderStats[STATUS] == client.ORDER_STATUS_FILLED):
			cf = True
			# get fill stats
			fillQty = float(orderStats[EXEC_QTY])
			fillPrice = float(orderStats[CUMUL_QTY]) / fillQty
		elif(currPrice > (float(stepDic[E_UPPER_TRESHOLD]) * (1 + maxSlippage))):
			cf = True
			if(orderStats[STATUS] == client.ORDER_STATUS_PARTIALLY_FILLED):
				# get data from prev order ID if filled partially
				fillQty = float(orderStats[EXEC_QTY])
				fillPrice = float(orderStats[CUMUL_QTY]) / fillQty
				restQty = float(stepDic[E_ORDER_QTY]) - fillQty
				# create market order for the rest amount
				# TODO tuto este over ci restQty je validne mnozstvo podla binance poziadaviek
				marketOrderStats = client.order_market_buy(tradedSymbol, quantity=restQty)
				# @tested
				if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
					fillQty_market = float(marketOrderStats[EXEC_QTY])
					fillPrice_market = float(marketOrderStats[CUMUL_QTY]) / fillQty_market
					fillPrice = ((fillQty_market * fillPrice_market) + (fillQty * fillPrice)) / (fillQty_market + fillQty)
					# nove fillQty musi byt vypocitane az ako posledne, ekdze pouzivas povodnu hodnotu na predoslom riadku
					fillQty = fillQty_market + fillQty
				else:
					# TODO log error, zapis cely marketOrderStats, lebo ten response by mal byt filled (testoval som to)
					pass
			else:
				# the order got slipped all away
				marketOrderStats = client.order_market_buy(tradedSymbol, quantity=float(stepDic[E_ORDER_QTY]))
				if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
					fillQty = float(marketOrderStats[EXEC_QTY])
					fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
				else:
					# TODO log error, zapis cely marketOrderStats, lebo ten response by mal byt filled (testoval som to)
					pass
				
			# cancel the previous orderID (or the rest of it)
			client.cancel_order(tradedSymbol, orderId))
	
	if(cf):
		# update stepDic, goig to be a waitToSell
		stepDic[E_ENTRY_TYPE] = WAIT_TO_SELL
		stepDic[E_LAST_EXCHANGE_PRICE] = fillPrice
		stepDic[E_ORDER_QTY] = fillQty
		# calculate the uT and lT for the new waitToSell entry
		# upper treshold bude avgExchangePrice + sensitivity, ked je prekrocena, vytvori limitSell
		stepDic[E_UPPER_TRESHOLD] = fillPrice * (1.0 + sensitivity)
		# lower treshold bude avgExchangePrice minus maxLoss kde bude cakat stopLimitOrder na predaj so stratou
		stepDic[E_LOWER_TRESHOLD] = fillPrice * (1.0 - maxLoss)
		return stepDic
	else:
		return None

# DONE
def uTlimitSell(stepDic, currPrice):
	# toto je hodnota climaxu, ked je prekrocena, tak prepocitas cenu za ktoru chces predat'
	stepDic[E_UPPER_TRESHOLD] = float(currPrice)
	# zaokruhlenie podla pravidiel na minPrice atd je potom ked vytvaras order, aby si optimalizoval pocetnost
	stepDic[E_LOWER_TRESHOLD] = strategyFunctions.calculateExchangePrice(float(stepDic[E_LAST_EXCHANGE_PRICE]), currPrice, LIMIT_SELL)
	return stepDic

# DONE, jedine ze by si to mohol pouzit na inti order, treba este rozhodnut
def uTwaitToBuy(stepDic, currPrice):
	# nerobis minusovy obchod v tomto smere (defCoin to Coin), to znamena, ze ta nezaujima upperTreshold ked cakas an kupu, jedina moznost na ozivenie je ked cena klesne pod exchangePrice minus sensitivity
	# tato funkcia NIE JE VOLANA, je tu iba ako POZNAMKA
	# todo, mohol by si v buducnosti spravi nejake pocitadlo, na tento pripade (mimo sensitivity area), aby si vedel kolko dead orderov mas
	return None


# DONE
def uTwaitToSell(stepDic, currPrice):
	# hodnota avgExchangePrice + sensitivity, bola prekrocena, takze vytvoris limitSell
	stepDic[E_ENTRY_TYPE] = LIMIT_SELL
	# nove lT, uT
	stepDic[E_UPPER_TRESHOLD] = currPrice
	# uT, bude polovica medzi tym co si predal a terajsou cenou
	stepDic[E_LOWER_TRESHOLD] = strategyFunctions.calculateExchangePrice(float(stepDic[E_LAST_EXCHANGE_PRICE]), currPrice, LIMIT_SELL)
	
	return stepDic

# DONE - len je to este nejak zakombinovane s tym init orderom
# to treba overit a rozhodnut kory bude init oreder ci limitBuy alebo waitToBuy
def lTlimitBuy(stepDic, currPrice):
	# - je to climax, po ktoreho prekroceni vyratas novu hodnotu limit orderu
	# TODO to stym init orderom uz nepotrebujem ASI
	# - pri init orderi to budem brat tiez ako climax, tj ked podlezeny, tak vypoctam novu hodnotu za ktoru by som chcel kupit
	# pre int order mala byt tato hodnota nastavena ako cena za ktoru som chcel kupit minus 2 nasobok sensitivity
	# opatrenie ked pri init orderi lastExchangePrice_avg = None
	lastExchangePrice_avg = stepDic.get(E_LAST_EXCHANGE_PRICE, None)
	if (lastExchangePrice_avg is None):
		# setting lastExchangePrice_avg to value where the uT will come as the current uT - this is supposed to be only for a new step in the ladder
		lastExchangePrice_avg = currPrice * (1 + (2 * a_sensitivityForMinimalPriceChange))
		
	stepDic[E_LOWER_TRESHOLD] = float(currPrice)
	# zaokruhlenie podla pravidiel na minPrice atd je potom ked vytvaras order, aby si optimalizoval pocetnost
	stepDic[E_UPPER_TRESHOLD] = strategyFunctions.calculateExchangePrice(float(lastExchangePrice_avg), currPrice, LIMIT_BUY)
	
	return stepDic
	
def lTlimitSell(stepDic, currPrice, maxSlippage):
	# hodnota, za ktoru si chcel predat, ked prekrocena pozeras ci sa naplnil sell order - ak ano vytvoris waitToBuy. Potom pozeras, ci sa neprekrocil maxSlippage, ak ano vytvoris marketSell a hned waitToBuy
	# TODO ak sa prekrocil maxSlippage, tak pozri aj ci nepredavas so stratou, lebo ak ano, tak musis nastavit inak lT a uT
	if(strategyFunctions.isOrderIdFilled(stepDic[E_ORDER_ID]))
		# update stepDic
	
	elif(currPrice < (float(stepDic[E_LOWER_TRESHOLD]) * (1 - maxSlippage)))
		# create market order
		
		marketOrderStats = client.order_market_sell(tradedSymbol, quantity=float(stepDic[E_ORDER_QTY]))
			if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
				fillQty = float(marketOrderStats[EXEC_QTY])
				fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		if(fillPrice < (float(stepDic[E_LAST_EXCHANGE_PRICE]))):
			# predal som so stratou, tj vyrataj lT a uT inak
			pass
		# update stepDic
	
	# TODO check and update cumullativeLosses 
	
	return stepDic

# DONE
def lTwaitToBuy(stepDic, currPrice):
	# hodnota avgExchangePrice minus sensitivity, ked je prekrocena, vytvoris limitBuy
	stepDic[E_ENTRY_TYPE] = LIMIT_BUY
	# nove lT, uT
	stepDic[E_LOWER_TRESHOLD] = currPrice
	# uT, bude polovica medzi tym co si predal a terajsou cenou
	stepDic[E_UPPER_TRESHOLD] = strategyFunctions.calculateExchangePrice(float(stepDic[E_LAST_EXCHANGE_PRICE]), currPrice, LIMIT_BUY)
	
	return stepDic

# TUTO SOM SKONCIL
# TODO pozri ako je s tou quantity, ked ju mas iba v USDT ale pri sell potrebujes quote asset amount
def lTwaitToSell(stepDic, currPrice, maxSlippage, tradedSymbol):
	# hodnota avgExchangePrice minus maxLoss - tu bol dany limit sell na stratu - aspon by mal byt ak vydalo)
	# pozres ci sa order naplnil (ak by nebol k tomuto bodu vytvoreny ziadny order, tak v dic je hodnota 0)
	# ak nie, pozres ci sa neprekrocil maxSlippage, ak ano das market order
	if(strategyFunctions.isOrderIdFilled(stepDic[E_ORDER_ID])):
		# TODO check and update the var cumullativeLosses
		# cumullativeLosses = stepDic[E_CUMUL_LOSSES] + stepDic[E_LAST_EXCHANGE_PRICE] - 
		# if ( cumullativeLosses > ( 2 * maxLoss ) ):
		#	stepDic[E_ENTRY_TYPE] = DELETED
		# else:
		#	stepDic[E_ENTRY_TYPE] = WAIT_TO_BUY
		#	# kedze uT pri WaitToBuy nie je akceptovane, dam to na vysoke cislo
		#	stepDic[E_UPPER_TRESHOLD] = i_OUTOFRANGE
		#	stepDic[E_LOWER_TRESHOLD] = currPrice * (1.0 - maxLoss)
		pass	
		
	elif(currPrice < (float(stepDic[E_LOWER_TRESHOLD]) * (1 - maxSlippage))):
		# create market order for the rest qty if the order would be partially filled
		# todo quantity musi potom vzdy prejst skuskou na validitu
		if (stepDic[E_ORDER_ID] is not None):
			client.cancel_order( symbol=tradedSymbol, orderId=stepDic[E_ORDER_ID])
			qtyMarketOrder = traderFunctions.unfilledAmountFrom(stepDic[E_ORDER_ID])
		else:
			qtyMarketOrder = 
		
		
			marketOrderStats = client.order_market_sell(tradedSymbol, quantity=float(traderFunctions.unfilledAmountFrom(stepDic[E_ORDER_ID])))
			if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
				fillQty = float(marketOrderStats[EXEC_QTY])
				fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		# TODO check and update the var cumullativeLosses
		
		# TODO predal si so slippage,takze inak vyrataj lt a uT
		
		
		# update stepDic
		stepDic[E_ENTRY_TYPE] = WAIT_TO_BUY
	
	return stepDic
	
def updateSortedListsOfTresholds(dic):
	# TODO neveim ci tuto enbum musiet filtrovat an spravny typ entry, kedze napr pri limitBuy ked podlieza lt, tak je to iba novy climax a tym padom netreba robit stopLimitOrder
	entries = dic.get('entries', None)
	if (entries is None):
		# TODO log err
		return dic
	
	list_to_be_sorted = list(())
	for ladderStep, ladderStepDic in entries.items():
		list_to_be_sorted.extend({ladderStep, ladderStepDic[E_LOWER_TRESHOLD], ladderStepDic[E_UPPER_TRESHOLD]})
	
	lTSortedList = sorted(list_to_be_sorted, key=lambda k: k[E_LOWER_TRESHOLD], reverse=True)
	uTSortedList = sorted(list_to_be_sorted, key=lambda k: k[E_UPPER_TRESHOLD])
	
	dic.update({'c_uTs_sortAsc': uTSortedList,	'c_lTs_sortDesc': lTSortedList})
	return dic
	
def resetOrdersAfterChangesInLadder(jD):
	
	jD = updateSortedListsOfTresholds(jD)
	
	# TODO ked budes vytvarat order, tak to musis zaokruhlit podla binance pravidiel pre cenu a mnozsvor
	templD = {}
	
	# vracia finalny jD dictionary
	return templD
	
def getAmountForSpecificStep(amountsDic, stepNo):
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
	calcQty = getAmountForSpecificStep(jD['u_singleEntryAmounts'], ladderHighestReachedStep)
	# get Qty - step 2 (convert the USDT to coin amount based on the price from the ticker)
	calcQty = calcQty / priceFromTicker
	# get Qty - step 3 (run the calculated Qty throught the Qty validator)
	calcQty = traderFunctions.validQty(jD['u_PriceQtyReqs'], priceFromTicker, calcQty)
	
	marketOrderStats = client.order_market_buy(jD['a_tradedSymbol'], quantity=calcQty)
	if(marketOrderStats[STATUS] == client.ORDER_STATUS_FILLED):
		fillQty = float(marketOrderStats[EXEC_QTY])
		fillPrice = float(marketOrderStats[CUMUL_QTY]) / fillQty
		# update dics
		jD['c_ladderNextPriceLevel'] = fillPrice * (1.0 + jD['a_sensitivityForMinimalPriceChange'])
		jD['entries'][str(ladderHighestReachedStep)] = {E_ENTRY_TYPE: WAIT_TO_SELL,
														E_ORDER_QTY: fillQty,
														E_LAST_EXCHANGE_PRICE: fillPrice,
														E_UPPER_TRESHOLD: fillPrice * (1.0 + jD['a_sensitivityForMinimalPriceChange']),
														E_LOWER_TRESHOLD: fillPrice * (1.0 - jD['a_maxLoss'])
													}
	else:
		# TODO log error, zapis cely marketOrderStats, lebo ten response by mal byt filled (testoval som to)
		return None

	return jD
	
def mergeAndDeleteEntries(jD):
	pass




# HOW TO USE STOP LIMIT ORDERS:
#try:
#	client.order_stop_limit_buy(**traderFunctions.validLimitPriceAndQty(traderFunctions.getPriceAndQtyReqs('BTCUSDT', client), 'BTCUSDT', 8000, 0.0002100, 0.999))
#except Exception:
#	if(traceback.format_exc()[-55:-1] == API_ERR_TOO_LATE):
#		# here comes a market order, as it was too late
