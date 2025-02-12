#!/usr/bin/env python3

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet

# List of target stock symbols, add other stocks here
# sector 1
# TARGET_SYMBOLS = [
#     "AAPL",  # Apple
#     "MSFT",  # Microsoft
#     "AMZN",  # Amazon
#     "TSLA",  # Tesla
#     "GOOG",  # Alphabet
#     "META",  # Meta
# ]


# sector 2-financial
# TARGET_SYMBOLS = [
#     "JPM",  # JP Morgan Chase & Co.
#     "BX",  # Blackstone Inc.
#     "GS",  # Goldman Sachs Group, Inc. (The)
#     "RJF", #Raymond James Financial, Inc.
#     "V", # Visa Inc.
#     "MA", # Mastercard Incorporated
# ]

# # sector 3-healthcare
# TARGET_SYMBOLS = [
#     "CVS",  # CVS Health Corporation
#     "UNH",  # UnitedHealth Group Incorporated
#     "JNJ",  # Johnson & Johnson
#     "EW",  # Edwards Lifesciences Corporation
#     "GEHC",  # GE HealthCare Technologies Inc.
#     "IDXX",  # IDEXX Laboratories, Inc.
# ]

# sector 3 - communication
TARGET_SYMBOLS = [
    "NFLX",  # Netflix, Inc.
    "TMUS",  # T-Mobile US, Inc.
    "DIS",  # The Walt Disney Company
    "VZ",  # Verizon Communications Inc.
    "LYV",  # Live Nation Entertainment, Inc.
    "FOX",  # Fox Corporation
]

# other sectors?

def load_full_data():
    """
    Loads the CSV file containing all S&P 500 stock data.
    Returns a DataFrame.
    If the file is not found, the script exits.
    """
    csv_path = os.path.join("sp500_stocks", "sp500_stocks.csv")
    if not os.path.exists(csv_path):
        sys.exit(f"[ERROR] CSV file not found at: {csv_path}")

    print(f"[INFO] Loading dataset from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[INFO] DataFrame shape: {df.shape}")
    print(df.head(3))
    return df

def filter_by_symbol(df, symbol):
    """
    Returns only the rows for the specified stock symbol.
    """
    df_symbol = df[df['Symbol'] == symbol].copy()
    if df_symbol.empty:
        print(f"[WARNING] No data found for {symbol}.")
    else:
        print(f"[INFO] {symbol}: {len(df_symbol)} rows found.")
    return df_symbol

def preprocess_data_prophet(df_symbol):
    """
    Prepares the DataFrame in the format required by Prophet:
      - 'ds' (datetime) instead of 'Date'
      - 'y' (value) instead of 'Close'
    """
    # Drop NaN values in the Close column before renaming
    df_symbol = df_symbol.dropna(subset=['Close'])

    # If there are missing values, apply forward-fill
    df_symbol.fillna(method='bfill', inplace=True)  # Fill backward first
    df_symbol.fillna(method='ffill', inplace=True)  # Then fill forward

    # Convert 'Date' column to datetime format
    if 'Date' in df_symbol.columns:
        df_symbol['Date'] = pd.to_datetime(df_symbol['Date'])

    # Sort by date
    df_symbol.sort_values(by='Date', inplace=True)

    # Rename columns for Prophet
    # We only need two columns: ds and y
    # ds = date, y = value to be predicted
    df_prophet = df_symbol[['Date', 'Close']].rename(
        columns={'Date': 'ds', 'Close': 'y'}
    )

    return df_prophet

def prophet_forecast(df_prophet, periods=365*2):
    """
    Trains the Prophet model and generates a forecast for 'periods' days (default: 2 years).
    Returns:
      - forecast: DataFrame containing predictions
      - model: trained Prophet model object
    """
    # Initialize Prophet
    model = Prophet(daily_seasonality=True, yearly_seasonality=True)
    model.fit(df_prophet)

    # Create a DataFrame for future dates
    future = model.make_future_dataframe(periods=periods, freq='D')
    forecast = model.predict(future)

    return forecast, model

def main():
    # 1. Load dataset
    df = load_full_data()

    # 2. Loop through stock symbols
    for symbol in TARGET_SYMBOLS:
        print(f"\n[INFO] Processing symbol: {symbol}")

        df_symbol = filter_by_symbol(df, symbol)
        if df_symbol.empty:
            continue

        # 3. Prepare data in Prophet format
        df_prophet = preprocess_data_prophet(df_symbol)

        # Check if we have enough data
        if len(df_prophet) < 50:
            print(f"[WARNING] {symbol}: insufficient data after preprocessing.")
            continue
        if df_prophet.shape[0] < 2:
            print(f"[ERROR] {symbol}: Not enough valid data for forecasting.")
            continue

        # 4. Train Prophet model and generate a 2-year forecast

        forecast, model = prophet_forecast(df_prophet, periods=365*2)

        print(f"[INFO] Displaying part of the forecast for {symbol}:")
        print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(5))

        # 5. Generate main forecast plot
        fig1 = model.plot(forecast, xlabel='Date', ylabel='Price (Close)')
        fig1.suptitle(f"2-Year Forecast for {symbol}", fontsize=14)
        out_file1 = f"{symbol}_forecast.png"
        fig1.savefig(out_file1)
        print(f"[INFO] Forecast plot saved at: {out_file1}")
        plt.close(fig1)

        # 6. Generate component plots (trend and seasonality)
        fig2 = model.plot_components(forecast)
        fig2.suptitle(f"Forecast Components for {symbol}", fontsize=14)
        out_file2 = f"{symbol}_forecast_components.png"
        fig2.savefig(out_file2)
        print(f"[INFO] Component plot saved at: {out_file2}")
        plt.close(fig2)

# reference: https://www.linkedin.com/pulse/building-llm-driven-stock-price-forecast-prediction-sp-juliano-souza-5nkwf/
if __name__ == "__main__":
    main()


