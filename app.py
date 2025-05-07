import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
import io

st.set_page_config(page_title="Golf Tournament CSV Cleaner", layout="wide")

st.title("Golf Tournament CSV Cleaner")
st.write("Upload your golf tournament CSV files to clean and standardize the data.")

# Required columns
REQUIRED_COLUMNS = ["Date", "Name", "Course", "Category", "City", "State", "Zip"]

def standardize_date(date_str):
    """Convert various date formats to YYYY-MM-DD format."""
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    # Try different date formats
    date_formats = [
        '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%Y/%m/%d',
        '%m/%d/%y', '%m-%d-%y', '%d/%m/%Y', '%d-%m-%Y',
        '%B %d, %Y', '%b %d, %Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
            
    # If none of the formats work, try to extract date using regex
    date_pattern = r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})'
    match = re.search(date_pattern, date_str)
    if match:
        month, day, year = match.groups()
        if len(year) == 2:
            year = f"20{year}" if int(year) < 50 else f"19{year}"
        try:
            return datetime(int(year), int(month), int(day)).strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    return date_str

def standardize_state(state_str):
    """Convert state names to two-letter abbreviations."""
    if pd.isna(state_str):
        return None
        
    state_str = str(state_str).strip().upper()
    
    # Dictionary of state names to abbreviations
    state_dict = {
        'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR',
        'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
        'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID',
        'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
        'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
        'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
        'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
        'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY',
        'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK',
        'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
        'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
        'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV',
        'WISCONSIN': 'WI', 'WYOMING': 'WY', 'DISTRICT OF COLUMBIA': 'DC'
    }
    
    # If already an abbreviation
    if len(state_str) == 2:
        return state_str
    
    # If it's a full state name
    return state_dict.get(state_str, state_str)

def standardize_zip(zip_str):
    """Standardize ZIP code format."""
    if pd.isna(zip_str):
        return None
    
    zip_str = str(zip_str).strip()
    
    # Extract 5-digit zip code
    zip_pattern = r'(\d{5})(?:-\d{4})?'
    match = re.search(zip_pattern, zip_str)
    if match:
        return match.group(1)
    
    return zip_str

def extract_location_data(df):
    """Attempt to extract city, state, zip from location columns."""
    # Look for columns that might contain location information
    location_cols = [col for col in df.columns if any(x in col.lower() for x in ['location', 'address', 'city', 'state', 'zip'])]
    
    if not location_cols:
        return df
    
    # Try to extract city, state, zip from location columns
    for col in location_cols:
        if 'city' not in df.columns.str.lower() and 'city' in col.lower():
            df['City'] = df[col]
        elif 'state' not in df.columns.str.lower() and 'state' in col.lower():
            df['State'] = df[col].apply(standardize_state)
        elif 'zip' not in df.columns.str.lower() and 'zip' in col.lower():
            df['Zip'] = df[col].apply(standardize_zip)
        elif 'location' in col.lower() or 'address' in col.lower():
            # Try to extract city, state, zip from location/address column
            if 'City' not in df.columns:
                df['City'] = df[col].str.extract(r'([A-Za-z\s]+),')
            if 'State' not in df.columns:
                df['State'] = df[col].str.extract(r',\s*([A-Za-z]{2})')
                df['State'] = df['State'].apply(standardize_state)
            if 'Zip' not in df.columns:
                df['Zip'] = df[col].str.extract(r'(\d{5}(?:-\d{4})?)')
                df['Zip'] = df['Zip'].apply(standardize_zip)
    
    return df

