import pandas as pd
import numpy as np
import os

# --- SETUP ---
# Force Python to look in the same folder as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f"Looking for files in: {script_dir}")

# --- CONFIGURATION ---
REVIEW_RATE = 0.5 
AVG_NIGHTS = 3 
MAX_OCCUPANCY = 0.70 

# 1. LOAD DATA
print("Loading data...")
try:
    df = pd.read_csv('listings.csv')
except FileNotFoundError:
    print("Error: 'listings.csv' not found.")
    exit()

# 2. FILTERING
# Keep only entire homes
df = df[df['room_type'] == 'Entire home/apt'].copy()

# 3. CLEANING PRICE
# Fix the "SyntaxWarning" by using r'\$' (raw string)
if 'price' in df.columns:
    df['price_clean'] = df['price'].replace({r'\$': '', ',': ''}, regex=True).astype(float)
else:
    print("Error: 'price' column not found.")
    exit()

# Remove rows with $0 price
df = df[df['price_clean'] > 0]

# 4. ENGINEER FINANCIAL METRICS
df['reviews_per_month'] = df['reviews_per_month'].fillna(0)
df['est_bookings_mo'] = df['reviews_per_month'] / REVIEW_RATE
df['occupancy_rate'] = (df['est_bookings_mo'] * AVG_NIGHTS) / 30
df['occupancy_rate'] = df['occupancy_rate'].clip(upper=MAX_OCCUPANCY)
df['projected_revenue'] = df['price_clean'] * 30 * df['occupancy_rate']

# 5. REMOVE OUTLIERS
price_cap = df['price_clean'].quantile(0.95)
df_clean = df[df['price_clean'] < price_cap]

# 6. AGGREGATE RESULTS
# INTELLIGENT COLUMN SELECTION:
# We check if 'neighbourhood_cleansed' exists; if not, we use 'neighbourhood'
if 'neighbourhood_cleansed' in df_clean.columns:
    group_col = 'neighbourhood_cleansed'
elif 'neighbourhood' in df_clean.columns:
    group_col = 'neighbourhood'
else:
    print("Error: Could not find a neighborhood column. Please check your CSV.")
    exit()

print(f"Grouping data by: {group_col}")

neighborhood_stats = df_clean.groupby(group_col).agg({
    'price_clean': 'mean',
    'projected_revenue': 'mean',
    'occupancy_rate': 'mean',
    'id': 'count'
}).reset_index()

# Rename columns for the final report
neighborhood_stats.columns = ['Neighborhood', 'Avg_Nightly_Price', 'Avg_Monthly_Revenue', 'Avg_Occupancy', 'Listing_Count']

# Filter for relevant neighborhoods (at least 20 listings)
neighborhood_stats = neighborhood_stats[neighborhood_stats['Listing_Count'] > 20]
neighborhood_stats = neighborhood_stats.sort_values(by='Avg_Monthly_Revenue', ascending=False)

# 7. EXPORT
print("Success! Exporting data to 'investor_analysis_nashville.csv'...")
df_clean.to_csv('investor_analysis_nashville.csv', index=False)
print("Done. You can now open 'investor_analysis_nashville.csv' in Tableau.")