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

def detect_format(text):
    """Detect which format the text is in."""
    # Split the text into lines and check for patterns
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Check for tabular format with Date, Tournaments columns (Format 3)
    if len(lines) > 0 and ("Date\tTournaments\t" in lines[0] or "Date    Tournaments    " in lines[0]):
        return "TABULAR"
    
    # Check for Championship format (Format 2)
    championship_count = 0
    for line in lines[:20]:  # Check first 20 lines
        if re.search(r'(?:\*\*)?(.*?(?:Championship|Tournament|Cup|Series|Amateur|Open))', line):
            championship_count += 1
    
    if championship_count >= 2:
        return "CHAMPIONSHIP"
    
    # Otherwise assume it's the simple format (Format 1)
    return "SIMPLE"

def parse_tournament_text(text):
    """Parse tournament text and extract structured data based on detected format."""
    # Detect format
    format_type = detect_format(text)
    st.write(f"Detected format: {format_type}")
    
    if format_type == "TABULAR":
        return parse_tabular_format(text)
    elif format_type == "CHAMPIONSHIP":
        return parse_championship_format(text)
    else:
        return parse_simple_format(text)
    
def parse_tabular_format(text):
    """Parse tabular format with columns like 'Date', 'Tournaments', etc."""
    lines = [line for line in text.split('\n') if line.strip()]
    
    tournaments = []
    current_date = None
    current_tournament_name = None
    
    # Skip header line
    i = 1
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for date pattern (Apr 13, May 4, etc.)
        date_match = re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:\-\d{1,2})?$', line)
        
        if date_match:
            # We found a date, update the current date
            month, day = date_match.groups()
            current_date = standardize_date(f"{month} {day}", "2025")
            i += 1
            continue
        
        # Check for tournament name (usually follows a date line)
        if current_date and line and not line.isspace() and not re.match(r'^(Leaderboard|Info|T|M|View leaderboard|Register)', line):
            # This might be a tournament name
            tournament_name = line
            
            # Remove "About" suffix if present
            tournament_name = re.sub(r'\s+About$', '', tournament_name)
            
            # Store the tournament name
            current_tournament_name = tournament_name
            
            # Move to next line
            i += 1
            
            # Check if next line has course/location information
            if i < len(lines):
                course_line = lines[i].strip()
                
                # Look for a line with " · " separator or similar
                location_match = re.search(r'(.*?)(?:\s+·\s+|\s{2,})(.*?),\s+([A-Z]{2})$', course_line)
                
                if location_match:
                    course, city, state = location_match.groups()
                    
                    # Create a tournament entry
                    tournament = {
                        'Date': current_date,
                        'Name': current_tournament_name.strip(),
                        'Course': course.strip(),
                        'Category': "Men's",  # Default category
                        'City': city.strip(),
                        'State': standardize_state(state.strip()),
                        'Zip': None
                    }
                    
                    # Determine category based on tournament name
                    if "Amateur" in current_tournament_name:
                        tournament['Category'] = "Amateur"
                    elif "Senior" in current_tournament_name:
                        tournament['Category'] = "Seniors"
                    elif "Women" in current_tournament_name or "Ladies" in current_tournament_name:
                        tournament['Category'] = "Women's"
                    elif "Junior" in current_tournament_name:
                        tournament['Category'] = "Junior's"
                    
                    tournaments.append(tournament)
                
        # Always move to next line after processing
        i += 1
    
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
        st.warning("No tournaments found in tabular format. Attempting alternative parsing...")
        return parse_tabular_format_alternative(text)

