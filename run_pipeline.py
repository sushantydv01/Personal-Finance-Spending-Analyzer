import os
from utils.data_loader import process_data, load_data

def run_pipeline():
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    
    clean_csv_path = os.path.join(data_dir, 'transactions_clean.csv')
    messy_csv_path = os.path.join(data_dir, 'transactions_messy.csv')
    
    # Process transactions_clean.csv
    if os.path.exists(clean_csv_path):
        print("=" * 60)
        print("PROCESSING: transactions_clean.csv")
        print("=" * 60)
        raw_df = load_data(clean_csv_path)
        processed_df = process_data(clean_csv_path)
        
        output_path = os.path.join(data_dir, 'transactions_clean_processed.csv')
        processed_df.to_csv(output_path, index=False)
        
        print(f"Raw rows: {len(raw_df)}")
        print(f"Processed rows: {len(processed_df)}")
        print(f"Date range: {processed_df['Date'].min().date()} to {processed_df['Date'].max().date()}")
        print("\nBreakdown of transactions by category:")
        print(processed_df['Category'].value_counts())
        print(f"\nSaved processed data to: {output_path}\n")
    else:
        print(f"Error: {clean_csv_path} does not exist.")
        
    # Process transactions_messy.csv
    if os.path.exists(messy_csv_path):
        print("=" * 60)
        print("PROCESSING: transactions_messy.csv")
        print("=" * 60)
        raw_df = load_data(messy_csv_path)
        processed_df = process_data(messy_csv_path)
        
        output_path = os.path.join(data_dir, 'transactions_messy_processed.csv')
        processed_df.to_csv(output_path, index=False)
        
        print(f"Raw rows: {len(raw_df)}")
        print(f"Processed rows: {len(processed_df)}")
        print(f"Dropped invalid rows: {len(raw_df) - len(processed_df)}")
        print(f"Date range: {processed_df['Date'].min().date()} to {processed_df['Date'].max().date()}")
        print("\nBreakdown of transactions by category:")
        print(processed_df['Category'].value_counts())
        print(f"\nSaved processed data to: {output_path}\n")
    else:
        print(f"Error: {messy_csv_path} does not exist.")

if __name__ == "__main__":
    run_pipeline()