def clean_golf_data(df):
    """Clean and standardize golf tournament data."""
    # Make a copy to avoid modifying the original
    cleaned_df = df.copy()
    
    # Standardize column names (capitalization and whitespace)
    cleaned_df.columns = [col.strip().title() for col in cleaned_df.columns]
    
    # Map similar column names to required column names
    column_mapping = {
        'Tournament': 'Name',
        'Tournament Name': 'Name',
        'Event': 'Name',
        'Event Name': 'Name',
        'Golf Course': 'Course',
        'Course Name': 'Course',
        'Type': 'Category',
        'Tournament Type': 'Category',
        'Event Type': 'Category',
        'Tournament Date': 'Date',
        'Event Date': 'Date',
        'Zip Code': 'Zip',
        'Zipcode': 'Zip',
        'Postal Code': 'Zip',
        'St': 'State',
        'Location': 'City'
    }
    
    # Rename columns based on mapping
    for old_col, new_col in column_mapping.items():
        if old_col in cleaned_df.columns and new_col not in cleaned_df.columns:
            cleaned_df.rename(columns={old_col: new_col}, inplace=True)
    
    # Ensure required columns exist, create if missing
    for col in REQUIRED_COLUMNS:
        if col not in cleaned_df.columns:
            cleaned_df[col] = None
    
    # Try to extract location data
    cleaned_df = extract_location_data(cleaned_df)
    
    # Standardize date format
    if 'Date' in cleaned_df.columns:
        cleaned_df['Date'] = cleaned_df['Date'].apply(standardize_date)
    
    # Standardize state abbreviations
    if 'State' in cleaned_df.columns:
        cleaned_df['State'] = cleaned_df['State'].apply(standardize_state)
    
    # Standardize ZIP codes
    if 'Zip' in cleaned_df.columns:
        cleaned_df['Zip'] = cleaned_df['Zip'].apply(standardize_zip)
    
    # Remove any empty rows
    cleaned_df = cleaned_df.dropna(how='all')
    
    # Reorder columns to put required columns first
    all_columns = REQUIRED_COLUMNS + [col for col in cleaned_df.columns if col not in REQUIRED_COLUMNS]
    cleaned_df = cleaned_df[all_columns]
    
    return cleaned_df

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read the CSV file
    try:
        df = pd.read_csv(uploaded_file)
        
        # Display original data
        st.subheader("Original Data")
        st.dataframe(df)
        
        # Clean the data
        cleaned_df = clean_golf_data(df)
        
        # Display cleaned data
        st.subheader("Cleaned Data")
        st.dataframe(cleaned_df)
        
        # Show which columns were missing and added
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            st.warning(f"Added missing columns: {', '.join(missing_cols)}")
        
        # Create a download button for the cleaned data
        csv = cleaned_df.to_csv(index=False)
        st.download_button(
            label="Download Cleaned Data",
            data=csv,
            file_name="cleaned_golf_tournaments.csv",
            mime="text/csv"
        )
        
        # Display analysis of the data
        st.subheader("Data Analysis")
        
        # Count tournaments by category
        if cleaned_df['Category'].notna().any():
            st.write("Tournament Count by Category")
            category_counts = cleaned_df['Category'].value_counts()
            st.bar_chart(category_counts)
        
        # Count tournaments by state
        if cleaned_df['State'].notna().any():
            st.write("Tournament Count by State")
            state_counts = cleaned_df['State'].value_counts()
            st.bar_chart(state_counts)
        
        # Count tournaments by month (if dates are available)
        if cleaned_df['Date'].notna().any():
            try:
                cleaned_df['Month'] = pd.to_datetime(cleaned_df['Date']).dt.strftime('%B')
                st.write("Tournament Count by Month")
                month_counts = cleaned_df['Month'].value_counts()
                st.bar_chart(month_counts)
            except:
                st.write("Could not analyze tournament count by month due to date format issues.")
        
    except Exception as e:
        st.error(f"Error: {e}")
        st.write("Please ensure your CSV file is properly formatted.")

# Sidebar with instructions
with st.sidebar:
    st.header("Instructions")
    st.write("""
    1. Upload a CSV file containing golf tournament data.
    2. The app will automatically clean and standardize the data.
    3. Required columns will be identified or created:
       - Date
       - Name
       - Course
       - Category
       - City
       - State
       - Zip
    4. Download the cleaned data as a CSV file.
    """)
    
    st.header("Data Processing")
    st.write("""
    This app performs the following:
    
    - Standardizes date formats to YYYY-MM-DD
    - Converts state names to two-letter abbreviations
    - Standardizes ZIP codes to 5-digit format
    - Extracts location data from address fields
    - Maps similar column names to required columns
    - Reorders columns with required columns first
    """)
