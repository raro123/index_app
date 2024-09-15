import pandas as pd
import numpy as np
from enum import Enum
from scipy.stats import norm
from deltalake import DeltaTable
from utils.cloudstorage import get_storage_options

DATAPATH = 's3://financial-data-store/bronze/nseindex/daily_price_nifty_indices/'
QUANT_PERCENTILE_EXTREME = 0.01
QUANT_PERCENTILE_STD = 0.3
NORMAL_DISTR_RATIO = norm.ppf(QUANT_PERCENTILE_EXTREME) / norm.ppf(QUANT_PERCENTILE_STD)
BUSINESS_DAYS_IN_YEAR = 256
WEEKS_PER_YEAR = 52.25
MONTHS_PER_YEAR = 12
SECONDS_PER_YEAR = 365.25 * 24 * 60 * 60

Frequency = Enum(
    "Frequency",
    "Natural Year Month Week BDay",
)

NATURAL = Frequency.Natural
YEAR = Frequency.Year
MONTH = Frequency.Month
WEEK = Frequency.Week

PERIODS_PER_YEAR = {
    MONTH: MONTHS_PER_YEAR,
    WEEK: WEEKS_PER_YEAR,
    YEAR: 1

}

def load_daily_price_data(path=DATAPATH):
    daily_index_price = DeltaTable(path, storage_options=get_storage_options()).to_pandas()
    return daily_index_price


def robust_vol(
    daily_returns:pd.Series,
    annualise_stdev: bool = False,
    BUSINESS_DAYS_IN_YEAR = 256
) -> pd.Series:

    ## Can do the whole series or recent history
    daily_exp_std_dev = daily_returns.ewm(span=32).std()

    if annualise_stdev:
        annualisation_factor = BUSINESS_DAYS_IN_YEAR ** 0.5
    else:
        ## leave at daily
        annualisation_factor = 1

    annualised_std_dev = daily_exp_std_dev * annualisation_factor

    ## Weight with ten year vol
    ten_year_vol = annualised_std_dev.rolling(
        BUSINESS_DAYS_IN_YEAR * 10, min_periods=1
    ).mean()
    weighted_vol = 0.3 * ten_year_vol + 0.7 * annualised_std_dev

    return weighted_vol


def calculate_stats(perc_return: pd.Series,
                at_frequency: Frequency = NATURAL) -> dict:

    perc_return_at_freq = sum_at_frequency(perc_return, at_frequency=at_frequency)

    ann_mean = ann_mean_given_frequency(perc_return_at_freq, at_frequency=at_frequency)
    ann_median = ann_median_given_frequency(perc_return_at_freq, at_frequency=at_frequency)
    ann_std = ann_std_given_frequency(perc_return_at_freq, at_frequency=at_frequency)
    sharpe_ratio = ann_mean / ann_std

    skew_at_freq = perc_return_at_freq.skew()
    drawdowns = calculate_drawdown(perc_return_at_freq)
    avg_drawdown = drawdowns.mean()
    max_drawdown = drawdowns.min()
    quant_ratio_lower = calculate_quant_ratio_lower(perc_return_at_freq)
    quant_ratio_upper = calculate_quant_ratio_upper(perc_return_at_freq)

    return dict(
        ann_mean = ann_mean,
       # ann_median = ann_median,
        ann_std = ann_std,
        sharpe_ratio = sharpe_ratio,
        skew = skew_at_freq,
        avg_drawdown = avg_drawdown,
        max_drawdown = max_drawdown,
        quant_ratio_lower = quant_ratio_lower,
        quant_ratio_upper = quant_ratio_upper
    )



def periods_per_year(at_frequency: Frequency):
    if at_frequency == NATURAL:
        return BUSINESS_DAYS_IN_YEAR
    else:
        return PERIODS_PER_YEAR[at_frequency]



def years_in_data(some_data: pd.Series) -> float:
    datediff = some_data.index[-1] - some_data.index[0]
    seconds_in_data = datediff.total_seconds()
    return seconds_in_data / SECONDS_PER_YEAR


def sum_at_frequency(perc_return: pd.Series,
                     at_frequency: Frequency = NATURAL) -> pd.Series:

    if at_frequency == NATURAL:
        return perc_return

    at_frequency_str_dict = {
                        YEAR: "Y",
                        WEEK: "7D",
                        MONTH: "1M"}
    at_frequency_str = at_frequency_str_dict[at_frequency]

    perc_return_at_freq = perc_return.resample(at_frequency_str).sum()

    return perc_return_at_freq


