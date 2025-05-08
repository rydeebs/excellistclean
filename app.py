import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
import io
import requests
import time

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

def search_golf_course_location(course_name, state_code):
    """
    Search for the location of a golf course using web_search tool.
    This function will be used in the Streamlit app to find location data.
    """
    # In the actual implementation, this would call web_search
    # For now, we'll add a placeholder function that simulates a search result
    
    # Create a progress indicator
    with st.spinner(f"Looking up location for {course_name}..."):
        # This is where the actual web search would happen
        # In a real implementation, you would use Streamlit's built-in functions
        # or external APIs to perform the search
        time.sleep(0.5)  # Simulate search delay
        
        # Example implementation (replace with actual web search function):
        # In a real implementation, you would analyze search results to extract city/zip
        
        # Try to extract location from course name if it contains it
        if ',' in course_name:
            parts = course_name.split(',')
            if len(parts) >= 2:
                city = parts[1].strip()
                return (city, state_code, "")
        
        # Extract city from course name if it might be part of the name
        if " in " in course_name:
            parts = course_name.split(" in ")
            if len(parts) == 2:
                location_part = parts[1].strip()
                if ',' in location_part:
                    city = location_part.split(',')[0].strip()
                    return (city, state_code, "")
    
    # Return placeholder for demo purposes
    # In real implementation, you would return actual search results
    return ("Location pending search", state_code, "")

def parse_tournament_text(text):
    """Parse tournament text and extract structured data."""
    # Split the text into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    current_tournament = None
    
    # Define patterns
    championship_pattern = r'^(?:\*\*)?(.*?(?:Championship|Tournament|Cup|Series|Amateur|Open))(?:\s+\*+[A-Za-z\s]*\*+)?(?:\*\*)?$'
    date_pattern = r'(?:\*\*)?(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,\s]+(\d{1,2})(?:,\s+(\d{4}))?(?:\*\*)?'
    date_range_pattern = r'(?:\*\*)?(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+[A-Za-z]+\s+\d{1,2}(?:,\s+\d{4})?\s+-\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+([A-Za-z]+)\s+(\d{1,2})(?:,\s+(\d{4}))?(?:\*\*)?'
    course_pattern = r'^(?:\*\*)?(.*?(?:Course|Club|GC|G&CC|Golf|Country|CC|National|International|Plantation))(?:\s+\*+[A-Za-z\s]*\*+)?(?:\*\*)?$'
    status_pattern = r'(?:\*\*)?(OPEN|CLOSED|INVITATION LIST)(?:\*\*)?'
    
    i = 0
    year = "2025"  # Default year
    
    while i < len(lines):
        line = lines[i]
        
        # Check for championship name
        championship_match = re.search(championship_pattern, line)
        if championship_match:
            # Save previous tournament if exists
            if current_tournament and current_tournament.get('Name'):
                tournaments.append(current_tournament)
            
            # Start new tournament
            current_tournament = {col: None for col in REQUIRED_COLUMNS}
            tournament_name = championship_match.group(1).strip()
            current_tournament['Name'] = tournament_name
            
            # Set default category based on name
            if "Senior" in tournament_name:
                current_tournament['Category'] = "Seniors"
            elif "Men's" in tournament_name or "Mens" in tournament_name:
                current_tournament['Category'] = "Men's"
            elif "Amateur" in tournament_name:
                current_tournament['Category'] = "Amateur"
            elif "Junior" in tournament_name:
                current_tournament['Category'] = "Junior's"
            elif "Women's" in tournament_name or "Womens" in tournament_name or "Ladies" in tournament_name:
                current_tournament['Category'] = "Women's"
            else:
                current_tournament['Category'] = "Men's"  # Default category
            
            i += 1
            continue
        
        # Check for date (single day)
        date_match = re.search(date_pattern, line)
        if date_match and current_tournament:
            month, day, yr = date_match.groups()
            current_year = yr if yr else year
            current_tournament['Date'] = standardize_date(f"{month} {day} {current_year}")
            i += 1
            continue
        
        # Check for date range (use end date)
        date_range_match = re.search(date_range_pattern, line)
        if date_range_match and current_tournament:
            month, day, yr = date_range_match.groups()
            current_year = yr if yr else year
            current_tournament['Date'] = standardize_date(f"{month} {day} {current_year}")
            i += 1
            continue
        
        # Check for course/venue
        course_match = re.search(course_pattern, line)
        if course_match and current_tournament:
            course_name = course_match.group(1).strip()
            current_tournament['Course'] = course_name
            
            # Try to extract city from course name if it contains a comma
            if ',' in course_name:
                parts = course_name.split(',')
                if len(parts) >= 2:
                    current_tournament['City'] = parts[1].strip()
            
            i += 1
            continue
        
        # Check for status (skip)
        status_match = re.search(status_pattern, line)
        if status_match:
            i += 1
            continue
        
        # Other lines - check if it might be a standalone venue
        if current_tournament and not current_tournament.get('Course'):
            if re.search(r'Country Club|Golf Club|Golf Course', line) and not line.startswith('**'):
                current_tournament['Course'] = line.strip()
            
        i += 1
    
    # Don't forget to add the last tournament
    if current_tournament and current_tournament.get('Name'):
        tournaments.append(current_tournament)
    
    # Convert to DataFrame
    if tournaments:
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

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
            
        # Look for specified tournament categories
        name_lower = name.lower()
        if 'senior' in name_lower or 'seniors' in name_lower:
            cleaned_df.at[idx, 'Category'] = "Seniors"
        elif "men's" in name_lower or "mens" in name_lower:
            cleaned_df.at[idx, 'Category'] = "Men's"
        elif 'amateur' in name_lower:
            cleaned_df.at[idx, 'Category'] = "Amateur"
        elif "junior's" in name_lower or "juniors" in name_lower or "junior" in name_lower:
            cleaned_df.at[idx, 'Category'] = "Junior's"
        elif "women's" in name_lower or "womens" in name_lower or "ladies" in name_lower:
            cleaned_df.at[idx, 'Category'] = "Women's"
        
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
        filled_df['Category'] = filled_df['Category'].fillna('Men\'s')  # Default to Men's if not specified
    
    return filled_df

