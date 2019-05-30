def calculateExchangePrice(lastExchangePrice_avg, newPriceClimax, desiredDirection, startingTargetRatio=0.5, maxTargetRatio=0.8):
	# startingTargetRatio = inicialna hodnota pomeru s ktorym zacne pocitat ked dosiahne minimalny posun v cene
	# maxTargetRatio = maximal target ratio value
	
	if (desiredDirection == 'limitBuy'):
		if (lastExchangePrice_avg > newPriceClimax):
			#((3000 - 2000) / 2000) / 2 + 0,5
			newTargetRatio = ((lastExchangePrice_avg - newPriceClimax) / newPriceClimax) / 2 + startingTargetRatio
		else:
			newTargetRatio = startingTargetRatio
			# we are on the wrong side - using 1.004 as the half of it is 0.2 % and that is the minimum trade diff which is making profit
			#TODO tuto over co to sposobuje, sice by sa to sme nemalo dostat
			newPriceClimax = lastExchangePrice_avg * 1.004
		if (newTargetRatio > maxTargetRatio):
			newTargetRatio = maxTargetRatio
		print('am here, values are: lastExchangePrice_avg=' + str(lastExchangePrice_avg) + ' newPriceClimax=' + str(newPriceClimax) + 'newTargetRatio=' + str(newTargetRatio))
		newTargetPrice = lastExchangePrice_avg - ((lastExchangePrice_avg - newPriceClimax) * newTargetRatio)
		
	if (desiredDirection == 'limitSell'):
		if (lastExchangePrice_avg < newPriceClimax):
			# ((4000 - 3000) / 3000) / 2 + 0,5
			newTargetRatio = ((newPriceClimax - lastExchangePrice_avg) / lastExchangePrice_avg) / 2 + startingTargetRatio
		else:
			newTargetRatio = startingTargetRatio
			# we are on the wrong side - using 0.996 as the half of it is 0.2 % and that is the minimum trade diff which is making profit
			#TODO tuto over co to sposobuje, sice by sa to sme nemalo dostat
			newPriceClimax = lastExchangePrice_avg * 0.996
		if (newTargetRatio > maxTargetRatio):
			newTargetRatio = maxTargetRatio
		newTargetPrice = ((newPriceClimax - lastExchangePrice_avg) * newTargetRatio) + lastExchangePrice_avg
	
	return newTargetPrice


def isOrderIdFilled(client, tradedSymbol, orderID):
	# was checking, it is an int, but maybe it could change in the future
	if( isinstance(orderID, int) ):
		# 0 stands for no order
		if(int(orderID) == 0):
			return false
			
	order = client.get_order(symbol=tradedSymbol, orderId=orderID)
	
	pass

# returns the amount which wasnt filled
def unfilledAmountFrom(orderID):
	pass

	