import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
import io
import importlib.util
import sys

# Check for required dependencies
def check_dependencies():
    missing_deps = []
    for package in ['openpyxl', 'xlsxwriter']:
        if importlib.util.find_spec(package) is None:
            missing_deps.append(package)
    return missing_deps

# Display dependency installation instructions if needed
missing_dependencies = check_dependencies()
if missing_dependencies:
    st.error(f"Missing required dependencies: {', '.join(missing_dependencies)}")
    st.write("""
    ### Installation Instructions:
    
    Please install the missing dependencies by running the following command in your terminal:
    ```
    pip install {0}
    ```
    
    Then restart the Streamlit app.
    """.format(' '.join(missing_dependencies)))
    st.stop()

st.set_page_config(page_title="Golf Tournament Data Cleaner", layout="wide")

st.title("Golf Tournament Data Cleaner")
st.write("Upload your golf tournament Excel files to clean and standardize the data.")

# Required columns
REQUIRED_COLUMNS = ["Date", "Name", "Course", "Category", "City", "State", "Zip"]

def standardize_date(date_val):
    """Convert various date formats to YYYY-MM-DD format."""
    if pd.isna(date_val):
        return None
    
    # If already a datetime object (Excel dates are often parsed as datetime)
    if isinstance(date_val, (datetime, pd.Timestamp)):
        return date_val.strftime('%Y-%m-%d')
    
    date_str = str(date_val).strip()
    
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

def extract_location_from_col(df, col):
    """Extract city, state, zip from a single column."""
    # Try to extract city, state, zip from a location column
    # Pattern: "City, ST ZIPCODE" or "City, State ZIPCODE"
    location_pattern = r'([^,]+),\s*([A-Za-z]{2}|\w+)\s+(\d{5}(?:-\d{4})?)?'
    
    if col not in df.columns:
        return df
    
    # Apply extraction where possible
    mask = df[col].notna()
    if mask.any():
        matches = df.loc[mask, col].astype(str).str.extract(location_pattern)
        
        if matches is not None and not matches.empty:
            # City (first group)
            if 'City' not in df.columns and not matches[0].isna().all():
                df.loc[mask, 'City'] = matches[0]
            
            # State (second group)
            if 'State' not in df.columns and not matches[1].isna().all():
                df.loc[mask, 'State'] = matches[1].apply(standardize_state)
            
            # Zip (third group)
            if 'Zip' not in df.columns and not matches[2].isna().all():
                df.loc[mask, 'Zip'] = matches[2].apply(standardize_zip)
    
    return df

def detect_tournament_groups(df):
    """Attempt to detect tournament groups in the data."""
    # Check if there are empty rows that might separate tournament groups
    empty_rows = df.isna().all(axis=1)
    if empty_rows.any():
        # Use empty rows as separators
        group_indices = np.where(empty_rows)[0]
        
        # Create a list to hold tournament groups
        tournament_groups = []
        
        # Extract each group
        start_idx = 0
        for end_idx in group_indices:
            if end_idx > start_idx:  # Ensure there's actual data
                group_df = df.iloc[start_idx:end_idx].reset_index(drop=True)
                if not group_df.empty:
                    tournament_groups.append(group_df)
            start_idx = end_idx + 1
        
        # Don't forget the last group
        if start_idx < len(df):
            group_df = df.iloc[start_idx:].reset_index(drop=True)
            if not group_df.empty:
                tournament_groups.append(group_df)
        
        return tournament_groups
    
    # If no empty rows, check if there's a 'Tournament' or 'Name' column
    # that might indicate different tournaments
    for col in ['Tournament', 'Name', 'Event']:
        if col in df.columns:
            if not df[col].isna().all():
                # Group by tournament name
                grouped = df.groupby(col, dropna=False)
                return [group.reset_index(drop=True) for _, group in grouped]
    
    # If we can't detect groups, return the entire DataFrame as one group
    return [df]