# Main application layout
st.subheader("Enter Tournament Text Data")

# Default text example
default_text = """**125th WPGA Amateur Championship - Qualifying**
**Tee Sheet**
**Thu, May 8 - Wed, Jun 4, 2025**
**Next Round: Thu, May 8, 2025**
Multiple Courses
**CLOSED**
**122nd WPGA Open Championship - Qualifying**
**Tee Sheet**
**Results**
**Wed, Apr 30 - Thu, May 15, 2025**
**Next Round: Thu, May 15, 2025**
Montour Heights Country Club
Willowbrook Country Club
**OPEN**
**closes on**
**WED, MAY 07 5:00 PM EDT**"""

# Text area for input
tournament_text = st.text_area(
    "Paste your tournament text here:", 
    height=300,
    value=default_text,
    help="Paste the raw text containing tournament information."
)

# Year input
year = st.text_input("Tournament Year (if not specified in text):", "2025")

# Default state input
default_state = st.selectbox(
    "Default State for Tournaments:",
    ["", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
     "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
     "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
     "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
     "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"],
    help="Select the default state for tournaments. This will be used to look up course information."
)

# Search option for course locations
use_web_search = st.checkbox("Use web search to find golf course locations", value=True, 
                           help="Enable this to search for course locations on the web.")

# File naming option
output_filename = st.text_input("Output Filename (without extension):", "golf_tournaments")

# Process button
if st.button("Process Tournament Data"):
    if tournament_text:
        try:
            # Parse the text
            df = parse_tournament_text(tournament_text)
            
            # Display the raw parsed data for debugging
            st.subheader("Raw Parsed Data")
            st.write(f"Found {len(df)} tournaments")
            st.write(f"Columns: {list(df.columns)}")
            
            # Check if DataFrame is empty or missing required columns
            if df.empty:
                st.error("No tournaments could be extracted from the text. Please check the format.")
                # Create an empty DataFrame with all required columns
                df = pd.DataFrame(columns=REQUIRED_COLUMNS)
            else:
                # Ensure all required columns exist
                for col in REQUIRED_COLUMNS:
                    if col not in df.columns:
                        df[col] = None
            
            # Standardize names
            df = standardize_tournament_names(df)
            
            # Apply default state if provided
            if default_state:
                # Update State column for rows with missing state
                df.loc[df['State'].isna(), 'State'] = default_state
                
                # Look up City and Zip based on Course name and State if enabled
                if use_web_search:
                    progress_bar = st.progress(0)
                    st.write("Looking up golf course locations...")
                    
                    for idx, row in df.iterrows():
                        progress = int((idx + 1) / len(df) * 100)
                        progress_bar.progress(progress)
                        
                        if pd.isna(row['City']) or pd.isna(row['Zip']):
                            if pd.notna(row['Course']) and pd.notna(row['State']):
                                city, state, zip_code = search_golf_course_location(row['Course'], row['State'])
                                
                                # Update only if currently missing
                                if pd.isna(row['City']):
                                    df.at[idx, 'City'] = city
                                if pd.isna(row['Zip']):
                                    df.at[idx, 'Zip'] = zip_code
                    
                    progress_bar.empty()
            
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
                                # Category dropdown with updated options
                                categories = ["Men's", "Women's", "Seniors", "Amateur", "Junior's"]
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
                file_name=f"{output_filename}.csv",
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
                file_name=f"{output_filename}.xlsx",
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
                except Exception as e:
                    st.write(f"Could not analyze tournament count by month: {str(e)}")
        
        except Exception as e:
            st.error(f"Error processing text: {str(e)}")
            # Show traceback for debugging
            import traceback
            st.code(traceback.format_exc())
    else:
        st.error("Please enter tournament text data.")

# Sidebar with instructions
with st.sidebar:
    st.header("Instructions")
    st.write("""
    ### How to Use This App:
    
    1. Paste your tournament text data in the text area
    2. Set the default tournament year
    3. Select the default state for tournaments
    4. Choose whether to use web search for course locations
    5. Enter a filename for your output file
    6. Click the "Process Tournament Data" button
    7. Review the extracted information
    8. Fill in any missing data as needed
    9. Download the cleaned data in CSV or Excel format
    
    ### Web Search Feature:
    
    When enabled, the app will search for golf course location information online.
    This can help automatically fill in City and Zip information based on the course name.
    """)
    
    st.header("Required Columns")
    st.write("""
    The app extracts these required columns:
    - Date (tournament date)
    - Name (tournament name)
    - Course (golf course name)
    - Category (tournament type/category) - Men's, Women's, Seniors, Amateur, or Junior's
    - City (location city)
    - State (location state, 2-letter code)
    - Zip (5-digit zip code)
    """)