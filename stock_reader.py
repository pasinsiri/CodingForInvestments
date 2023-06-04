import json 
import datetime as dt 
from functions.datareader import YFinanceReader

# TODO: set parameters
start = dt.date(2022, 5, 1)
ANNUALIZATION_FACTOR = 252
MARKET_SUFFIX = '.BK'

# TODO: load stock and sector data
with open('./keys/set_sectors.json', 'r') as f:
    sectors = json.load(f)

all_tickers = sectors.values()
all_tickers = [v + MARKET_SUFFIX for s in all_tickers for v in s]

yfr = YFinanceReader(stock_sectors = sectors, market_suffix = MARKET_SUFFIX)
yfr.load_data(period = '1y')
yfr.save('./data/set', start_writing_date=start)