def ann_mean_given_frequency(perc_return_at_freq: pd.Series,
                             at_frequency: Frequency) -> float:

    mean_at_frequency = perc_return_at_freq.mean()
    periods_per_year_for_frequency = periods_per_year(at_frequency)
    annualised_mean = mean_at_frequency * periods_per_year_for_frequency

    return annualised_mean

def ann_median_given_frequency(perc_return_at_freq: pd.Series,
                             at_frequency: Frequency) -> float:

    median_at_frequency = perc_return_at_freq.median()
    periods_per_year_for_frequency = periods_per_year(at_frequency)
    annualised_median = median_at_frequency * periods_per_year_for_frequency

    return annualised_median

def ann_std_given_frequency(perc_return_at_freq: pd.Series,
                             at_frequency: Frequency) -> float:

    std_at_frequency = perc_return_at_freq.std()
    periods_per_year_for_frequency = periods_per_year(at_frequency)
    annualised_std = std_at_frequency * (periods_per_year_for_frequency**.5)

    return annualised_std


def calculate_drawdown(perc_return):
    cum_perc_return = perc_return.apply(np.log1p).cumsum().apply(np.exp)
    max_cum_perc_return = cum_perc_return.rolling(len(perc_return)+1,
                                                  min_periods=1).max()
    return cum_perc_return/max_cum_perc_return-1


def calculate_quant_ratio_lower(x):
    x_dm = demeaned_remove_zeros(x)
    raw_ratio = x_dm.quantile(QUANT_PERCENTILE_EXTREME) / x_dm.quantile(
        QUANT_PERCENTILE_STD
    )
    return raw_ratio / NORMAL_DISTR_RATIO

def calculate_quant_ratio_upper(x):
    x_dm = demeaned_remove_zeros(x)
    raw_ratio = x_dm.quantile(1 - QUANT_PERCENTILE_EXTREME) / x_dm.quantile(
        1 - QUANT_PERCENTILE_STD
    )
    return raw_ratio / NORMAL_DISTR_RATIO

def demeaned_remove_zeros(x):
    x[x == 0] = np.nan
    return x - x.mean()


def performance_stats_df(perc_return, at_frequency=NATURAL):
    stats = calculate_stats(perc_return, at_frequency)
    df = (pd.DataFrame
          .from_dict(stats,orient='index',columns=['stats'])
          .assign(freq = at_frequency.name)
    )

    return df

def calculate_returns_wide(df,kind = 'log', resample=None,dropna=True):
    log_returns = df.drop(['index_name','index_type','index_category'], axis=1).set_index(['symbol', 'date'])[['close']].unstack(0).droplevel(0, axis=1).apply(np.log).diff()
    if dropna:
        log_returns = log_returns.dropna()
    if resample:
        log_returns = log_returns.resample(resample).sum()
        
    if kind == 'log':
        return log_returns
    else:
        return np.expm1(log_returns)
    
def performance_stats_instruments(df):
    stats_df = pd.DataFrame()
    for c in df.columns:
        stats_df[c] = performance_stats_df(df[c])[['stats']]
    return stats_df.T

def robust_vol(
    daily_returns:pd.Series,
    annualise_stdev: bool = False,
    BUSINESS_DAYS_IN_YEAR = 256
) -> pd.Series:

    ## Can do the whole series or recent history
    daily_exp_std_dev = daily_returns.ewm(span=32).std()

    if annualise_stdev:
        annualisation_factor = BUSINESS_DAYS_IN_YEAR ** 0.5
    else:
        ## leave at daily
        annualisation_factor = 1

    annualised_std_dev = daily_exp_std_dev * annualisation_factor

    ## Weight with ten year vol
    ten_year_vol = annualised_std_dev.rolling(
        BUSINESS_DAYS_IN_YEAR * 10, min_periods=1
    ).mean()
    weighted_vol = 0.3 * ten_year_vol + 0.7 * annualised_std_dev

    return weighted_vol

def calculate_returns_wide(df,kind = 'log', resample=None,dropna=True, close_col = 'close'):
    log_returns = df.drop(['index_name'], axis=1).set_index(['symbol', 'date'])[[close_col]].unstack(0).droplevel(0, axis=1).apply(np.log).diff()
    if dropna:
        log_returns = log_returns.dropna()
    if resample:
        log_returns = log_returns.resample(resample).sum()
        
    if kind == 'log':
        return log_returns
    else:
        return np.expm1(log_returns)
    
def create_wide_price_df(df):
    analysis_df = df[['symbol','close','date']].set_index(['date','symbol']).unstack(1).droplevel(0, axis=1).sort_index()
    return analysis_df