def parse_tabular_format_alternative(text):
    """Alternative parser for tabular format that's more forgiving."""
    lines = [line for line in text.split('\n') if line.strip()]
    
    tournaments = []
    current_date = None
    
    # Skip header line
    i = 1
    
    while i < len(lines) - 1:  # Need at least 2 lines for a complete entry
        current_line = lines[i].strip()
        
        # Check for date pattern
        date_match = re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:\-\d{1,2})?', current_line)
        
        if date_match:
            # We found a date, store it
            month, day = date_match.groups()
            current_date = standardize_date(f"{month} {day}", "2025")
            
            # Advance to next non-empty line
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            
            # Skip lines until we find something that might be a tournament name
            tournament_name = None
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty or marker lines
                if not line or line in ["Leaderboard", "Info", "T", "M", "View leaderboard", "Register"]:
                    i += 1
                    continue
                
                # If has a dot or bullet or "About", likely a tournament line
                if "About" in line or "·" in line:
                    tournament_name = line.split("About")[0].strip() if "About" in line else line
                    i += 1
                    break
                
                # Otherwise, just take this as the tournament name
                tournament_name = line
                i += 1
                break
            
            # Now look for course and location in the next few lines
            course_name = None
            city = None
            state = None
            
            # Search next 3 lines for location
            for j in range(i, min(i+3, len(lines))):
                line = lines[j].strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Look for location pattern (with state abbreviation)
                location_match = re.search(r'(.+?)(?:\s+·\s+|\s{2,})(.+?),\s+([A-Z]{2})$', line)
                if location_match:
                    course_name, city, state = location_match.groups()
                    i = j + 1  # Skip to next line after location
                    break
            
            # If we have enough data, create a tournament entry
            if tournament_name and course_name and city and state:
                tournament = {
                    'Date': current_date,
                    'Name': tournament_name.strip(),
                    'Course': course_name.strip(),
                    'Category': "Men's",  # Default category
                    'City': city.strip(),
                    'State': standardize_state(state.strip()),
                    'Zip': None
                }
                
                # Determine category based on tournament name
                if "Amateur" in tournament_name:
                    tournament['Category'] = "Amateur"
                elif "Senior" in tournament_name:
                    tournament['Category'] = "Seniors"
                elif "Women" in tournament_name or "Ladies" in tournament_name:
                    tournament['Category'] = "Women's"
                elif "Junior" in tournament_name:
                    tournament['Category'] = "Junior's"
                
                tournaments.append(tournament)
            
            # Continue with next lines
            continue
        
        # If not a date line, just move to next line
        i += 1
    
    # Convert to DataFrame
    if tournaments:
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # One last attempt
        return parse_tabular_greedy(text)

def parse_tabular_greedy(text):
    """Greedy parser that looks for any date and location patterns in the text."""
    lines = text.split('\n')
    
    tournaments = []
    
    # Start parsing
    i = 0
    while i < len(lines) - 2:  # Need at least 3 lines for a complete entry
        line = lines[i].strip()
        
        # Look for date pattern
        date_match = None
        if line:
            date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:\-\d{1,2})?', line)
        
        if date_match:
            month, day = date_match.groups()
            current_date = standardize_date(f"{month} {day}", "2025")
            
            # Look ahead for a tournament name and location within the next 10 lines
            for j in range(i+1, min(i+10, len(lines))):
                next_line = lines[j].strip()
                
                # Skip empty lines and specific markers
                if not next_line or next_line in ["Leaderboard", "Info", "T", "M", "View leaderboard"]:
                    continue
                
                # This might be a tournament name
                tournament_name = next_line
                
                # Look ahead for location information
                for k in range(j+1, min(j+5, len(lines))):
                    loc_line = lines[k].strip()
                    
                    # Look for city/state pattern
                    location_match = re.search(r'(.*?)(?:\s+·\s+|\s{2,}|\t+)(.*?),\s+([A-Z]{2})(?:\s|$)', loc_line)
                    
                    if location_match:
                        course, city, state = location_match.groups()
                        
                        # Create a tournament entry
                        tournament = {
                            'Date': current_date,
                            'Name': tournament_name.replace("About", "").strip(),
                            'Course': course.strip(),
                            'Category': "Men's",  # Default category
                            'City': city.strip(),
                            'State': standardize_state(state.strip()),
                            'Zip': None
                        }
                        
                        # Determine category based on tournament name
                        if "Amateur" in tournament_name:
                            tournament['Category'] = "Amateur"
                        elif "Senior" in tournament_name:
                            tournament['Category'] = "Seniors"
                        elif "Women" in tournament_name or "Ladies" in tournament_name:
                            tournament['Category'] = "Women's"
                        elif "Junior" in tournament_name:
                            tournament['Category'] = "Junior's"
                        
                        tournaments.append(tournament)
                        
                        # Skip ahead to after the location line
                        i = k
                        break
                
                # If we found a tournament entry, break out of the inner loop
                if i == k:
                    break
        
        # Move to next line
        i += 1
    
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

