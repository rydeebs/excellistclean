import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
import io

st.set_page_config(page_title="Golf Tournament Data Parser", layout="wide")

st.title("Golf Tournament Data Parser")
st.write("Paste your tournament text data and we'll parse it into a structured format.")

# Required columns
REQUIRED_COLUMNS = ["Date", "Name", "Course", "Category", "City", "State", "Zip"]

def standardize_date(date_str, year="2025"):
    """Convert various date formats to YYYY-MM-DD format."""
    if not date_str:
        return None
    
    date_str = str(date_str).strip()
    
    # Handle month and day only (add year)
    month_day_pattern = r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,\s]+(\d{1,2})$'
    match = re.match(month_day_pattern, date_str, re.IGNORECASE)
    if match:
        month, day = match.groups()
        # Convert month name to number
        month_dict = {
            'January': '01', 'Jan': '01', 'February': '02', 'Feb': '02', 'March': '03', 'Mar': '03',
            'April': '04', 'Apr': '04', 'May': '05', 'June': '06', 'Jun': '06', 'July': '07', 
            'Jul': '07', 'August': '08', 'Aug': '08', 'September': '09', 'Sep': '09', 
            'October': '10', 'Oct': '10', 'November': '11', 'Nov': '11', 'December': '12', 'Dec': '12'
        }
        month_num = month_dict.get(month.capitalize(), '01')
        day_padded = day.zfill(2)
        return f"{year}-{month_num}-{day_padded}"
    
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
    
    return date_str

def standardize_state(state_str):
    """Convert state names to two-letter abbreviations."""
    if not state_str:
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
    if not zip_str:
        return None
    
    zip_str = str(zip_str).strip()
    
    # Extract 5-digit zip code
    zip_pattern = r'(\d{5})(?:-\d{4})?'
    match = re.search(zip_pattern, zip_str)
    if match:
        return match.group(1)
    
    return zip_str

def extract_location_info(location_str):
    """Extract city and state from location string."""
    if not location_str:
        return None, None
    
    # Try to match "City, ST" or "City, State" pattern
    location_match = re.search(r'([^,]+),\s*([A-Za-z]{2}|[A-Za-z\s]+)(?:\s+(\d{5}))?', location_str)
    if location_match:
        city = location_match.group(1).strip()
        state = location_match.group(2).strip()
        zip_code = location_match.group(3) if location_match.groups()[2] else None
        return city, standardize_state(state), zip_code
    
    return None, None, None