def extract_tournament_info(group_df):
    """Extract tournament info from a group of rows."""
    # Initialize a dictionary to hold tournament info
    tournament_info = {col: None for col in REQUIRED_COLUMNS}
    
    # Function to normalize column names for matching
    def normalize_col(col):
        return col.lower().replace(' ', '_')
    
    # Map of normalized column names to required columns
    col_mapping = {
        'tournament': 'Name', 'event': 'Name', 
        'tournament_name': 'Name', 'event_name': 'Name',
        'golf_course': 'Course', 'course_name': 'Course', 
        'tournament_type': 'Category', 'event_type': 'Category', 'type': 'Category',
        'tournament_date': 'Date', 'event_date': 'Date',
        'zip_code': 'Zip', 'zipcode': 'Zip', 'postal_code': 'Zip',
        'st': 'State', 'location': 'City'
    }
    
    # First, try to find values in column headers and first row
    if not group_df.empty:
        # Check for column structures like "Name | Value"
        for col in group_df.columns:
            if ':' in str(col) or '|' in str(col):
                parts = re.split(r'[:|]', str(col))
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    # Map to required column if possible
                    for req_col in REQUIRED_COLUMNS:
                        if req_col.lower() in key.lower():
                            tournament_info[req_col] = value
                            break
        
        # Map columns to required columns
        for col in group_df.columns:
            norm_col = normalize_col(str(col))
            if norm_col in col_mapping and tournament_info[col_mapping[norm_col]] is None:
                # Find the first non-NaN value in this column
                non_nan_values = group_df[col].dropna()
                if not non_nan_values.empty:
                    tournament_info[col_mapping[norm_col]] = non_nan_values.iloc[0]
            
            # Direct match with required columns
            for req_col in REQUIRED_COLUMNS:
                if req_col.lower() == norm_col and tournament_info[req_col] is None:
                    non_nan_values = group_df[col].dropna()
                    if not non_nan_values.empty:
                        tournament_info[req_col] = non_nan_values.iloc[0]
        
        # Look for key-value pairs in the data
        for idx, row in group_df.iterrows():
            for col in group_df.columns:
                cell_value = row[col]
                if pd.notna(cell_value):
                    cell_str = str(cell_value).strip()
                    
                    # Check for "Key: Value" or "Key | Value" format
                    patterns = [r'^(.*?):\s*(.*)$', r'^(.*?)\|\s*(.*)$']
                    for pattern in patterns:
                        match = re.match(pattern, cell_str)
                        if match:
                            key, value = match.groups()
                            key = key.strip()
                            value = value.strip()
                            
                            # Map to required column if possible
                            for req_col in REQUIRED_COLUMNS:
                                if req_col.lower() in key.lower():
                                    tournament_info[req_col] = value
                                    break
        
        # Try to extract location data
        location_cols = ['Location', 'Address', 'Venue']
        for col in location_cols:
            if col in group_df.columns:
                # Extract city, state, zip from location column
                tmp_df = pd.DataFrame([tournament_info])
                tmp_df[col] = group_df[col].dropna().iloc[0] if not group_df[col].dropna().empty else None
                tmp_df = extract_location_from_col(tmp_df, col)
                
                # Update tournament info with extracted data
                for field in ['City', 'State', 'Zip']:
                    if tournament_info[field] is None and field in tmp_df.columns:
                        tournament_info[field] = tmp_df[field].iloc[0]
    
    # Standardize values
    if tournament_info['Date'] is not None:
        tournament_info['Date'] = standardize_date(tournament_info['Date'])
    if tournament_info['State'] is not None:
        tournament_info['State'] = standardize_state(tournament_info['State'])
    if tournament_info['Zip'] is not None:
        tournament_info['Zip'] = standardize_zip(tournament_info['Zip'])
    
    return tournament_info

