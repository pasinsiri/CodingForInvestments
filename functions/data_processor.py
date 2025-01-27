import pandas as pd
import numpy as np
import os

DEFAULT_DTYPE_DICT = {
    'ticker': 'str',
    'open': 'float64',
    'high': 'float64',
    'low': 'float64',
    'close': 'float64',
    'volume': 'int64',
    'adj close': 'float64',
    'dividends': 'float64',
    'stock splits': 'float64'
}

def get_parquet_paths(base_path: str, first_year: int, last_year: int, ticker: str = None):
    """Get the paths of parquet files in a specific year and month

    Args:
        base_path (str): a base directory where the parquet files are stored
        first_year (int): the first year to be considered
        last_year (int): the last year to be considered
        ticker (str, optional): the stock ticker of interest, if set to None, the function will read all the data regardless of tickers. Defaults to None.

    Returns:
        list: a list of paths of parquet files
    """
    paths = []
    for year in range(first_year, last_year + 1):
        for month in range(1, 13):
            m_str = '{:02d}'.format(month)
            # ? if no ticker is parsed, all available in a specific year and month will be returned
            ym_path = f'{base_path}/{year}/{m_str}'
            if ticker is None:
                paths.extend(os.listdir(ym_path))
            else:
                path = f'{ym_path}/{ticker}.parquet'
                if os.path.exists(path):
                    paths.append(path)
                else:
                    # print(f'{path} not found')
                    pass
    return paths

def convert_price_to_raw(
        ticker: str, base_path: str, export_base_path: str, 
        first_year: int, last_year: int,  dtype_dict: dict = DEFAULT_DTYPE_DICT, 
        adjust_cols: list = ['open', 'high', 'low', 'close', 'dividends'], split_col_name:str = 'stock splits',
        remove_factor_columns: bool = True, save_data: bool = True
):
    """Calculate the raw prices by adjusting for stock splits and dividends.

    Args:
        ticker (str): The stock ticker.
        base_path (str): The base directory where the parquet files are stored.
        export_base_path (str): The base directory where the processed files will be saved.
        first_year (int): The first year to be considered.
        last_year (int): The last year to be considered.
        dtype_dict (dict, optional): A dictionary specifying the data types for the columns. Defaults to DEFAULT_DTYPE_DICT.
        adjust_cols (list, optional): A list of columns to be adjusted. Defaults to ['open', 'high', 'low', 'close', 'dividends'].
        split_col_name (str, optional): The name of the column containing stock split information. Defaults to 'stock splits'.
        remove_factor_columns (bool, optional): Whether to remove the adjustment factor columns after processing. Defaults to True.
        save_data (bool, optional): Whether to save the processed data. Defaults to True.
    """
    paths = get_parquet_paths(
        base_path=base_path,
        first_year=first_year,
        last_year=last_year,
        ticker=ticker
    )

    # * if data for the ticker does not exist, skip it
    if len(paths) == 0:
        return
    
    # * load data
    ticker_df = pd.read_parquet(*[paths]).sort_index(ascending=False)
    ticker_df['adjust_factor'] = ticker_df[split_col_name] \
                                    .apply(lambda x: 1 if x == 0 else x)
    ticker_df['cum_adj_factor'] = ticker_df['adjust_factor'].cumprod() \
                                    .shift(1).fillna(1)
    
    for col in adjust_cols:
        ticker_df[col] = ticker_df[col] * ticker_df['cum_adj_factor']
    
    ticker_df = ticker_df.sort_index()

    # TODO: cast data type
    for col, dtype in dtype_dict.items():
        ticker_df[col] = ticker_df[col].astype(dtype)

    if remove_factor_columns:
        ticker_df = ticker_df.drop(['adjust_factor', 'cum_adj_factor'], axis=1)

    # TODO: save data
    if save_data:
        for path in paths:
            path_split = path.split('/')
            year, month = path_split[4], path_split[5]
            month_df = ticker_df[(ticker_df.index.year == int(year)) & 
                                 (ticker_df.index.month == int(month))]
            # export_path = f'{export_base_path}/{year}/{month}/{ticker}.parquet'
            year_path = f'{export_base_path}/{year}'
            if not os.path.exists(year_path):
                os.mkdir(year_path)
            month_path = f'{year_path}/{month}'
            if not os.path.exists(month_path):
                os.mkdir(month_path)
            month_df.to_parquet(f'{month_path}/{ticker}.parquet')
    else:
        return ticker_df

