import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Function to authenticate with Google Sheets
def authenticate_gspread():
    try:
        creds_json = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_json)
        scoped_creds = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(scoped_creds)
        return gc
    except Exception as e:
        st.error(f"Error authenticating with Google Sheets: {e}")
        return None

# Function to read data from a spreadsheet
def get_sheet_data(gc, spreadsheet_id, sheet_name):
    try:
        spreadsheet = gc.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return data
    except Exception as e:
        st.error(f"Error reading data from Google Sheets: {e}")
        return None
