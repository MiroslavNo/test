#*********************************************#
#******	 EVERY STRATEGY HAS TO HAVE		******#
#*********************************************#
import traderFunctions
import strategyFunctions

# prefix "a_" stands for mandatory variables
# prefix "c_" stands for computed variables
# client and strategy have no prefix ( DO NOT put one there, because you would need to edit the runner as well)
mandatoryInitVars = {
				   "a_tradedSymbol": "",
				   "a_currentState": "vals: waitToBUY, waitToSELL, BuyingNow, SellingNow",
				   "a_lastExchangePrice_avg": "",
				   "a_quantity": "",
				   "a_sensibilityForMinimalPriceChange": "percentualna hodnota v absolutnom cisle, ktora musi byt prekrocena, aby po zmene pozicie zacal uvazovat nad tym, ze zmeni poziciu zas (hodnota hovori ze sme dosiahli prvy climax od zmeny pozicie)",
				   "c_priceClimaxSinceLastExchange": "maximalna cena ktoru dosiahol v tebe priaznivom smere",
				   "c_priceToExchange": "vypocitana cena kedy bude vystupovat z danej pozicie",
				   "strategy": "NEVYPLNAS, bere automaticky z nazvu suboru",
				   "client": "NEVYPLNAS, bere automaticky z nazvu suboru"
					}


def trade(client, key, jD, pricesFromTicker, backTest=False):
	
	#*********************************************#
	#* 					NOTES					**#
	#*********************************************#	
	cf = False
	
	# key stands for the name of the json
	#
	# jD stands for jsonDictionary
	# prefix "a_" stands for mandatory variables
	# prefix "c_" stands for computed variables
	# all variables from jD have a prefix (except "strategy" and "client") - these need to be !! updated !! in the jD
	# !!! variables without prefix are NOT updated in the jD !!!
	#
	# cf stands for the change flag
	#
	# if the value a_currentState was updated than write:
	#		a_currentState = "sellingNow"
	#		jD["a_currentState"], cf = a_currentState, True
	#
	# kazdy RETURN musis napisat nasledovne
	# return (jD if cf else None)	
	#
	#*********************************************#
	#*********************************************#
	#*********************************************#

	# minimalny zisk oproti predoslemu trade-u, inak nebudem tradovat, lebo poplatky su vo vyske zisku
	minimalPriceChangeForATrade = 0.002


	if (a_currentState == "waitToBUY"):
		if (c_priceClimaxSinceLastExchange == 0.0):
			# c_priceClimaxSinceLastExchange == 0.0 means it is either an initial json file or after a trade (position change)
			if (currentPrice > (lastExchangePrice_avg * (1.0 - a_sensibilityForMinimalPriceChange))):
				# no climax achieved yet ()
				return (jD if c else None)
			else:
				traderFunctions.logger.info('%s - first climax reached since the initialisation of the json with state: ' + a_currentState, key)
				traderFunctions.logger.info('%s - current price=' + str(currentPrice) + " / lastExchangePrice_avg=" + str(lastExchangePrice_avg), key)













	return (jD if c else None)	