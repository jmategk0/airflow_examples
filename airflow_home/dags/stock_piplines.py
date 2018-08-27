from datetime import datetime
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
import requests
import pandas as pd
import csv
import json

URL = "https://raw.githubusercontent.com/jmategk0/quandl_reports/master/WIKI-PRICES_10k.csv"
DATA_INPUT_FILE = "stock_prices_10k_sample.csv"
DATA_EXPORT_FILE = "report_open_close_10k_sample.csv"
TEMP_FILE = "report_open_close_10k_sample.json"
STOCK_CODES = ["COF", "GOOGL", "MSFT"]
START_DATE = "2017-01-01"
END_DATE = "2017-06-30"

EX_DIVIDEND_COL = "ex-dividend"
SPLIT_RATIO = "split_ratio"
ADJ_OPEN = "adj_open"
ADJ_HIGH = "adj_high"
ADJ_LOW = "adj_low"
ADJ_CLOSE = "adj_close"
ADJ_VOLUME = "adj_volume"

PRICES_COLUMNS_TO_DROP = [
    EX_DIVIDEND_COL,
    SPLIT_RATIO,
    ADJ_OPEN,
    ADJ_HIGH,
    ADJ_LOW,
    ADJ_CLOSE,
    ADJ_VOLUME
]

TICKER_COL = "ticker"
DATE_COL = "date"
OPEN_COL = "open"
HIGH_COL = "high"
LOW_COL = "low"
CLOSE_COL = "close"
VOLUME_COL = "volume"

PRICES_COLUMNS_TO_KEEP = [
    TICKER_COL,
    DATE_COL,
    OPEN_COL,
    CLOSE_COL,
    HIGH_COL,
    LOW_COL,
    VOLUME_COL
]

def download_file():
	r = requests.get(URL)
	with open(DATA_INPUT_FILE,'wb') as f:
		f.write(r.content)
	return True

def dictionary_to_json(dictionary, write_to_file=False, filename=" ", write_mode='w'):
        if write_to_file:
            with open(filename, write_mode) as json_file:
                json_data = json.dump(dictionary, json_file, indent=4)
        else:
            json_data = json.dumps(dictionary, indent=4)
        return json_data

def populate_dataframe():
    final_df = pd.DataFrame()
    raw_df = pd.read_csv(filepath_or_buffer=DATA_INPUT_FILE, parse_dates=["date"])
    df_filtered_by_code = raw_df[raw_df.ticker.isin(STOCK_CODES)]
    df_filtered_by_date = df_filtered_by_code[
        (df_filtered_by_code.date >= START_DATE) & (df_filtered_by_code.date <= END_DATE)
    ]
    final_df = df_filtered_by_date.drop(PRICES_COLUMNS_TO_DROP, axis=1)
    return final_df

def get_stock_open_close(df, stock_code, time_period="M", round_precision=2):
    stock_results = []

    stock_df = df[df.ticker == stock_code]

    group_by_period_and_open = stock_df[OPEN_COL].groupby(by=stock_df.date.dt.to_period(time_period))
    group_by_period_and_close = stock_df[CLOSE_COL].groupby(by=stock_df.date.dt.to_period(time_period))

    open_means = dict(group_by_period_and_open.mean())
    close_means = dict(group_by_period_and_close.mean())

    for year_mo_key in open_means:
        row = {
            "month": str(year_mo_key),
            "average_open": round(open_means[year_mo_key], round_precision),
            "average_close": round(close_means[year_mo_key], round_precision)
        }
        stock_results.append(row)

    return stock_results

def report_average_open_close():
    raw_df = populate_dataframe()
    report_results = {}

    for stock in STOCK_CODES:
        report_results[stock] = get_stock_open_close(df=raw_df, stock_code=stock)
    dictionary_to_json(report_results, write_to_file=True, filename=TEMP_FILE)
    return True

def json_to_dictionary(filename):

    with open(filename) as json_file:
        json_data = json.load(json_file)
    return json_data

def dictionary_to_csv(list_of_dictionaries, filename, field_names, delimiter=",", write_mode='w'):

    with open(filename, write_mode) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names, delimiter=delimiter)
        writer.writeheader()
        for row in list_of_dictionaries:
            writer.writerow(row)
        return len(list_of_dictionaries)

def save_report():
    raw_results = json_to_dictionary(TEMP_FILE)
    dictionary_to_csv(results, DATA_EXPORT_FILE, PRICES_COLUMNS_TO_KEEP)

dag = DAG('stock_report', description='open_close_report DAG',
          schedule_interval='0 12 * * *',
          start_date=datetime(2018, 8, 25), catchup=False)

extract_operator = PythonOperator(
	task_id='extract_stock_prices_task', 
	python_callable=download_file, 
	retries=3, 
	dag=dag
	)

transform_operator = PythonOperator(
	task_id='transform_stock_prices_task',
	python_callable=report_average_open_close,
	retries=3,
	dag=dag
	)

load_operator = PythonOperator(
	task_id='load_stock_prices_task', 
	python_callable=save_report, 
	retries=3,
	dag=dag
	)

extract_operator >> transform_operator >> load_operator
