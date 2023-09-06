"""
File: stock_reader.py
Author: pasins
Latest Update: 2023-09-04
How to run:
    From your command line: 
    python stock_reader.py --start 2023-08-01 --ann_factor 252 --market_suffix .BK --export_path ./data/set
    (all parameters description can be found in the parser block below)
"""

import json 
import datetime as dt
import logging
import argparse
from functions.data_reader import YFinanceReader

# TODO: get arguments
parser = argparse.ArgumentParser()
parser.add_argument('--start', help='Start month of (over)writing data, should be in the date format with day equal to 1')
parser.add_argument('--ann_factor', help='Annualization factor')
parser.add_argument('--market_suffix', help='Market suffix')
parser.add_argument('--export_path', help='Path to save file (data will be partitioned by ticker and then year and month in the given path)')
parser.add_argument('--log', default='warning')

# TODO: access arguments
# START = dt.date(2022, 5, 1) # ? parsing example
# ANNUALIZATION_FACTOR = 252 # ? parsing example
# MARKET_SUFFIX = '.BK' # ? parsing example
args = parser.parse_args()
START = dt.datetime.strptime(args.start, '%Y-%m-%d')
ANNUALIZATION_FACTOR = args.ann_factor
MARKET_SUFFIX = args.market_suffix
EXPORT_PATH = args.export_path
LOGGING_LEVEL = args.log

# * check logging config
log_level_mapping = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}
log_level = log_level_mapping[LOGGING_LEVEL.lower()]
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f'Retrieving data and saving since {START}.')
logging.info(f'Using annualization factor of {ANNUALIZATION_FACTOR}')
logging.info(f'The market suffix is {MARKET_SUFFIX}')

# TODO: load stock and sector data
with open('./keys/set_sectors.json', 'r') as f:
    sectors = json.load(f)

all_tickers = sectors.values()
all_tickers = [v + MARKET_SUFFIX for s in all_tickers for v in s]
logging.info(f'Getting data of {len(all_tickers)} tickers')

yfr = YFinanceReader(stock_sectors = sectors, market_suffix = MARKET_SUFFIX)
yfr.load_data(period = '1y')
yfr.save(EXPORT_PATH, start_writing_date=START)