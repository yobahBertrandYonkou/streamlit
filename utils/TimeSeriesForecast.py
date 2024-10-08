import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.varmax import VARMAX
from statsmodels.tsa.api import VAR
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


class TimeSeriesForecast:
    def __init__(self, df):
        """Initialize the class with a pre-loaded DataFrame."""
        self.df = df

        # Ensure Date is in datetime format and find the last available date
        self.df['Date'] = pd.to_datetime(self.df['Date'])  # Ensure 'Date' column is datetime
        self.lastDateTimestamp = self.df['Date'].max()  # Last date in the data
        self.lastDate = self.lastDateTimestamp.strftime('%Y-%m-%d')

        # Copy only the columns needed for forecasting and convert to float64
        self.df_copy = self.df[['Billed Volumes', 'Received Volumes', 'Revenue','No_Of_Audits','Depletion Rate']].copy()
        self.df_copy.index = pd.to_datetime(self.df['Date'])
        self.df_copy = self.df_copy.astype('float64')  # Convert all columns to float64 to avoid dtype mismatch

    def get_next_x_weeks(self, start_date, num_weeks):
        """Generate the next x weeks from the start_date."""
        date_format = "%Y-%m-%d"
        current_date = datetime.strptime(start_date, date_format)

        next_weeks = []
        for _ in range(num_weeks):
            next_week = current_date + timedelta(days=7)
            next_weeks.append(next_week.strftime(date_format))
            current_date = next_week

        return next_weeks

    def append_forecast_dates(self, num_weeks):
        """Append new forecast dates to the dataframe for the specified number of weeks."""
        next_weeks = self.get_next_x_weeks(self.lastDate, num_weeks)
        datesList = pd.to_datetime(next_weeks)  # Ensure dates are datetime objects
        self.df_forecast = pd.DataFrame(index=datesList, columns=self.df_copy.columns)
        self.df_forecast.index.name = 'Date'
        self.df = pd.concat([self.df_copy, self.df_forecast])
        print(f"Appended forecast dates for {num_weeks} weeks.")

    def clean_data(self, df):
        """Clean the dataframe by replacing infinities and dropping NaNs."""
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        return df

    def run_adfuller_tests(self, train_df):
        """Placeholder for ADF stationarity test."""
        pass  # In case this is needed, you can add ADF test logic

    def run_forecast(self, num_days):
        try:
            # Adjust the number of weeks based on the input days (30, 60, 90 days)
            if num_days == 30:
                num_weeks = 5  # Approx 30 days ~ 4 weeks
            elif num_days == 60:
                num_weeks = 9  # Approx 60 days ~ 8 weeks
            elif num_days == 90:
                num_weeks = 13  # Approx 90 days ~ 12 weeks

            self.append_forecast_dates(num_weeks)
            self.df = self.df.astype(float)

            nobs = num_weeks
            train_df = self.df.iloc[:-nobs]
            test_df = self.df.iloc[-nobs:]

            self.run_adfuller_tests(train_df)
            df_diff = train_df.diff().dropna()

            # Fit the VARMAX model using all columns
            var_model = VARMAX(train_df, order=(1, 0), enforce_stationarity=True)
            fitted_model = var_model.fit(disp=False)

            # Generate predictions
            n_forecast = len(test_df)
            predict = fitted_model.get_prediction(start=len(train_df), end=len(train_df) + n_forecast - 1)
            predictions = predict.predicted_mean

            # Forecasted Data will have all columns. Rename forecasted columns accordingly.
            forecast_columns = [f"{col}_forecast" for col in self.df_copy.columns]
            predictions.columns = forecast_columns
            predictions.index.name = 'Date'

            # Concatenate predictions with the original data
            df_res = pd.concat([self.df_copy, predictions])

            # Group by month and sum the forecasts for each month
            monthly_forecast = df_res.resample('M').sum()

            # Ensure the forecast has a 'Date' column
            monthly_forecast.index.name = 'Date'  # Ensure 'Date' is set as index name

            # Reset index to ensure 'Date' column is present
            forecasted_values = monthly_forecast.loc[monthly_forecast.index >= self.df_forecast.index.min()].reset_index()

            # Aggregate totals for 60-Day and 90-Day forecasts
            if num_days > 30:
                # Calculate total for 2 months (60 days) or 3 months (90 days)
                last_date = forecasted_values['Date'].max()  # Get the last date of the forecast range
                aggregated_total = forecasted_values.sum(numeric_only=True).to_frame().T
                aggregated_total['Date'] = last_date  # Set the 'Date' as the last date of the range

                # Return only the necessary columns ('Billed Volumes', 'Received Volumes', 'Revenue')
                return aggregated_total[['Date', 'Billed Volumes_forecast', 'Received Volumes_forecast', 'Revenue_forecast']]

            # Return the monthly forecasted values but display only the necessary columns
            return forecasted_values[['Date', 'Billed Volumes_forecast', 'Received Volumes_forecast', 'Revenue_forecast']]
        except Exception as e:
            print(f"Error during forecasting: {e}")
            return None
