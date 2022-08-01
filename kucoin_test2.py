import asyncio
from datetime import datetime

from kucoin.client import Client
from kucoin.asyncio import KucoinSocketManager

api_key = '609b7c06ce6dbe0006f0e631'
api_secret = 'b5a5092c-644f-44a9-9cf6-426569201a51'
api_passphrase = 'Learntotradeinkucoin'


async def main():
    global loop

    # callback function that receives messages from the socket
    async def handle_evt(msg):
        '''arr1 = msg['topic'].split(':')
        arr2 = arr1[1].split('_')
        ticker = arr2[0]
        print('ticker: ', ticker)'''
        '''if msg['topic'] == '/market/ticker:ETH-USDT':
            print(f'got ETH-USDT tick:{msg["data"]}')

        elif msg['topic'] == '/market/snapshot:BTC':
            print(f'got BTC market snapshot:{msg["data"]}')

        elif msg['topic'] == '/market/snapshot:KCS-BTC':
            print(f'got KCS-BTC symbol snapshot:{msg["data"]}')

        elif msg['topic'] == '/market/ticker:all':
            print(f'got all market snapshot:{msg["data"]}')

        elif msg['topic'] == '/account/balance':
            print(f'got account balance:{msg["data"]}')

        elif msg['topic'] == '/market/level2:KCS-BTC':
            print(f'got L2 msg:{msg["data"]}')

        elif msg['topic'] == '/market/match:BTC-USDT':
            print(f'got market match msg:{msg["data"]}')

        elif msg['topic'] == '/market/level3:KCS-BTC':
            if msg['subject'] == 'trade.l3received':
                if msg['data']['type'] == 'activated':
                    # must be logged into see these messages
                    print(f"L3 your order activated: {msg['data']}")
                else:
                    print(f"L3 order received:{msg['data']}")
            elif msg['subject'] == 'trade.l3open':
                print(f"L3 order open: {msg['data']}")
            elif msg['subject'] == 'trade.l3done':
                print(f"L3 order done: {msg['data']}")
            elif msg['subject'] == 'trade.l3match':
                print(f"L3 order matched: {msg['data']}")
            elif msg['subject'] == 'trade.l3change':
                print(f"L3 order changed: {msg['data']}")'''

        if msg['topic'] == '/market/candles:KCS-BTC_1min':
            print(f'got KCS-BTC symbol candles:{msg["data"]}')
            candle = msg['data']['candles']
            openTimeStamp = datetime.fromtimestamp(int(candle[0])).strftime("%Y%m%d %H:%M:%S")
            print('KCS-BTC TimeStamp: ', openTimeStamp)
        elif msg['topic'] == '/market/candles:BTC-USDT_1min':
            print(f'got BTC-USDT symbol candles:{msg["data"]}')
            candle = msg['data']['candles']
            openTimeStamp = datetime.fromtimestamp(int(candle[0])).strftime("%Y%m%d %H:%M:%S")
            print('BTC-USDT TimeStamp: ', openTimeStamp)

    client = Client(api_key, api_secret, api_passphrase)

    ksm = await KucoinSocketManager.create(loop, client, handle_evt)

    # for private topics such as '/account/balance' pass private=True
    # ksm_private = await KucoinSocketManager.create(loop, client, handle_evt, private=True)

    # ETH-USDT Market Ticker
    # await ksm.subscribe('/market/ticker:ETH-USDT')
    # BTC Symbol Snapshots
    # await ksm.subscribe('/market/snapshot:BTC')
    # KCS-BTC Market Snapshots
    # await ksm.subscribe('/market/snapshot:KCS-BTC')
    # All tickers
    # await ksm.subscribe('/market/ticker:all')
    # Level 2 Market Data
    # await ksm.subscribe('/market/level2:KCS-BTC')
    # Market Execution Data
    # await ksm.subscribe('/market/match:BTC-USDT')
    # Level 3 market data
    # await ksm.subscribe('/market/level3:KCS-BTC')
    # Account balance - must be authenticated
    # await ksm_private.subscribe('/account/balance')
    await ksm.subscribe('/market/candles:KCS-BTC_1min')
    await ksm.subscribe('/market/candles:BTC-USDT_1min')

    while True:
        print("sleeping to keep loop open")
        await asyncio.sleep(20, loop=loop)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())