def process_excel_file(file):
    """Process an Excel file and extract tournament information."""
    try:
        # Read all sheets
        xls = pd.ExcelFile(file)
        sheet_names = xls.sheet_names
        
        all_tournaments = []
        
        for sheet_name in sheet_names:
            # Read the sheet
            df = pd.read_excel(file, sheet_name=sheet_name, header=None)
            
            # Try to detect if there's a header row
            potential_header_row = df.iloc[0]
            if potential_header_row.astype(str).str.contains('|').any() or potential_header_row.astype(str).str.contains(':').any():
                # This might be a header row with column names
                df = pd.read_excel(file, sheet_name=sheet_name)
            else:
                # Try to detect header based on data types
                # Assuming headers are typically strings while data can be mixed
                header_candidates = []
                for i in range(min(5, len(df))):
                    row = df.iloc[i]
                    if row.apply(lambda x: isinstance(x, str)).mean() > 0.7:  # If >70% of columns are strings
                        header_candidates.append(i)
                
                if header_candidates:
                    # Use the last candidate as header (often headers span multiple rows)
                    header_row = max(header_candidates)
                    df = pd.read_excel(file, sheet_name=sheet_name, header=header_row)
                else:
                    # No clear header, keep as is
                    pass
            
            # Detect tournament groups
            groups = detect_tournament_groups(df)
            
            # Process each group
            for group_df in groups:
                tournament_info = extract_tournament_info(group_df)
                all_tournaments.append(tournament_info)
        
        # Convert to DataFrame
        tournaments_df = pd.DataFrame(all_tournaments)
        
        # Filter out rows where all required columns are None/NaN
        tournaments_df = tournaments_df.dropna(subset=REQUIRED_COLUMNS, how='all')
        
        return tournaments_df
    
    except Exception as e:
        st.error(f"Error processing Excel file: {str(e)}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

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
    
    # Try to extract location data from combined fields
    for col in cleaned_df.columns:
        if any(loc_key in col.lower() for loc_key in ['location', 'address', 'venue']):
            cleaned_df = extract_location_from_col(cleaned_df, col)
    
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

# Manual entry for filling missing data
def manual_entry_form(df):
    """Form for manually entering missing data."""
    st.subheader("Fill Missing Data")
    
    # Check which required columns have missing data
    missing_data = {col: df[col].isna().sum() for col in REQUIRED_COLUMNS}
    missing_cols = [col for col, count in missing_data.items() if count > 0]
    
    if not missing_cols:
        st.success("All required data is present!")
        return df
    
    st.write("Some required data is missing. Please fill in the missing information:")
    
    # Create tabs for editing each row with missing data
    rows_with_missing = df[df[missing_cols].isna().any(axis=1)]
    
    if not rows_with_missing.empty:
        tabs = st.tabs([f"Tournament {i+1}" for i in range(len(rows_with_missing))])
        
        for i, (tab, (idx, row)) in enumerate(zip(tabs, rows_with_missing.iterrows())):
            with tab:
                st.write(f"Tournament: {row['Name'] if pd.notna(row['Name']) else 'Unknown'}")
                
                # Create form fields for missing data
                updated_values = {}
                for col in missing_cols:
                    # Show current value (if any)
                    current_val = row[col] if pd.notna(row[col]) else ""
                    
                    # Create appropriate input field based on column type
                    if col == 'Date':
                        if current_val:
                            try:
                                date_val = pd.to_datetime(current_val)
                                new_val = st.date_input(f"{col}", date_val, key=f"date_{idx}_{i}")
                            except:
                                new_val = st.date_input(f"{col}", key=f"date_{idx}_{i}")
                        else:
                            new_val = st.date_input(f"{col}", key=f"date_{idx}_{i}")
                        updated_values[col] = new_val.strftime('%Y-%m-%d') if new_val else None
                    elif col == 'State':
                        states = ["", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                                 "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                                 "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                                 "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                                 "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"]
                        new_val = st.selectbox(f"{col}", states, index=0 if not current_val else states.index(current_val), key=f"state_{idx}_{i}")
                        updated_values[col] = new_val if new_val else None
                    elif col == 'Category':
                        existing_categories = df['Category'].dropna().unique().tolist()
                        categories = [""] + existing_categories
                        new_val = st.selectbox(f"{col}", categories, index=0 if not current_val else 
                                             categories.index(current_val) if current_val in categories else 0, key=f"category_{idx}_{i}")
                        updated_values[col] = new_val if new_val else None
                    else:
                        new_val = st.text_input(f"{col}", current_val, key=f"text_{idx}_{i}")
                        updated_values[col] = new_val if new_val else None
                
                # Update button
                if st.button(f"Update Tournament {i+1}", key=f"button_{idx}_{i}"):
                    for col, val in updated_values.items():
                        df.at[idx, col] = val
                    st.success(f"Tournament {i+1} updated!")
    
    return df

# File uploader
st.subheader("Upload your file")
file_format = st.radio("Select file format:", ["Excel (.xlsx)", "CSV (.csv)"])

uploaded_file = None
if file_format == "Excel (.xlsx)":
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])
else:
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Process the file based on format
        if file_format == "Excel (.xlsx)":
            # For Excel files, use the specialized processing
            df = process_excel_file(uploaded_file)
            
            if not df.empty:
                # Display extracted tournaments
                st.subheader("Extracted Tournament Data")
                st.dataframe(df)
                
                # Clean the data
                cleaned_df = clean_golf_data(df)
                
                # Display cleaned data
                st.subheader("Cleaned Tournament Data")
                st.dataframe(cleaned_df)
                
                # Allow manual entry for missing data
                final_df = manual_entry_form(cleaned_df)
                
                # Create a download button for the cleaned data
                csv = final_df.to_csv(index=False)
                st.download_button(
                    label="Download Cleaned Data (CSV)",
                    data=csv,
                    file_name="cleaned_golf_tournaments.csv",
                    mime="text/csv"
                )
                
                # Also provide Excel download
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, sheet_name='Tournaments', index=False)
                    # Auto-adjust columns' width
                    worksheet = writer.sheets['Tournaments']
                    for i, col in enumerate(final_df.columns):
                        max_len = max(final_df[col].astype(str).apply(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, max_len)
                
                buffer.seek(0)
                
                st.download_button(
                    label="Download Cleaned Data (Excel)",
                    data=buffer,
                    file_name="cleaned_golf_tournaments.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Display analysis of the data
                if not final_df.empty:
                    st.subheader("Data Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    # Count tournaments by category
                    if final_df['Category'].notna().any():
                        with col1:
                            st.write("Tournament Count by Category")
                            category_counts = final_df['Category'].value_counts()
                            st.bar_chart(category_counts)
                    
                    # Count tournaments by state
                    if final_df['State'].notna().any():
                        with col2:
                            st.write("Tournament Count by State")
                            state_counts = final_df['State'].value_counts()
                            st.bar_chart(state_counts)
                    
                    # Count tournaments by month (if dates are available)
                    if final_df['Date'].notna().any():
                        try:
                            final_df['Month'] = pd.to_datetime(final_df['Date']).dt.strftime('%B')
                            st.write("Tournament Count by Month")
                            month_counts = final_df['Month'].value_counts()
                            st.bar_chart(month_counts)
                        except:
                            st.write("Could not analyze tournament count by month due to date format issues.")
            else:
                st.warning("No tournament data found in the Excel file.")
        
        else:  # CSV format
            # Read the CSV file
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
            
            # Allow manual entry for missing data
            final_df = manual_entry_form(cleaned_df)
            
            # Create a download button for the cleaned data
            csv = final_df.to_csv(index=False)
            st.download_button(
                label="Download Cleaned Data",
                data=csv,
                file_name="cleaned_golf_tournaments.csv",
                mime="text/csv"
            )
            
            # Display analysis of the data
            st.subheader("Data Analysis")
            
            # Count tournaments by category
            if final_df['Category'].notna().any():
                st.write("Tournament Count by Category")
                category_counts = final_df['Category'].value_counts()
                st.bar_chart(category_counts)
            
            # Count tournaments by state
            if final_df['State'].notna().any():
                st.write("Tournament Count by State")
                state_counts = final_df['State'].value_counts()
                st.bar_chart(state_counts)
            
            # Count tournaments by month (if dates are available)
            if final_df['Date'].notna().any():
                try:
                    final_df['Month'] = pd.to_datetime(final_df['Date']).dt.strftime('%B')
                    st.write("Tournament Count by Month")
                    month_counts = final_df['Month'].value_counts()
                    st.bar_chart(month_counts)
                except:
                    st.write("Could not analyze tournament count by month due to date format issues.")
    
    except Exception as e:
        st.error(f"Error: {e}")
        st.write("Please ensure your file is properly formatted.")

# Sidebar with instructions
with st.sidebar:
    st.header("Instructions")
    st.write("""
    1. Select your file format (Excel or CSV)
    2. Upload your golf tournament data file
    3. The app will:
       - Extract tournament information
       - Clean and standardize the data
       - Allow you to fill in any missing information
       - Provide data visualizations
    4. Download the cleaned data in your preferred format
    """)
    
    st.header("Required Columns")
    st.write("""
    The app will ensure these required columns are present:
    - Date (tournament date)
    - Name (tournament name)
    - Course (golf course name)
    - Category (tournament type/category)
    - City (location city)
    - State (location state, 2-letter code)
    - Zip (5-digit zip code)
    """)
    
    st.header("Data Processing")
    st.write("""
    This app performs the following:
    
    - For Excel files, intelligent extraction of tournament data
    - Detection of tournament groups within the data
    - Standardization of date formats to YYYY-MM-DD
    - Conversion of state names to two-letter abbreviations
    - Standardization of ZIP codes to 5-digit format
    - Extraction of location data from address fields
    - Interactive form for filling in missing data
    """)