def parse_tournament_text(text):
    """Parse tournament text and extract structured data."""
    # Split the text into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    current_tournament = None
    
    # Define patterns
    date_pattern = r'^(?:\*\*)?(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,\s]+(\d{1,2})(?:\*\*)?$'
    entries_close_pattern = r'Entries\s+Close:\s+(.*)'
    course_pattern = r'^(?:\*\*)?(.*?(?:Course|Club|GC|G&CC|Golf|Country|CC|National|International|Plantation))(?:\s+\*+[A-Za-z\s]*\*+)?(?:\*\*)?$'
    location_pattern = r'(.*?),\s+([A-Za-z\s]+),\s+([A-Za-z]{2})(?:\s+(\d{5}))?'
    
    i = 0
    year = "2025"  # Default year
    
    while i < len(lines):
        line = lines[i]
        
        # Check for date
        date_match = re.search(date_pattern, line, re.IGNORECASE)
        if date_match:
            # Save previous tournament if exists
            if current_tournament and 'Name' in current_tournament:
                tournaments.append(current_tournament)
            
            # Start new tournament
            current_tournament = {col: None for col in REQUIRED_COLUMNS}
            month, day = date_match.groups()
            # Format as YYYY-MM-DD
            current_tournament['Date'] = standardize_date(f"{month} {day}", year)
            i += 1
            continue
        
        # Check for entries close date (skip)
        if re.search(entries_close_pattern, line):
            i += 1
            continue
        
        # Check for course name (this will be the tournament name too)
        course_match = re.search(course_pattern, line)
        if course_match and current_tournament:
            course_name = course_match.group(1).strip()
            
            # Clean up any asterisks or special markers
            course_name = re.sub(r'\*+[A-Za-z\s\-]*\*+', '', course_name).strip()
            
            # Set as both Name and Course
            current_tournament['Name'] = course_name
            current_tournament['Course'] = course_name
            
            # Check if the line contains category indicators
            if "Four-Ball" in line or "FOUR-BALL" in line:
                current_tournament['Category'] = "Four-Ball"
            elif "Scramble" in line or "SCRAMBLE" in line:
                current_tournament['Category'] = "Scramble"
            else:
                current_tournament['Category'] = "Regular"  # Default category
            
            i += 1
            continue
        
        # Check for location line
        location_match = re.search(location_pattern, line)
        if location_match and current_tournament:
            location_parts = [p.strip() for p in line.split(',')]
            
            if len(location_parts) >= 3:
                # Format: Venue, City, State (maybe with ZIP)
                venue = location_parts[0].strip()
                city = location_parts[1].strip()
                
                # Parse state and possibly zip
                state_zip = location_parts[2].strip()
                state_parts = state_zip.split()
                
                if len(state_parts) >= 1:
                    state = state_parts[0]
                    current_tournament['State'] = standardize_state(state)
                
                if len(state_parts) >= 2:
                    zip_code = state_parts[1]
                    if re.search(r'\d{5}', zip_code):
                        current_tournament['Zip'] = zip_code
                
                current_tournament['City'] = city
                
                # Update Course if we didn't get it earlier
                if not current_tournament['Course']:
                    current_tournament['Course'] = venue
            
            i += 1
            continue
        
        # Other lines - skip
        i += 1
    
    # Don't forget to add the last tournament
    if current_tournament and 'Name' in current_tournament:
        tournaments.append(current_tournament)
    
    # Convert to DataFrame
    tournaments_df = pd.DataFrame(tournaments)
    return tournaments_df

def standardize_tournament_names(df):
    """Standardize tournament names and extract additional info."""
    if 'Name' not in df.columns:
        return df
    
    # Create copy to avoid modifying the original
    cleaned_df = df.copy()
    
    # Standardize course names
    for idx, name in enumerate(cleaned_df['Name']):
        if pd.isna(name):
            continue
            
        # Remove asterisks and contained text
        name = re.sub(r'\*+[A-Za-z\s\-]*\*+', '', name)
        
        # Remove "Course" suffix if course name is already present
        name = re.sub(r'\s+\-\s+[A-Za-z\s/]+Course$', '', name)
        
        # Clean up
        name = name.strip()
        
        cleaned_df.at[idx, 'Name'] = name
        
        # Ensure Course is populated
        if pd.isna(cleaned_df.at[idx, 'Course']):
            cleaned_df.at[idx, 'Course'] = name
    
    # Extract information from names
    if 'Category' not in cleaned_df.columns:
        cleaned_df['Category'] = None
    
    for idx, name in enumerate(cleaned_df['Name']):
        if pd.isna(name):
            continue
            
        # Look for common tournament types
        if 'championship' in name.lower():
            cleaned_df.at[idx, 'Category'] = 'Championship'
        elif 'amateur' in name.lower():
            cleaned_df.at[idx, 'Category'] = 'Amateur'
        elif 'open' in name.lower():
            cleaned_df.at[idx, 'Category'] = 'Open'
        elif 'invitational' in name.lower():
            cleaned_df.at[idx, 'Category'] = 'Invitational'
        elif 'classic' in name.lower():
            cleaned_df.at[idx, 'Category'] = 'Classic'
        elif 'pro-am' in name.lower() or 'proam' in name.lower():
            cleaned_df.at[idx, 'Category'] = 'Pro-Am'
        elif 'four-ball' in name.lower() or 'fourball' in name.lower():
            cleaned_df.at[idx, 'Category'] = 'Four-Ball'
        elif 'scramble' in name.lower():
            cleaned_df.at[idx, 'Category'] = 'Scramble'
    
    return cleaned_df

