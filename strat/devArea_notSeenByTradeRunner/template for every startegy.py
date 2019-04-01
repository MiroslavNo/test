#*********************************************#
#******	 EVERY STRATEGY HAS TO HAVE		******#
#*********************************************#
import traderFunctions
import strategyFunctions

# hodnota objektu je popis a vars zacinajuce 'a_' su mandatory
mandatoryInitVars = {
				   "a_currentState": "",
				   "a_epochTimeClimaxSinceLastExchange": "",
				   "a_lastExchangePrice_avg": "",
				   "a_tradedSymbol": "",
				   "strategy": "NEVYPLNAS, bere automaticky z nazvu suboru",
				   "client": "NEVYPLNAS, bere automaticky z nazvu suboru",
					}


def trade(client, pricesFromTicker, jD, backTest=False):
	
	#*********************************************#
	#* 	EVERY TRADE FCION HAS TO HAVE - Begin	**#
	#*********************************************#	
	c = False
	
	# jD stands for jsonDictionary
	# c stands for the change flag
	# if the value a_currentState waas updated than write:
	#		a_currentState = "sellingNow"
	#		jD["a_currentState"], c = a_currentState, True
	#
	# kazdy RETURN musis napisat nasledovne
	# return (jD if c else None)	
	#
	#*********************************************#
	#*********************************************#
	#*********************************************#

	return (jD if c else None)	