def calculateExchangePrice(lastExchangePrice_avg, newPriceClimax, desiredDirection, startingTargetRatio=0.5, maxTargetRatio=0.8):
	# startingTargetRatio = inicialna hodnota pomeru s ktorym zacne pocitat ked dosiahne minimalny posun v cene
	# maxTargetRatio = maximal target ratio value
	
	if (desiredDirection == 'limitBuy'):
		if (lastExchangePrice_avg > newPriceClimax):
			#((3000 - 2000) / 2000) / 2 + 0,5
			newTargetRatio = ((lastExchangePrice_avg - newPriceClimax) / newPriceClimax) / 2 + startingTargetRatio
		else:
			newTargetRatio = startingTargetRatio
			# we are on the wrong side - using 0.996 as the half of it is 0.2 % and that is the minimum trade diff which is making profit
			#TODO tuto over co to sposobuje, sice by sa to sme nemalo dostat
			newPriceClimax = lastExchangePrice_avg * 0.996
		if (newTargetRatio > maxTargetRatio):
			newTargetRatio = maxTargetRatio
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

def correctOrderQty(desiredPrice, desiredQty, u_PriceQtyReqs):
	pass
def correctOrderPrice(desiredPrice, desiredQty, u_PriceQtyReqs):
	pass

def getPriceAndQtyReqs(tradedSymbol, client):
	infos = client.get_symbol_info(tradedSymbol)
	
	filters = infos.get("filters", None)
	
	if (filters is not None):
		for filter in filters:
			if(filter.get("filterType", None) == "PRICE_FILTER"):
				tickSize = float(filter.get("tickSize", 0.0))
				minPrice = float(filter.get("minPrice", 0.0))
				#price >= minPrice
				#(price-minPrice) % tickSize == 0
			if(filter.get("filterType", None) == "LOT_SIZE"):
				minQty = float(filter.get("minQty", 0.0))
				stepSize = float(filter.get("stepSize", 0.0))
				#quantity >= minQty
				#(quantity-minQty) % stepSize == 0
			if(filter.get("filterType", None) == "MIN_NOTIONAL"):
				applyToMarket = bool(filter.get("applyToMarket", False))
				if(applyToMarket):
					minNotional = float(filter.get("minNotional", 0.0))
					# Check minimum order size
					#if ( price * quantity < minNotional ):
					#	quantity = minNotional / price


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