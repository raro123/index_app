import pandas as pd
from typing import List, Dict, Tuple, Optional
import sys
from pathlib import Path
from glob import glob

def extract_statement_period(df: pd.DataFrame) -> Optional[str]:
    """
    Extract the statement period from the DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame containing portfolio data.

    Returns:
        Optional[str]: The statement period if found, None otherwise.

    Raises:
        ValueError: If no statement period is found in the DataFrame.
    """
    try:
        return df[df.iloc[:,1].astype('str').str.contains('Monthly Portfolio Statement')].iloc[:,1].values[0]
    except (IndexError, KeyError):
        raise ValueError("No statement period found in the DataFrame")

def get_idx_from_instrument_text(df: pd.DataFrame, text: str, column: int = 1) -> int:
    """
    Get the index of the row containing the specified text in the given column.

    Args:
        df (pd.DataFrame): The input DataFrame.
        text (str): The text to search for.
        column (int): The column index to search in.

    Returns:
        int: The index of the row containing the text.
    """
    return df[df.iloc[:, column] == text].index[0]

def get_raw_table(df: pd.DataFrame, start_idx_text: str, end_idx_text: str) -> pd.DataFrame:
    """
    Extract a raw table from the DataFrame between the specified start and end texts.

    Args:
        df (pd.DataFrame): The input DataFrame.
        start_idx_text (str): The text indicating the start of the table.
        end_idx_text: The text indicating the end of the table.

    Returns:
        pd.DataFrame: The extracted raw table.
    """
    start_idx = get_idx_from_instrument_text(df, start_idx_text)
    end_idx = get_idx_from_instrument_text(df, end_idx_text)
    table_df = df.iloc[start_idx:end_idx-1, :]
    return table_df

def extract_all_raw_tables(df: pd.DataFrame, table_extract_combos: List[Tuple[str, str]]) -> Dict[str, pd.DataFrame]:
    """
    Extract all raw tables from the DataFrame based on the specified start and end text combinations.

    Args:
        df (pd.DataFrame): The input DataFrame.
        table_extract_combos: A list of tuples containing start and end texts.

    Returns:
        Dict[str, pd.DataFrame]: A dictionary of extracted raw tables.
    """
    df_dict = {}
    for start, end in table_extract_combos:
        df_dict[start] = get_raw_table(df, start, end)
    return df_dict

def rename_columns(df: pd.DataFrame, col_list: List[str]) -> pd.DataFrame:
    """
    Rename the columns of the DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.
        col_list: The list of new column names.

    Returns:
        pd.DataFrame: The DataFrame with renamed columns.
    """
    df.columns = col_list
    return df

def clean_raw_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw table by renaming columns, filtering rows, and converting data types.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    col_list = ['instrument', 'isin', 'industry', 'quantity', 'value', 'percentage_of_net_assets', 'ytm']
    clean_df = (df
                .iloc[:, 1:-3]
                .pipe(rename_columns, col_list)
                .query('(~quantity.isnull())|(~ytm.isnull())')
                .assign(
                    quantity=lambda x: x.quantity.astype(float),
                    value=lambda x: x.value.astype(float),
                    percentage_of_net_assets=lambda x: x.percentage_of_net_assets.astype('string').str.replace('$', '').str.replace('%', '').astype(float),
                    ytm=lambda x: x.ytm.astype(float)
                )
               )
    return clean_df

def clean_all_raw_tables(df_dict: Dict[str, pd.DataFrame]) -> List[pd.DataFrame]:
    """
    Clean all raw tables in the dictionary.

    Args:
        df_dict: A dictionary of raw tables.

    Returns:
        List[pd.DataFrame]: A list of cleaned DataFrames.
    """
    clean_df_list = []
    for key, df in df_dict.items():
        try:
            print(key)
            df = clean_raw_table(df).assign(table_name=key)
            clean_df_list.append(df)
        except Exception as e:
            print(e)
            continue
    return clean_df_list

def process_fund_portfolio(excel_path: Path) -> pd.DataFrame:
    """
    Process a single portfolio Excel file.
    
    Args:
        excel_path (Path): Path to the Excel file.
        
    Returns:
        pd.DataFrame: Processed portfolio data.
        
    Raises:
        FileNotFoundError: If Excel file not found.
        pd.errors.EmptyDataError: If Excel file is empty.
    """
    try:
        df = pd.read_excel(excel_path)
    except (FileNotFoundError, pd.errors.EmptyDataError) as e:
        print(f"Error processing {excel_path}: {str(e)}")
        return pd.DataFrame()

    # Define the text markers for different sections
    equity_domestic = 'Equity & Equity related'
    arbitrage = 'Arbitrage'
    unlisted = '(b) Unlisted'
    equity_foreign = 'Equity & Equity related Foreign Investments'
    derivatives = 'Derivatives'
    money_market = 'Money Market Instruments' 
    options = 'Index / Stock Options'
    futures = 'Index / Stock Futures'
    end_note = 'Notes:'

    try:
        # Extract statement period
        statement_period = extract_statement_period(df)
        
        # Define table extraction combinations
        table_extract_combos = [
            (equity_domestic, arbitrage),
            (arbitrage, unlisted), 
            (equity_foreign, options),
            (options, money_market),
            (money_market, futures),
            (futures, end_note)
        ]

        # Extract and clean tables
        df_dict = extract_all_raw_tables(df, table_extract_combos)
        clean_df_list = clean_all_raw_tables(df_dict)
        
        # Combine cleaned DataFrames
        combined_df = pd.concat(clean_df_list).assign(
            statement_period=statement_period,
            file_name=excel_path.name
        ).reset_index(drop=True)
        
        return combined_df
        
    except Exception as e:
        print(f"Error processing {excel_path}: {str(e)}")
        return pd.DataFrame()

def process_fund_files(fund_code: str) -> pd.DataFrame:
    """
    Process all Excel files for a given fund code.
    
    Args:
        fund_code (str): The fund code to process (e.g. 'PPFAS')
        
    Returns:
        pd.DataFrame: Combined processed data from all Excel files
        
    Raises:
        FileNotFoundError: If data directory not found
    """
    # Get data directory path
    data_dir = Path('data') / fund_code
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
    # Get all Excel files
    excel_files = list(data_dir.glob('*.xls*'))
    
    if not excel_files:
        print(f"No Excel files found in {data_dir}")
        return pd.DataFrame()
        
    # Process each file and combine results
    df_list = []
    for excel_file in excel_files:
        df = process_fund_portfolio(excel_file)
        if not df.empty:
            df_list.append(df)
            
    if df_list:
        return pd.concat(df_list, ignore_index=True)
    else:
        return pd.DataFrame()

def main(fund_code: str = 'PPFAS') -> None:
    """
    Main function to process fund portfolio files.
    
    Args:
        fund_code (str): Fund code to process
    """
    try:
        # Process all files for fund
        combined_df = process_fund_files(fund_code)
        
        if not combined_df.empty:
            print(f"Successfully processed {fund_code} portfolio files:")
            print(f"Total records: {len(combined_df)}")
            print(combined_df.head())
        else:
            print(f"No data processed for fund {fund_code}")
            
    except Exception as e:
        print(f"Error processing fund {fund_code}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Can be called with fund code as argument
    fund_code = sys.argv[1] if len(sys.argv) > 1 else 'PPFAS'
    main(fund_code)