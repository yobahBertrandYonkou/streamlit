import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO
import os
import base64
# import yaml
import zipfile
from utils.TimeSeriesForecast import TimeSeriesForecast  # Your forecasting backend class
from PIL import Image
import markdown_content as mc

# Load configuration file
# with open("config.yaml", "r") as f:
#     config = yaml.safe_load(f)

# Assign variables from the configuration
# project_name = config["project_name"]
# sidebar_title = config["sidebar_title"]
preloaded_file = "utils/ReceivedBilledVolumesData.xlsx"  # Preloaded Excel file

# Set up page configuration
st.set_page_config(
    page_title=project_name,
    page_icon="🧊",
    layout="wide",
)

st.markdown("""
    <style>
    .stButton button {
        width: 40%;
        height: 35px;
        font-size: 16px;
        margin: 5px auto;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

# Apply markdown content
st.markdown(mc.sidebar_markdown, unsafe_allow_html=True)
st.markdown(mc.main_container_css, unsafe_allow_html=True)
st.markdown(mc.layout_css, unsafe_allow_html=True)

# Load and display the logo
# image = Image.open("Firstsource-logo.png")
# buffered = BytesIO()
# image.save(buffered, format="PNG")
# img_str = base64.b64encode(buffered.getvalue()).decode()
# st.markdown(mc.generate_title_image_markdown(img_str, project_name), unsafe_allow_html=True)

# Creating only a tab for Project Details
# Create a separate tab for "About Application"
app_tab, about_tab = st.tabs(["Output","About Application"])
# Project Details tab
with about_tab:
    #st.markdown("### Project Details")
    st.markdown("""
    **Revenue Forecasting Application**

    This application helps forecast revenue and other key performance indicators based on the input data you provide. You can input your data weekly or upload historical data, and the system will generate forecasts for 30, 60, and 90-day periods.

    **Features**
    - **Input weekly data:** You can input key performance indicators such as Billed Volumes, Received Volumes, Revenue, Number of Audits, and Depletion Rate, Using Add weekly data and forecast tab.
    - **Upload historical data:** Upload your historical data using Monthly Forecasting tab and the system will generate forecasts for 30, 60, and 90 days.
    - **Generate forecast:** You can generate forecasts based on your data and review the forecasted data.
    - **Download forecasted data:** Download the forecasted data in CSV format.

    **Input Fields**
    - **Week Date:** Date for the start of each week.
    - **Billed Volumes:** The total billed volumes for the week.
    - **Received Volumes:** The total received volumes for the week.
    - **Revenue:** The total revenue for the week.
    - **Number of Audits:** The total number of audits conducted for the week.
    - **Depletion Rate:** The depletion rate for the week.
    """)
    # Initialize session state for user input data and input fields
    if 'user_input_df' not in st.session_state:
        st.session_state['user_input_df'] = pd.DataFrame()

    if 'input_fields' not in st.session_state:
        st.session_state['input_fields'] = {
            'weeks_to_input': 1,  # Default to 1 week
            'billed_volumes': [],
            'received_volumes': [],
            'revenue': [],
            'week_date': [],
            'No_Of_Audits':[],
            'Depletion Rate':[]
        }

    # Helper function to reset input fields
    def reset_input_fields():
        st.session_state['input_fields'] = {
            'weeks_to_input': 1,
            'billed_volumes': [],
            'received_volumes': [],
            'revenue': [],
            'week_date': [],
            'No_Of_Audits':[],
            'Depletion Rate':[]
        }

    # Helper function to convert DataFrame to CSV
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    # Helper function to replace or append new data to the preloaded file
    def replace_or_append_to_excel(file_path, new_data):
        existing_df = pd.read_excel(file_path)
        existing_df.set_index('Date', inplace=True)
        new_data.set_index('Date', inplace=True)

        # Replace rows with new data if dates overlap, otherwise append
        existing_df.update(new_data)  # This replaces the overlapping data
        updated_df = pd.concat([existing_df, new_data[~new_data.index.isin(existing_df.index)]])  # Append non-overlapping data

        updated_df.reset_index(inplace=True)
        updated_df.to_excel(file_path, index=False)

    # Load preloaded data
    @st.cache_data
    def load_preloaded_data():
        return pd.read_excel(preloaded_file)

with app_tab:
    # Sidebar content
    with st.sidebar:
        #st.header(sidebar_title)
        st.header(sidebar_title,divider="rainbow")
        
        # Add the Download Sample Data button for the 'Employee_RAG_Details.xlsx' file
        st.subheader("Download Sample Data")

        # Load the sample Excel file
        sample_file_path = "ReceivedBilledVolumesData.xlsx"

        @st.cache_data
        def load_sample_file(file_path):
            return pd.read_excel(file_path)

        # Load the sample data
        sample_df = load_sample_file(sample_file_path)

        # Convert the sample file to a downloadable format (e.g., Excel format)
        def convert_df_to_excel(df):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='SampleData')
            writer.save()
            processed_data = output.getvalue()
            return processed_data

        excel_data = convert_df_to_excel(sample_df)

        # Add the download button for the sample file
        st.download_button(
            label="Download Sample Data",
            data=excel_data,
            file_name="Sample_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Now add the radio button for the tab selection (Monthly Forecasting, Add Weekly Data and Forecast)
        tab = st.radio("Choose an option", ["Monthly Forecasting", "Add Weekly Data and Forecast"])
        
        # File uploader for uploading files
        uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=["xlsx", "csv"], key="file_upload_1")


    def format_forecast_results(forecast, num_days):
        if forecast is None:
            st.error("Error: Forecast is not available.")
            return None
        
        # Ensure 'Date' is part of the forecast DataFrame
        if 'Date' not in forecast.columns:
            st.error("Error: 'Date' column is missing in the forecast data.")
            return None

        # For 30-Day Forecast: Show the last row without 'Total'
        if num_days == 30:
            forecast = forecast.tail(1)
        
        # For 60-Day and 90-Day Forecast: Replace 'Total' with the last forecasted date
        else:
            forecast['Date'] = pd.to_datetime(forecast['Date'])  # Ensure Date is in datetime format
            forecast = forecast.tail(1)  # Show only the last row

        return forecast

    # Helper function to create a ZIP file of forecast CSVs
    def zip_forecast_files(files):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_name, data in files.items():
                zf.writestr(file_name, data)
        buffer.seek(0)
        return buffer

    # Preloaded Excel file for "Add Weekly Data and Forecast"
    if tab == "Add Weekly Data and Forecast":
        # Load preloaded data from the Excel file
        dataframe = load_preloaded_data()
        #st.write("Preloaded data loaded from the file.")

        # Detect the last date available in the file
        last_date = pd.to_datetime(dataframe['Date']).max()
        st.write(f"Last date available in the data: {last_date.strftime('%Y-%m-%d')}")

        # Ask user how many weeks of data they want to input
        st.subheader("Input Weekly Data for the Next Month")
        
        # Number of weeks input
        weeks_to_input = st.number_input("How many weeks of data do you want to input?", min_value=1, step=1, value=st.session_state['input_fields']['weeks_to_input'], help="Enter the number of weeks you would like to input data for the upcoming month.")
        st.session_state['input_fields']['weeks_to_input'] = weeks_to_input

        # Initialize empty list to collect user inputs
        user_data = []

        # Create input fields for each week's data
        for i in range(weeks_to_input):
            st.subheader(f"Week {i + 1} Data")

            # Use session state to maintain and reset values
            week_date = st.date_input(f"Date for Week {i + 1}", last_date + timedelta(days=(i+1)*7), key=f"week_date_{i}", help="Select the start date for this week's data.")
            billed_volumes = st.number_input(f"Billed Volumes for Week {i + 1}", min_value=0.0, step=1.0, key=f"billed_volumes_{i}", help="Enter the billed volumes for this week.")
            received_volumes = st.number_input(f"Received Volumes for Week {i + 1}", min_value=0.0, step=1.0, key=f"received_volumes_{i}", help="Enter the received volumes for this week.")
            revenue = st.number_input(f"Revenue for Week {i + 1}", min_value=0.0, step=1.0, key=f"revenue_{i}", help="Enter the revenue for this week.")
            no_of_audits = st.number_input(f"Number of audits for week {i + 1}", min_value=0.0, step=1.0, key=f"no_of_audits_{i}", help="Enter the no of audits for this week.")
            depletion_rate = st.number_input(f"Depletion Rate for week {i + 1}", min_value=0.0, step=1.0, key=f"depletion_rate_{i}", help="Enter the depletion rate for this week.")
            # Collect all user inputs for the week
            user_data.append([week_date, billed_volumes, received_volumes, revenue, no_of_audits, depletion_rate])

        st.write("""
            After you have entered the correct weekly data, click the **Load Data** button below. 
            """)

        # Button to Load and Save the input data to the preloaded file
        if st.button("Load Data"):
            # Convert user input to DataFrame
            user_df = pd.DataFrame(user_data, columns=['Date', 'Billed Volumes', 'Received Volumes', 'Revenue','No_Of_Audits','Depletion Rate'])
            user_df['Date'] = pd.to_datetime(user_df['Date'])  # Convert date to datetime format

            # Replace or append the new data to session state and preloaded file
            st.session_state['user_input_df'] = pd.concat([st.session_state['user_input_df'], user_df])
            replace_or_append_to_excel(preloaded_file, user_df)
            st.success("Weekly data has been saved in the preloaded file!")

        forecast_files = {}

        # Separate button to run the forecasts
        if st.button("Generate Forecast"):
            # Combine user input with the existing dataframe
            combined_df = pd.concat([dataframe, st.session_state['user_input_df']])

            # Run forecasts with the combined data
            forecast_model = TimeSeriesForecast(combined_df)

            # 30-Day Forecast
            st.subheader("30-Day Forecast")
            forecast_30 = forecast_model.run_forecast(30)
            forecast_30 = format_forecast_results(forecast_30, 30)

            if forecast_30 is not None:  # Ensure forecast is not None
                st.dataframe(forecast_30.replace(0, np.nan).dropna(axis=1, how="all"))
                # Download button for the 30-day forecast
                csv_30 = convert_df(forecast_30)
                forecast_files["30DayForecast.csv"] = csv_30
            else:
                st.warning("No forecast could be generated for 30 days.")

            # 60-Day Forecast
            st.subheader("60-Day Forecast")
            forecast_60 = forecast_model.run_forecast(60)
            forecast_60 = format_forecast_results(forecast_60, 60)

            if forecast_60 is not None:
                st.dataframe(forecast_60.replace(0, np.nan).dropna(axis=1, how="all"))
                # Download button for the 60-day forecast
                csv_60 = convert_df(forecast_60)
                forecast_files["60DayForecast.csv"] = csv_60
            else:
                st.warning("No forecast could be generated for 60 days.")

            # 90-Day Forecast
            st.subheader("90-Day Forecast")
            forecast_90 = forecast_model.run_forecast(90)
            forecast_90 = format_forecast_results(forecast_90, 90)

            if forecast_90 is not None:
                st.dataframe(forecast_90.replace(0, np.nan).dropna(axis=1, how="all"))
                # Download button for the 90-day forecast
                csv_90 = convert_df(forecast_90)
                forecast_files["90DayForecast.csv"] = csv_90
            else:
                st.warning("No forecast could be generated for 90 days.")

        # Generate and offer ZIP download button if there are files
        if forecast_files:
            zip_file = zip_forecast_files(forecast_files)
            st.download_button("Download All Forecasts", zip_file, "Forecasts.zip", "application/zip")

        # Clear Input Fields button
        if st.button("Clear Input Fields"):
            # Call the reset function to clear the inputs
            reset_input_fields()
            st.success("Input fields have been cleared. You can re-enter data.")


    # For "Monthly Forecasting", user uploads a file
    elif tab == "Monthly Forecasting":
        forecast_files = {}
        if uploaded_file:
            try:
                # Load the uploaded file
                if uploaded_file.name.endswith(".csv"):
                    dataframe = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith(".xlsx"):
                    dataframe = pd.read_excel(uploaded_file)
                else:
                    st.error("Invalid file type. Please upload a CSV or Excel file.")
                    dataframe = None

                if dataframe is not None:
                    st.write("File uploaded successfully!")
                    # Instantiate the TimeSeriesForecast class
                    forecast_model = TimeSeriesForecast(dataframe)

                    # Perform 30-Day Forecast
                    st.subheader("30-Day Forecast")
                    forecast_30 = forecast_model.run_forecast(30)
                    forecast_30 = format_forecast_results(forecast_30, 30)
                    st.dataframe(forecast_30.replace(0, np.nan).dropna(axis=1, how="all"))
                    csv_30 = convert_df(forecast_30)
                    forecast_files["30DayForecast.csv"] = csv_30

                    # Perform 60-Day Forecast
                    st.subheader("60-Day Forecast")
                    forecast_60 = forecast_model.run_forecast(60)
                    forecast_60 = format_forecast_results(forecast_60, 60)
                    st.dataframe(forecast_60.replace(0, np.nan).dropna(axis=1, how="all"))
                    csv_60 = convert_df(forecast_60)
                    forecast_files["60DayForecast.csv"] = csv_60

                    # Perform 90-Day Forecast
                    st.subheader("90-Day Forecast")
                    forecast_90 = forecast_model.run_forecast(90)
                    forecast_90 = format_forecast_results(forecast_90, 90)
                    st.dataframe(forecast_90.replace(0, np.nan).dropna(axis=1, how="all"))
                    csv_90 = convert_df(forecast_90)
                    forecast_files["90DayForecast.csv"] = csv_90

                    # Generate and offer ZIP download button if there are files
                    if forecast_files:
                        zip_file = zip_forecast_files(forecast_files)
                        st.download_button("Download All Forecasts", zip_file, "Forecasts.zip", "application/zip")

            except Exception as e:
                st.error(f"Error processing file: {e}")