def parse_championship_format(text):
    """Parse championship format with tournament names in titles."""
    # Split the text into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    current_tournament = None
    
    # Define patterns
    championship_pattern = r'^(?:\*\*)?(.*?(?:Championship|Tournament|Cup|Series|Amateur|Open|Four-Ball|Scramble|Father|Son|Parent|Child|Brothers|Foursomes))(?:\s+\*+[A-Za-z\s]*\*+)?(?:\*\*)?$'
    full_date_pattern = r'(?:\*\*)?(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,\s]+(\d{1,2})(?:,\s+(\d{4}))?(?:\*\*)?'
    date_range_pattern = r'(?:\*\*)?(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+[A-Za-z]+\s+\d{1,2}(?:,\s+\d{4})?\s+-\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+([A-Za-z]+)\s+(\d{1,2})(?:,\s+(\d{4}))?(?:\*\*)?'
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
        
        # Check for full date (Mon, May 7, 2025)
        date_match = re.search(full_date_pattern, line)
        if date_match and current_tournament:
            month, day, yr = date_match.groups()
            current_year = yr if yr else year
            current_tournament['Date'] = standardize_date(f"{month} {day} {current_year}")
            i += 1
            continue
        
        # Check for date range (Mon, May 7 - Wed, May 9, 2025)
        date_range_match = re.search(date_range_pattern, line)
        if date_range_match and current_tournament:
            month, day, yr = date_range_match.groups()
            current_year = yr if yr else year
            current_tournament['Date'] = standardize_date(f"{month} {day} {current_year}")
            i += 1
            continue
        
        # Skip status lines (OPEN, CLOSED, etc.)
        if re.match(status_pattern, line):
            i += 1
            continue
        
        # Look for a potential course name (not starting with **)
        if current_tournament and not current_tournament.get('Course') and not line.startswith('**'):
            # This might be a course name
            if re.search(r'(?:Club|Course|CC|GC|G&CC|Golf|Country)', line):
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

def parse_simple_format(text):
    """Parse simple format with dates followed by course info."""
    # Split the text into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    current_tournament = None
    
    # Define patterns
    simple_date_pattern = r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})$'
    entries_close_pattern = r'^Entries\s+Close:'
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
        name = row.get('Name')
        
        if pd.isna(course):
            continue
            
        # Clean up course name
        course = re.sub(r'\s+\*+[A-Za-z\s\-]*\*+', '', str(course))
        course = course.strip()
        
        # Update course name
        cleaned_df.at[idx, 'Course'] = course
        
        # Use course name as tournament name if name is missing
        if pd.isna(name):
            cleaned_df.at[idx, 'Name'] = course
        
        # If we already have a tournament name, make sure it's clean
        elif not pd.isna(name):
            name = re.sub(r'\s+\*+[A-Za-z\s\-]*\*+', '', str(name))
            # Remove "About" suffix if present
            name = re.sub(r'\s+About$', '', name)
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

# Example selector
format_option = st.selectbox(
    "Select an example format:",
    ["Format 1: Simple List", "Format 2: Championship List", "Format 3: Tabular List"]
)

# Default text examples
format1_example = """May 7
Entries Close: May 2, 2025
The Club at Admirals Cove - North/West Course *FULL*
The Club at Admirals Cove, Jupiter, FL
Tee Times & Info   Results  
May 7
Entries Close: May 2, 2025
LPGA International - Jones Course *FULL*
LPGA International, Daytona Beach, FL
Tee Times & Info   Results"""

format2_example = """**CLOSED**
**125th WPGA Amateur Championship - Qualifying**
**Tee Sheet**
**Results**
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
Willowbrook Country Club"""

format3_example = """Date	Tournaments	Info	Tournament Types	Favorite	Results
Apr 13	
	
SilverRock  About
SilverRock Resort	  ·  	
La Quinta, CA
Leaderboard	T		
View leaderboard
Apr 13	
	
The Boulder City Championship  About
Boulder City	  ·  	
Boulder City, NV
Leaderboard	T		
View leaderboard
Apr 14	
	
OAK TREE SPRING OPEN
Oak Tree CC- East	  ·  	
Edmond, OK
Leaderboard	T		
View leaderboard"""

# Select the default text based on the chosen format
if format_option == "Format 1: Simple List":
    default_text = format1_example
elif format_option == "Format 2: Championship List":
    default_text = format2_example
else:
    default_text = format3_example

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
    
    1. Select an example format or paste your own tournament text data
    2. Set the default tournament year
    3. Select the default state for tournaments (optional)
    4. Enter a filename for your output file
    5. Click the "Process Tournament Data" button
    6. Review the extracted information
    7. Fill in any missing data as needed
    8. Download the cleaned data in CSV or Excel format
    
    ### Supported Formats:
    
    The app supports three main formats of tournament data:
    
    **Format 1 - Simple List:**
    ```
    May 7
    Entries Close: May 2, 2025
    The Club at Admirals Cove - North/West Course
    The Club at Admirals Cove, Jupiter, FL
    ```
    
    **Format 2 - Championship List:**
    ```
    **125th WPGA Amateur Championship - Qualifying**
    **Tee Sheet**
    **Thu, May 8 - Wed, Jun 4, 2025**
    Montour Heights Country Club
    ```
    
    **Format 3 - Tabular List:**
    ```
    Date    Tournaments    Info    Tournament Types    Favorite    Results
    Apr 13  
        SilverRock  About
        SilverRock Resort    ·    
        La Quinta, CA
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