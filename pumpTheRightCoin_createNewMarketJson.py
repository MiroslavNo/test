import traderFunctions

clients = traderFunctions.addClients()
client=clients['tibRick']

from strat import pumpTheRightCoin

symbol = 'BNBUSDT'

# print(traderFunctions.formatDictForPrint(pumpTheRightCoin.startNewMarket('tibRick', client, 'BNBUSDT', traderFunctions.getScriptLocationPath(0))))

# additional param for a new market:
# pumpTheRightCoin.startNewMarket('tibRick', client, 'BNBUSDT', traderFunctions.getScriptLocationPath(0), 'NEW_MARKET')

# also the price can be added straight away:
pumpTheRightCoin.startNewMarket('tibRick', client, 'ETHUSDT', traderFunctions.getScriptLocationPath(0), 'NEW_MARKET', 10.2)