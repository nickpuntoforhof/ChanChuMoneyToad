# This file is part of krakenex.
# Licensed under the Simplified BSD license. See `examples/LICENSE.txt`.

"""
ChanChuMoneyToad
       ____  __.---""---.__  ____
      /$$$$\/              \/$$$$\
     ($$$$$$)              ($$$$$$)
      \__OO/                \OO__/
    __/                          \__
 .-"    .                      .    "-.
 |  |   \.._                _../   |  |
  \  \    \."-.__________.-"./    /  /
    \  \    "--.________.--"    /  /
  ___\  \_                    _/  /___
./    $$$$$                  $$$$$    \.
\                                      /
 \           \_          _/           /
   \    \____/$$-.____.-$$\____/    /
     \    \                  /    /
      -.  .|               ./.
    ." / |  -              /  | -  ".
 ."  /   |   -           /   |   -   ".
/.$./.$$.|.$$.\          /.$$.|.$$.\.$.|
"""

import datetime
from decimal import Decimal as D
import pprint
import pandas

import krakenex


class Log:
    
    def __init__(self, file, log_name = None):
        self._log = file
        self._name = log_name
        
    def log(x, mode='a'):
        print('')
        if self._name is not None:
            print(self._name, ' updated at: ', datetime.datetime.now())
        print(x)
        with open(self._log) as l:
            print('')
            if self._name is not None:
                print(self._name, ' updated at: ', datetime.datetime.now())
            print(x)


class KrakenOrder:

    def __init__(self,
            pair,
            type,
            order_type,
            price,
            price2,
            volume,
            leverage,
            oflags,
            starttm,
            expiretm,
            userref,
            validate,
            close
    ):
        """
        Kraken Documentation: Add standard order
        https://www.kraken.com/en-us/features/api

        pair = asset pair
        type = type of order (buy/sell)
        ordertype = order type:
            market
            limit (price = limit price)
            stop-loss (price = stop loss price)
            take-profit (price = take profit price)
            stop-loss-limit (price = stop loss trigger price, price2 = triggered limit price)
            take-profit-limit (price = take profit trigger price, price2 = triggered limit price)
            settle-position
        price = price (optional.  dependent upon ordertype)
        price2 = secondary price (optional.  dependent upon ordertype)
        volume = order volume in lots
        leverage = amount of leverage desired (optional.  default = none)
        oflags = comma delimited list of order flags (optional):
            fcib = prefer fee in base currency
            fciq = prefer fee in quote currency
            nompp = no market price protection
            post = post only order (available when ordertype = limit)
        starttm = scheduled start time (optional):
            0 = now (default)
            +<n> = schedule start time <n> seconds from now
            <n> = unix timestamp of start time
        expiretm = expiration time (optional):
            0 = no expiration (default)
            +<n> = expire <n> seconds from now
            <n> = unix timestamp of expiration time
        userref = user reference id.  32-bit signed number.  (optional)
        validate = validate inputs only.  do not submit order (optional)

        optional closing order to add to system when order gets filled:
            close[ordertype] = order type
            close[price] = price
            close[price2] = secondary price
        """
    
        self.query = {'pair': pair,
             'type': type,
             'ordertype': order_type,
             'price': price,
             'price2': price2,
             'volume': volume,
             'leverage': leverage,
             'oflags': oflags,
             'starttm': starttm,
             'expiretm': expiretm,
             'userref': userref,
             'validate': validate,
             'close': close}
         

class KrakenMarketOrder:

    def __init__(self,
            pair,
            type,
            volume,
    ):
    
        self.query = {'pair': pair,
                        'type': type,
                        'order_type': 'market',
                        'volume': volume}
 

class KrakenLimitOrder:

    def __init__(self,
            pair,
            type,
            volume,
    ):
    
        self.query = {'pair': pair,
                        'type': type,
                        'order_type': 'market',
                        'volume': volume}


class KrakenAPI:
    
    def __init__(self, api_path, project_name = None):
        self._k = krakenex.API()
        self._k.load_key(api_path)
        self.log = Log('./log.log', project_name)
    
    def check_book(self, order, n = 20):
        # Query Book for asset pair
        pair = order.query['pair']
        book = self._k.query_public('Depth', {'pair': pair}, n)
        column_names = ['price', 'volumne', 'timestamp']
        asks = pandas.DataFrame(book['result'][pair]['asks'], columns = column_names)
        bids = pandas.DataFrame(book['result'][pair]['bids'], columns = column_names)
        asks = asks.sort_values(by=['timestamp'], ascending=False)
        bids = bids.sort_values(by=['timestamp'], ascending=False)
        asks['timestamp'] = pandas.to_datetime(asks['timestamp'],unit='s')
        bids['timestamp'] = pandas.to_datetime(bids['timestamp'],unit='s')
        # Display Results
        print('~~~~~~~~~~~ Book for', pair, '~~~~~~~~~~~')
        print('Asks')
        print(asks.head(n=n))
        print('Bids')
        print(bids.head(n=n))
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        
    def validate_order(self, order):
        get_balances()
        

    def execute_order(self, order):
        response = self._k.query_private('AddOrder', order)
        self.log.log(response)
    
    def print_asset_pairs(self, *args):
        q = self._k.query_public('AssetPairs')
        asset_pairs = [key for key in q['result'].keys()]
        if len(args) == 0:
            print([pair for pair in asset_pairs])
        elif len(args) == 1:
            for pair in asset_pairs:
                if args[0] in pair:
                    print(pair)
        elif len(args) == 2:
            for pair in asset_pairs:
                if args[0] in pair and args[1] in pair:
                    print(pair)
        else:
            print('Too many assets')

    
    def get_balances(self):
        balance = self._k.query_private('Balance')
        orders = self._k.query_private('OpenOrders')

        balance = balance['result']
        orders = orders['result']
        
        #print(balance)

        newbalance = dict()
        for currency in balance:
            # remove first symbol ('Z' or 'X'), but not for GNO or DASH
            newname = currency[1:] if len(currency) == 4 and currency != "DASH" else currency
            newbalance[newname] = D(balance[currency]) # type(balance[currency]) == str
        balance = newbalance

        for _, o in orders['open'].items():
            # remaining volume in base currency
            volume = D(o['vol']) - D(o['vol_exec'])

            # extract for less typing
            descr = o['descr']

            # order price
            price = D(descr['price'])

            pair = descr['pair']
            base = pair[:3] if pair != "DASHEUR" else "DASH"
            quote = pair[3:] if pair != "DASHEUR" else "EUR"

            type_ = descr['type']
            if type_ == 'buy':
                # buying for quote - reduce quote balance
                balance[quote] -= volume * price
            elif type_ == 'sell':
                # selling base - reduce base balance
                balance[base] -= volume

        clean_balances = {}
        for k, v in balance.items():
            # convert to string for printing
            if v == D('0'):
                s = '0'
            else:
                s = str(v)
            # remove trailing zeros (remnant of being decimal)
            s = s.rstrip('0').rstrip('.') if '.' in s else s
            #
            clean_balances[k] = s

        return clean_balances