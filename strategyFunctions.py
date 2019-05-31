import traderFunctions




def isOrderIdFilled(client, tradedSymbol, orderID):
	# was checking, it is an int, but maybe it could change in the future
	if( isinstance(orderID, int) ):
		# 0 stands for no order
		if(int(orderID) == 0):
			return false
			
	order = client.get_order(symbol=tradedSymbol, orderId=orderID)
	
	pass

# returns the amount which wasnt filled
def getUnfilledAmount(orderID):
	pass
