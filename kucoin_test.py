import asyncio
from kucoin.ws_client import KucoinWsClient
from kucoin.client import WsToken
from kucoin.client import Trade
from kucoin.client import User
from kucoin.client import Market
from kucoin.client import Margin


async def main():
    def getLastSymbolCount(asset):
        accounts = userClient.get_account_list()
        for accountItem in accounts:
            if accountItem['type'] == 'margin' and accountItem['currency'] == asset:
                return float(accountItem['balance'])
        userClient.create_account(account_type='margin', currency=asset)
        return 0

    def getBaseAsset(symbol):
        arr = symbol.split('-')
        if len(arr) > 0:
            return arr[0]
        return ''

    async def deal_msg(msg):
        if msg['topic'] == '/spotMarket/level2Depth5:BTC-USDT':
            print(msg["data"])
        elif msg['topic'] == '/spotMarket/level2Depth5:KCS-USDT':
            print(f'Get KCS level3:{msg["data"]}')

    # is public
    client = WsToken()
    # is private
    # client = WsToken(key='', secret='', passphrase='', is_sandbox=False, url='')
    # is sandbox
    # client = WsToken(is_sandbox=True)
    ws_client = await KucoinWsClient.create(None, client, deal_msg, private=False)
    # await ws_client.subscribe('/market/ticker:BTC-USDT,ETH-USDT')
    # await ws_client.subscribe('/spotMarket/level2Depth5:BTC-USDT,KCS-USDT')

    API_KEY = '609b7c06ce6dbe0006f0e631'
    API_SECRET = 'b5a5092c-644f-44a9-9cf6-426569201a51'
    API_PASSPHRASE = 'Learntotradeinkucoin'

    userClient = User(API_KEY, API_SECRET, API_PASSPHRASE)
    tradeClient = Trade(key=API_KEY, secret=API_SECRET, passphrase=API_PASSPHRASE)
    marketClient = Market(url='https://api.kucoin.com')
    marginClient = Margin(API_KEY, API_SECRET, API_PASSPHRASE)
    # res = marginClient.get_mark_price('ETH-BTC')
    # print(res)
    # userClient.create_account(account_type='margin', currency='BCHSV')
    try:
        # res = tradeClient.create_market_margin_order(symbol='BTC-UST', side='sell', size=0.0004)
        res = marginClient.create_borrow_order('ETH', 'IOC', 2.26)
        # res = marginClient.click_to_repayment('BTC', 'RECENTLY_EXPIRE_FIRST', 0.01)
        print(res)
    except Exception as e:
        print("create_order exception occured - {}".format(e))

    accounts = userClient.get_account_list()
    print(accounts)
    # count = getLastSymbolCount(getBaseAsset('DOGE-USDT'))
    # print(count)
    # while True:
    #     await asyncio.sleep(60, loop=loop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())