def convert_price_to_raw_multiple(
        ticker_list: list, base_path: str, export_base_path: str, 
        first_year: int, last_year: int,  dtype_dict: dict = DEFAULT_DTYPE_DICT, 
        adjust_cols: list = ['open', 'high', 'low', 'close', 'dividends'], split_col_name:str = 'stock splits',
        remove_factor_columns: bool = True, save_data: bool = True
):
    """Convert price to raw for multiple tickers.

    Args:
        ticker_list (list): a list of stock tickers
        base_path (str): base directory where the parquet files are stored
        export_base_path (str): export directory where the processed files will be saved
        first_year (int): first year to be considered
        last_year (int): last year to be considered
        dtype_dict (dict, optional): a dictionary representing data type for each column. Defaults to DEFAULT_DTYPE_DICT.
        adjust_cols (list, optional): a list of columns to be adjusted. Defaults to ['open', 'high', 'low', 'close', 'dividends'].
        split_col_name (str, optional): column name for stock split actions. Defaults to 'stock splits'.
        remove_factor_columns (bool, optional): if true, remove factor columns created and used to adjust price. Defaults to True.
        save_data (bool, optional): if true, result will be saved. otherwise, it'll be returned. Defaults to True.

    Returns:
        pd.DataFrame: a pandas DataFrame of the processed data
    """
    
    res_list = [convert_price_to_raw(
        ticker, base_path, export_base_path, 
        first_year, last_year, dtype_dict, 
        adjust_cols, split_col_name, 
        remove_factor_columns, save_data
    ) for ticker in ticker_list]

    if not save_data:
        return res_list

    # for ticker in ticker_list:
    #     paths = get_parquet_paths(
    #         base_path=base_path,
    #         first_year=first_year,
    #         last_year=last_year,
    #         ticker=ticker
    #     )

    #     # * if data for the ticker does not exist, skip it
    #     if len(paths) == 0:
    #         continue

    #     ticker_df = pd.read_parquet(*[paths]).sort_index(ascending=False)
    #     ticker_df['adjust_factor'] = ticker_df[split_col_name] \
    #                                     .apply(lambda x: 1 if x == 0 else x)
    #     ticker_df['cum_adj_factor'] = ticker_df['adjust_factor'].cumprod() \
    #                                     .shift(1).fillna(1)
    #     for col in adjust_cols:
    #         ticker_df[col] = ticker_df[col] * ticker_df['cum_adj_factor']
    #     ticker_df = ticker_df.sort_index()

    #     # TODO: cast data type
    #     for col, dtype in dtype_dict.items():
    #         ticker_df[col] = ticker_df[col].astype(dtype)

    #     if remove_factor_columns:
    #         ticker_df = ticker_df.drop(['adjust_factor', 'cum_adj_factor'], axis=1)
        
    #     # TODO: save data
    #     for path in paths:
    #         path_split = path.split('/')
    #         year, month = path_split[4], path_split[5]
    #         month_df = ticker_df[(ticker_df.index.year == int(year)) & 
    #                              (ticker_df.index.month == int(month))]
    #         # export_path = f'{export_base_path}/{year}/{month}/{ticker}.parquet'
    #         year_path = f'{export_base_path}/{year}'
    #         if not os.path.exists(year_path):
    #             os.mkdir(year_path)
    #         month_path = f'{year_path}/{month}'
    #         if not os.path.exists(month_path):
    #             os.mkdir(month_path)
    #         month_df.to_parquet(f'{month_path}/{ticker}.parquet')

def adjust_price(
        ticker: str, base_path: str, export_base_path: str,
        first_year: int, last_year: int,
        adjust_cols: list = ['open', 'high', 'low', 'close', 'dividends'], split_col_name:str = 'stock splits',
        save_result: bool = False
):
    """adjust price for a single ticker

    Args:
        ticker (str): a stock ticker
        base_path (str): a base directory where the parquet files are stored
        export_base_path (str): an export directory where the processed files will be saved
        first_year (int): the first year
        last_year (int): the last year
        adjust_cols (list, optional): price columns to be adjusted. Defaults to ['open', 'high', 'low', 'close', 'dividends'].
        split_col_name (str, optional): stock splits' column name. Defaults to 'stock splits'.
        save_result (bool, optional): whether to save result or not. Defaults to False.

    Returns:
        pd.DataFrame: a pandas DataFrame of the processed data
    """
    paths = get_parquet_paths(
        base_path=base_path,
        first_year=first_year,
        last_year=last_year,
        ticker=ticker
    )

    # * if data for the ticker does not exist, skip it
    if len(paths) == 0:
        return

    ticker_df = pd.read_parquet(*[paths]).sort_index(ascending=False)

    # * handle for stock splits
    ticker_df['adjust_factor'] = ticker_df[split_col_name] \
                                    .apply(lambda x: 1 if x == 0 else x)
    ticker_df['cum_adj_factor'] = ticker_df['adjust_factor'].cumprod() \
                                    .shift(1).fillna(1)
    for col in adjust_cols:
        ticker_df[col] = ticker_df[col] / ticker_df['cum_adj_factor']

    # * adjust dividend
    ticker_df['fwd_div'] = ticker_df['dividends'].shift(1).fillna(0)
    ticker_df['retention_rate'] = 1 - (ticker_df['fwd_div'] / ticker_df['close'])
    ticker_df['accum_retention'] = ticker_df['retention_rate'].cumprod()
    ticker_df['adj_close'] = ticker_df['accum_retention'] * ticker_df['close']

    return ticker_df
    

def adjust_price_multiple(
        ticker_list: list, base_path: str, export_base_path: str,
        first_year: int, last_year: int,
        adjust_cols: list = ['open', 'high', 'low', 'close', 'dividends'], split_col_name:str = 'stock splits',
        save_result: bool = False
):
    res = [
        adjust_price(
            ticker=ticker,
            base_path=base_path,
            export_base_path=export_base_path,
            first_year=first_year,
            last_year=last_year,
            adjust_cols=adjust_cols,
            split_col_name=split_col_name,
            save_result=save_result
        ) for ticker in ticker_list
    ]

    if not save_result:
        return res