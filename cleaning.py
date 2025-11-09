import pandas as pd

# Load your NSE500 file (replace with your file path)
df = pd.read_csv("nifty500_list.csv")

# Ensure 'Symbol' column exists
if 'Symbol' not in df.columns:
    raise ValueError(" 'Symbol' column not found in CSV")

# Add .NS suffix
df['Symbol'] = df['Symbol'].astype(str).str.strip() + ".NS"

# Keep only the Symbol column
symbols_df = df[['Symbol']]

# Save to new CSV
symbols_df.to_csv("nse500_symbols.csv", index=False, header=False)

print("✅ File created successfully: nse500_symbols.csv")
print(f"Total symbols: {len(symbols_df)}")