def fill_missing_data(df):
    """Fill in missing data based on patterns and defaults."""
    # Create copy to avoid modifying the original
    filled_df = df.copy()
    
    # For tournaments in the same location, copy city/state/zip
    if 'City' in filled_df.columns and 'State' in filled_df.columns:
        for course in filled_df['Course'].unique():
            if pd.isna(course):
                continue
                
            # Find all rows with this course
            course_rows = filled_df['Course'] == course
            
            # Find the first row with city and state data
            if course_rows.any():
                filled_rows = filled_df.loc[course_rows]
                
                # Find first row with city and state
                has_location = filled_rows['City'].notna() & filled_rows['State'].notna()
                if has_location.any():
                    first_location_row = filled_rows.loc[has_location].iloc[0]
                    
                    # Fill in missing city and state for other rows with this course
                    missing_location = course_rows & (filled_df['City'].isna() | filled_df['State'].isna())
                    if missing_location.any():
                        filled_df.loc[missing_location, 'City'] = first_location_row['City']
                        filled_df.loc[missing_location, 'State'] = first_location_row['State']
                        
                        # Also fill zip if available
                        if 'Zip' in filled_df.columns and pd.notna(first_location_row.get('Zip')):
                            filled_df.loc[missing_location, 'Zip'] = first_location_row['Zip']
    
    # Set default categories if missing
    if 'Category' in filled_df.columns:
        filled_df['Category'] = filled_df['Category'].fillna('Regular')
    
    return filled_df

# Main application layout
st.subheader("Enter Tournament Text Data")

# Default text example
default_text = """**Dates**
**Event Information**
**May 7**
Entries Close: May 2, 2025
**The Club at Admirals Cove - North/West Course *****FULL***
The Club at Admirals Cove, Jupiter, FL
Tee Times & Info   Results  
Enter Late
**May 7**
Entries Close: May 2, 2025
**LPGA International - Jones Course *****FULL***
LPGA International, Daytona Beach, FL
Tee Times & Info   Results  
Enter Late"""

# Text area for input
tournament_text = st.text_area(
    "Paste your tournament text here:", 
    height=300,
    value=default_text,
    help="Paste the raw text containing tournament information."
)

# File uploader as an alternative
st.subheader("Or Upload a Text File")
uploaded_file = st.file_uploader("Choose a text file", type=["txt"])

if uploaded_file is not None:
    # Read text file
    tournament_text = uploaded_file.getvalue().decode("utf-8")
    st.success("File uploaded successfully!")

# Year input
year = st.text_input("Tournament Year (if not specified in text):", "2025")

