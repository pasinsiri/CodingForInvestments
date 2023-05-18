import numpy as np 
import pandas as pd 
import requests
import warnings 
import re 
from bs4 import BeautifulSoup

# * Thai Government Open Data (Web Crawling)
class ThaiGovDataReader():
    def __init__(self) -> None:
        pass

    def _get_divs(self, url:str, attr:dict = None):
        res = requests.get(url)
        soup = BeautifulSoup(res.content, 'html.parser')
        divs = soup.find_all('div', attr)
        return divs
    
    def get_tables(self, url:str, attr:dict = None) -> list:
        attr = attr or {'class': ['row hoverDownload', 'row hoverDownload active']}
        divs = self._get_divs(url=url, attr=attr)

        # * extract url from each div
        results = list()
        for div in divs:
            # ? check if the file is in .xlsx format. if so, get the url
            div = [r for r in div]
            if div[1].find('a').find('img')['alt'] == 'xlsx':
                url = div[1].find('a')['href']
                results.append(url)

        return results
    
    def _get_latest_update_annual(self, url_list:list, regex:str, year_index:list) -> dict:
        assert len(year_index) == 2, 'year_index must contain two values, start and end indices'
        assert year_index[0] < year_index[1], 'start index must be less than end index'
        year_dict = {url: re.findall(regex, url)[0][year_index[0]:year_index[1]] for url in url_list}

        latest_update = dict()
        for url, year in year_dict.items():
            if year not in latest_update:
                latest_update[year] = url

        return latest_update
    
    def save(self, data, export_dir:str):
        for year, url in data.items():
            print(f'Year = {year} and URL = {url}')
            # * get file format
            file_format = url.split('.')[-1]
            response = requests.get(url)
            if response.status_code == 200:
                if file_format == 'xlsx':
                    df = pd.read_excel(response.content)
                    df.to_parquet(f'{export_dir}/{str(year)}.parquet')
                elif file_format == 'csv':
                    df = pd.read_csv(response.content)
                    df.to_parquet(f'{export_dir}/{str(year)}.parquet')
                else:
                    warnings.warn(f'File format {file_format} not supported', category=UserWarning)