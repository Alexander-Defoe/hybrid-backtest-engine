import json
from src.data_manager import DataManager

def main():
    print("Initializing Data Ingestion Pipeline...")
    
    # Loads the stock symbols from config.json
    with open('config.json', 'r') as file:
        config = json.load(file)
        
    symbols = config['portfolio']['symbols']
    
    # Initialises the database manager
    db = DataManager()
    
    # Fetches 2 years of market data
    print(f"Fetching historical data for {len(symbols)} symbols...")
    db.update_stock_data(symbols, period="2y")
    db.close()
    
    print("Complete. Database is ready for the C++ engine.")

if __name__ == "__main__":
    main()