# Process button
if st.button("Process Tournament Data"):
    if tournament_text:
        try:
            # Parse the text
            df = parse_tournament_text(tournament_text)
            
            # Standardize names
            df = standardize_tournament_names(df)
            
            # Fill missing data
            df = fill_missing_data(df)
            
            # Display parsed data
            st.subheader("Extracted Tournament Data")
            st.dataframe(df)
            
            # Show missing data count
            missing_data = {col: df[col].isna().sum() for col in REQUIRED_COLUMNS}
            st.subheader("Missing Data Analysis")
            
            missing_df = pd.DataFrame([missing_data])
            st.dataframe(missing_df)
            
            # Manual data entry for missing fields
            st.subheader("Fill Missing Data")
            
            # For each tournament with missing data
            for idx, row in df.iterrows():
                missing_cols = [col for col in REQUIRED_COLUMNS if pd.isna(row[col])]
                
                if missing_cols:
                    st.write(f"**Tournament {idx+1}:** {row['Name']}")
                    
                    # Create columns for form layout
                    cols = st.columns(min(3, len(missing_cols)))
                    
                    # Create form fields for each missing column
                    updates = {}
                    for i, col in enumerate(missing_cols):
                        with cols[i % 3]:
                            if col == 'Date':
                                # Date picker
                                date_val = st.date_input(f"{col} for {row['Name']}")
                                updates[col] = date_val.strftime('%Y-%m-%d')
                            elif col == 'State':
                                # State dropdown
                                states = ["", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                                         "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                                         "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                                         "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                                         "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"]
                                updates[col] = st.selectbox(f"{col} for {row['Name']}", states, index=0)
                            elif col == 'Category':
                                # Category dropdown
                                categories = ["Regular", "Championship", "Amateur", "Open", "Invitational", 
                                            "Classic", "Pro-Am", "Four-Ball", "Scramble"]
                                updates[col] = st.selectbox(f"{col} for {row['Name']}", categories, index=0)
                            else:
                                # Text input for other fields
                                updates[col] = st.text_input(f"{col} for {row['Name']}")
                    
                    # Update button
                    if st.button(f"Update Tournament {idx+1}"):
                        for col, val in updates.items():
                            df.at[idx, col] = val
                        st.success(f"Tournament {idx+1} updated!")
            
            # Create download buttons for the data
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="golf_tournaments.csv",
                mime="text/csv"
            )
            
            # Excel download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Tournaments', index=False)
                
                # Auto-adjust columns' width
                worksheet = writer.sheets['Tournaments']
                for i, col in enumerate(df.columns):
                    max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, max_len)
            
            buffer.seek(0)
            
            st.download_button(
                label="Download Excel",
                data=buffer,
                file_name="golf_tournaments.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Display data visualizations
            st.subheader("Data Analysis")
            
            # Set up columns for charts
            col1, col2 = st.columns(2)
            
            # Tournament count by category
            with col1:
                st.write("Tournament Count by Category")
                category_counts = df['Category'].value_counts()
                st.bar_chart(category_counts)
            
            # Tournament count by city
            with col2:
                st.write("Tournament Count by City")
                city_counts = df['City'].value_counts()
                st.bar_chart(city_counts)
            
            # Tournament count by date
            if df['Date'].notna().any():
                try:
                    df['Month'] = pd.to_datetime(df['Date']).dt.strftime('%B')
                    st.write("Tournament Count by Month")
                    month_counts = df['Month'].value_counts()
                    st.bar_chart(month_counts)
                except:
                    st.write("Could not analyze tournament count by month due to date format issues.")
        
        except Exception as e:
            st.error(f"Error processing text: {str(e)}")
            # Show traceback for debugging
            import traceback
            st.code(traceback.format_exc())
    else:
        st.error("Please enter tournament text or upload a file.")

# Sidebar with instructions
with st.sidebar:
    st.header("Instructions")
    st.write("""
    ### How to Use This App:
    
    1. Paste your tournament text data in the text area or upload a text file
    2. Click the "Process Tournament Data" button
    3. Review the extracted information
    4. Fill in any missing data as needed
    5. Download the cleaned data in CSV or Excel format
    
    ### Expected Text Format:
    
    The app works best with data structured like:
    ```
    **Month Day**
    [Optional entries close info]
    **Course Name/Tournament Name**
    Location, City, State
    [Optional additional info]
    ```
    
    ### Example:
    ```
    **May 7**
    Entries Close: May 2, 2025
    **The Club at Admirals Cove**
    The Club at Admirals Cove, Jupiter, FL
    ```
    """)
    
    st.header("Required Columns")
    st.write("""
    The app extracts these required columns:
    - Date (tournament date)
    - Name (tournament name)
    - Course (golf course name)
    - Category (tournament type/category)
    - City (location city)
    - State (location state, 2-letter code)
    - Zip (5-digit zip code)
    """)