import traderFunctions

clients = traderFunctions.addClients()
client=clients['tibRick']

from strat import pumpTheRightCoin


symbol = 'BTCUSDT'
pumpTheRightCoin.startNewMarket('tibRick', client, symbol, traderFunctions.getScriptLocationPath(0))

symbol = 'ONEUSDT'
pumpTheRightCoin.startNewMarket('tibRick', client, symbol, traderFunctions.getScriptLocationPath(0))

symbol = 'ZILUSDT'
pumpTheRightCoin.startNewMarket('tibRick', client, symbol, traderFunctions.getScriptLocationPath(0))


# additional param for a new market:
# pumpTheRightCoin.startNewMarket('tibRick', client, symbol, traderFunctions.getScriptLocationPath(0), 'NEW_MARKET')

# also the price can be added straight away:
#pumpTheRightCoin.startNewMarket('tibRick', client, symbol, traderFunctions.getScriptLocationPath(0), 'NEW_MARKET', 10.2)