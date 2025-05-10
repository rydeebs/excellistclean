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

def parse_tournament_text(text):
    """Parse tournament text and extract structured data."""
    # Split the text into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    current_tournament = None
    
    # Define patterns
    # Simple date pattern (May 7)
    simple_date_pattern = r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})$'
    entries_close_pattern = r'^Entries\s+Close:'
    course_pattern = r'^(?:.*?)(?:Club|Course|CC|GC|G&CC|Golf|Country)(?:.*?)$'
    location_pattern = r'(.*?),\s+([A-Za-z\s]+),\s+([A-Za-z]{2})'
    
    i = 0
    year = "2025"  # Default year
    
    while i < len(lines):
        line = lines[i]
        
        # Check for simple date pattern (May 7)
        date_match = re.match(simple_date_pattern, line)
        if date_match:
            # Save previous tournament if exists
            if current_tournament and current_tournament.get('Course'):
                tournaments.append(current_tournament)
            
            # Start new tournament
            current_tournament = {col: None for col in REQUIRED_COLUMNS}
            month, day = date_match.groups()
            current_tournament['Date'] = standardize_date(f"{month} {day}", year)
            
            i += 1
            continue
        
        # Skip "Entries Close" lines
        if re.match(entries_close_pattern, line):
            i += 1
            continue
        
        # Check for course name
        if current_tournament and current_tournament.get('Date') and not current_tournament.get('Course'):
            # This might be a course name
            course_name = line
            # Clean up asterisks and contained text
            course_name = re.sub(r'\s+\*+[A-Za-z\s\-]*\*+', '', course_name)
            current_tournament['Course'] = course_name
            current_tournament['Name'] = course_name  # Use course name as tournament name
            
            # Set a default category (can be refined based on course name)
            if "Four-Ball" in line:
                current_tournament['Category'] = "Four-Ball"
            elif "Scramble" in line:
                current_tournament['Category'] = "Scramble"
            else:
                current_tournament['Category'] = "Men's"  # Default category
            
            i += 1
            continue
        
        # Check for location line (Club, City, State)
        if current_tournament and current_tournament.get('Course'):
            location_match = re.search(location_pattern, line)
            if location_match:
                club, city, state = location_match.groups()
                
                # Update course name if needed
                if club and club.strip() != current_tournament['Course']:
                    current_tournament['Course'] = club.strip()
                
                # Set city and state
                current_tournament['City'] = city.strip()
                current_tournament['State'] = standardize_state(state.strip())
                
                i += 1
                continue
        
        # Move to next line
        i += 1
    
    # Don't forget to add the last tournament
    if current_tournament and current_tournament.get('Course'):
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
    
    # Standardize course names and set as tournament names
    for idx, row in cleaned_df.iterrows():
        course = row.get('Course')
        if pd.isna(course):
            continue
            
        # Clean up course name
        course = re.sub(r'\s+\*+[A-Za-z\s\-]*\*+', '', course)
        course = course.strip()
        
        # Update course name
        cleaned_df.at[idx, 'Course'] = course
        
        # Use course name as tournament name if name is missing
        if pd.isna(row.get('Name')):
            cleaned_df.at[idx, 'Name'] = course
        
        # If we already have a tournament name, make sure it's clean
        elif not pd.isna(row.get('Name')):
            name = row.get('Name')
            name = re.sub(r'\s+\*+[A-Za-z\s\-]*\*+', '', name)
            cleaned_df.at[idx, 'Name'] = name.strip()
    
    # Extract information from course names
    if 'Category' not in cleaned_df.columns:
        cleaned_df['Category'] = None
    
    for idx, row in cleaned_df.iterrows():
        # Skip if we already have a category
        if pd.notna(row.get('Category')):
            continue
            
        course = str(row.get('Course', '')).lower()
        name = str(row.get('Name', '')).lower()
        
        # Look for category indicators
        if "scramble" in course or "scramble" in name:
            cleaned_df.at[idx, 'Category'] = "Scramble"
        elif "four-ball" in course or "four-ball" in name or "fourball" in course:
            cleaned_df.at[idx, 'Category'] = "Four-Ball"
        elif "senior" in course or "senior" in name:
            cleaned_df.at[idx, 'Category'] = "Seniors"
        elif "women" in course or "women" in name or "ladies" in course or "ladies" in name:
            cleaned_df.at[idx, 'Category'] = "Women's"
        elif "amateur" in course or "amateur" in name:
            cleaned_df.at[idx, 'Category'] = "Amateur"
        elif "junior" in course or "junior" in name:
            cleaned_df.at[idx, 'Category'] = "Junior's"
        else:
            cleaned_df.at[idx, 'Category'] = "Men's"  # Default category
    
    return cleaned_df

def fill_missing_data(df):
    """Fill in missing data based on patterns."""
    # Create copy to avoid modifying the original
    filled_df = df.copy()
    
    # Set default categories if missing
    if 'Category' in filled_df.columns:
        filled_df['Category'] = filled_df['Category'].fillna('Men\'s')  # Default to Men's if not specified
    
    # Apply default state if provided
    if 'State' in filled_df.columns and default_state:
        filled_df.loc[filled_df['State'].isna(), 'State'] = default_state
    
    return filled_df

# Main application layout
st.subheader("Enter Tournament Text Data")

# Default text example
default_text = """May 7
Entries Close: May 2, 2025
The Club at Admirals Cove - North/West Course *FULL*
The Club at Admirals Cove, Jupiter, FL
Tee Times & Info   Results  
May 7
Entries Close: May 2, 2025
LPGA International - Jones Course *FULL*
LPGA International, Daytona Beach, FL
Tee Times & Info   Results  
May 8
Entries Close: May 3, 2025
LPGA International - Hills Course *FULL*
LPGA International, Daytona Beach, FL
Tee Times & Info   Results"""

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
    help="Select the default state for tournaments. This will be used as the default state when not specified."
)

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
            
            # Fill missing data (just categories and default state)
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
            
            # Tournament count by state
            with col2:
                st.write("Tournament Count by State")
                state_counts = df['State'].value_counts()
                st.bar_chart(state_counts)
            
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
    3. Select the default state for tournaments (optional)
    4. Enter a filename for your output file
    5. Click the "Process Tournament Data" button
    6. Review the extracted information
    7. Fill in any missing data as needed
    8. Download the cleaned data in CSV or Excel format
    
    ### Expected Text Format:
    
    The app works best with data formatted like:
    ```
    May 7
    Entries Close: May 2, 2025
    The Club at Admirals Cove - North/West Course
    The Club at Admirals Cove, Jupiter, FL
    ```
    
    ### Required Columns:
    
    The app extracts these required columns:
    - Date (tournament date)
    - Name (tournament name)
    - Course (golf course name)
    - Category (tournament type/category) - Men's, Women's, Seniors, Amateur, or Junior's
    - City (location city) - extracted from text when available
    - State (location state, 2-letter code) - extracted from text or uses default
    - Zip (5-digit zip code) - mostly left blank
    """)