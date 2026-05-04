import sqlite3
import pandas as pd
import yfinance as yf
import logging
from pathlib import Path
from typing import List

class DataManager:
    def __init__(self, db_path: str = "data/market_data.db"):
        # Creates the target directory if it doesn't exist and parent.mkdir ensures we don't crash if the 'data/' folder is missing
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        
        # Establishes a connection to the local sqlite database
        self.conn = sqlite3.connect(self.db_path)
        self._initialize_db()

    def _initialize_db(self):
        cursor = self.conn.cursor()
        
        # Composite PK (symbol, date)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_prices (
                symbol TEXT,
                date TIMESTAMP,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (symbol, date)
            )
        ''')
        self.conn.commit()

    def update_stock_data(self, symbols: List[str], period: str = "2y"):
        logging.info(f"Updating local database for {len(symbols)} symbols...")
        
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                df = stock.history(period=period)
                
                # Failsafe for delisted stocks or network timeouts
                if df.empty:
                    logging.warning(f"No data found for {symbol}.")
                    continue
                
                # Standardises the dataframe schema to match our SQL table layout
                df = df.reset_index()
                df['symbol'] = symbol
                df.rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high', 
                                   'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
                
                # Strips out corporate actions (Dividends, Stock Splits) to save space
                columns_to_keep = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
                df = df[columns_to_keep]

                # Appends data using the custom upsert method
                df.to_sql('daily_prices', self.conn, if_exists='append', index=False, method=self._upsert_method)
                logging.info(f"Successfully updated {symbol}.")
                
            except Exception as e:
                logging.error(f"Failed to update {symbol}: {e}")

    def _upsert_method(self, table, conn, keys, data_iter):
        insert_stmt = f"INSERT OR IGNORE INTO {table.name} ({', '.join(keys)}) VALUES ({', '.join(['?'] * len(keys))})"
        # Depending on the pandas version 'conn' may be passed as a raw connection object
        if hasattr(conn, 'cursor'):
            conn.cursor().executemany(insert_stmt, data_iter)
        else:
            conn.executemany(insert_stmt, data_iter)
            
        self.conn.commit()

    def load_close_prices(self, symbols: List[str]) -> pd.DataFrame:
        query = f"""
            SELECT date, symbol, close 
            FROM daily_prices 
            WHERE symbol IN ({','.join(['?']*len(symbols))})
            ORDER BY date
        """
        # Reads the raw SQL query without auto-parsing dates to prevent DST errors
        df = pd.read_sql_query(query, self.conn, params=symbols)
        
        # Converts the string dates to UTC to resolves pandas mixed timezones detected error
        df['date'] = pd.to_datetime(df['date'], utc=True)
        
        # Turns the SQL data into a 2D matrix (rows = dates, columns = symbols)
        pivot_df = df.pivot(index='date', columns='symbol', values='close')
        
        # Forward fills to handle NaN gaps caused by trading halts
        pivot_df.ffill(inplace=True)
        # Drops rows at the beginning if some newer stocks didn't exist yet
        pivot_df.dropna(inplace=True) 
        
        return pivot_df
    
    def close(self):
        """Safely closes the database connection."""
        if self.conn:
            self.conn.close()