import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
import io

# Configure page settings for better display
st.set_page_config(
    page_title="Golf Tournament Data Parser",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Golf Tournament Data Parser")
st.write("Paste your tournament text data and we'll parse it into a structured format.")

# Required columns
REQUIRED_COLUMNS = ["Date", "Name", "Course", "Category", "City", "State", "Zip"]

def ultra_simple_date_extractor(text, default_year="2025"):
    """
    An extremely simple date extractor that works without complex regex.
    Returns formatted date (YYYY-MM-DD) or None if no date found.
    """
    if not text:
        return None
    
    # Step 1: Get the part before any dash
    first_part = text.split('-')[0].strip()
    
    # Step 2: Define all possible month names and numbers
    month_dict = {
        'January': '01', 'Jan': '01', 'February': '02', 'Feb': '02', 'March': '03', 'Mar': '03',
        'April': '04', 'Apr': '04', 'May': '05', 'June': '06', 'Jun': '06', 'July': '07', 
        'Jul': '07', 'August': '08', 'Aug': '08', 'September': '09', 'Sep': '09', 
        'October': '10', 'Oct': '10', 'November': '11', 'Nov': '11', 'December': '12', 'Dec': '12'
    }
    
    # Step 3: Find which month name is in the text
    found_month = None
    month_value = None
    
    for month_name, month_num in month_dict.items():
        if month_name in first_part:
            found_month = month_name
            month_value = month_num
            break
    
    if not found_month:
        return None
    
    # Step 4: Find any number after the month name
    after_month_text = first_part.split(found_month)[1]
    day_match = re.search(r'\d+', after_month_text)
    
    if not day_match:
        return None
    
    day = day_match.group(0).zfill(2)  # Pad with leading zero
    
    # Step 5: Find a 4-digit year, or use default
    year_match = re.search(r'\b(20\d{2})\b', text)
    year = year_match.group(1) if year_match else default_year
    
    # Step 6: Return formatted date
    return f"{year}-{month_value}-{day}"

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

def inspect_dataframe(df):
    """Debug function to inspect dataframe content at different stages"""
    st.write(f"DataFrame shape: {df.shape}")
    st.write(f"DataFrame columns: {df.columns.tolist()}")
    st.write(f"DataFrame first few rows:")
    st.write(df.head())
    # Print the entire dataframe for debugging
    with st.expander("Show full DataFrame for debugging"):
        for i, row in df.iterrows():
            st.write(f"Row {i}: {dict(row)}")
    return df

def detect_format(text):
    """Detect which format the text is in."""
    # Split the text into lines and check for patterns
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Special format for your data with bullets and markdown formatting
    if any('**' in line for line in lines) and any('*' in line for line in lines):
        return "MARKDOWN_FORMAT"
    
    # Look for a pattern of 4-line entries with a date range on the 4th line
    if len(lines) >= 4:
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", 
                      "September", "October", "November", "December", "Jan", "Feb", "Mar", 
                      "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # Check if every 4th line has a month name and a dash (indicating date range)
        date_ranges = 0
        for i in range(3, len(lines), 4):
            if i < len(lines) and any(month in lines[i] for month in month_names) and "-" in lines[i]:
                date_ranges += 1
        
        if date_ranges >= 1:
            return "LIST_FORMAT"
    
    # Other format checks
    if len(lines) > 0 and ("Date\tTournaments\t" in lines[0] or "Date    Tournaments    " in lines[0]):
        return "TABULAR"
    
    championship_count = 0
    for line in lines[:20]:
        if re.search(r'(?:\*\*)?(.*?(?:Championship|Tournament|Cup|Series|Amateur|Open))', line):
            championship_count += 1
    
    if championship_count >= 2:
        return "CHAMPIONSHIP"
    
    date_count = 0
    for line in lines[:20]:
        if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', line):
            date_count += 1
    
    if date_count >= 2:
        return "MANUAL_TABULAR"
    
    return "SIMPLE"

def parse_markdown_format(text):
    """Parse markdown format with bullet points and bold text."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    
    for line in lines:
        # Skip non-tournament lines
        if not ('*' in line and '**' in line):
            continue
        
        # Extract tournament name (text in bold)
        name_match = re.search(r'\*\*(.*?)\*\*', line)
        if not name_match:
            continue
            
        name = name_match.group(1).strip()
        
        # Get text after the name
        after_name_text = line[line.find(name_match.group(0)) + len(name_match.group(0)):].strip()
        
        # Split the text by state code (2 capital letters) to get course+city and date
        state_match = re.search(r'\b([A-Z]{2})\b', after_name_text)
        if not state_match:
            continue
            
        state = state_match.group(1)
        state_pos = after_name_text.find(state)
        
        # Extract course and city
        before_state = after_name_text[:state_pos].strip()
        last_space = before_state.rfind(' ')
        
        if last_space > 0:
            course = before_state[:last_space].strip()
            city = before_state[last_space:].strip().rstrip(',')
        else:
            course = before_state
            city = ""
        
        # Extract date
        after_state = after_name_text[state_pos + len(state):].strip()
        date_text = after_state.split('-')[0].strip()
        
        # Process the date
        date_value = ultra_simple_date_extractor(date_text, year)
        
        if date_value:
            # Create tournament entry
            tournament = {
                'Date': date_value,
                'Name': name.strip(),
                'Course': course.strip(),
                'Category': "Men's",  # Default category
                'City': city.strip(),
                'State': state.strip(),
                'Zip': None
            }
            
            # Determine category based on tournament name
            if "Amateur" in name:
                tournament['Category'] = "Amateur"
            elif "Senior" in name:
                tournament['Category'] = "Seniors"
            elif "Women" in name or "Ladies" in name:
                tournament['Category'] = "Women's"
            elif "Junior" in name or "Boys'" in name or "Girls'" in name:
                tournament['Category'] = "Junior's"
            
            # Add the tournament to our list
            tournaments.append(tournament)
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in markdown format")
        for i, t in enumerate(tournaments[:5]):
            st.write(f"Tournament {i+1}: {t['Name']}, Date: {t['Date']}")
        
        tournaments_df = pd.DataFrame(tournaments)
        return inspect_dataframe(tournaments_df)
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def parse_list_format(text, year="2025"):
    """
    Parse the list format with tournament name, course, location, and date range.
    Uses ultra-simple direct date extraction method.
    Processes all rows without artificial limitations.
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    # Skip header line if it exists (e.g., "FUTURE TOURNAMENTS")
    if i < len(lines) and ("TOURNAMENT" in lines[i].upper() or "FUTURE" in lines[i].upper()):
        i += 1
    
    # Process all lines in groups of 4 (name, course, location, date)
    while i <= len(lines) - 4:  # Ensure we check all complete entries
        # Assume pattern: Tournament Name, Course, Location, Date Range
        tournament_name = lines[i]
        course_name = lines[i+1]
        location_line = lines[i+2]
        date_line = lines[i+3]
        
        # Skip to next line if this line seems to be a date (probably not a name)
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", 
                      "September", "October", "November", "December", "Jan", "Feb", "Mar", 
                      "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        if any(month in tournament_name for month in month_names):
            i += 1
            continue
            
        # Parse location for city and state
        location_match = re.search(r'(.*?),\s+([A-Z]{2})(?:\s|$)', location_line)
        city = location_match.group(1) if location_match else ""
        state = location_match.group(2) if location_match else ""
        
        # Extract date using our ultra-simple method
        date_value = ultra_simple_date_extractor(date_line, year)
        
        # Add tournament to list if we have a valid date
        if date_value:
            # Create tournament entry
            tournament = {
                'Date': date_value,
                'Name': tournament_name.strip(),
                'Course': course_name.strip(),
                'Category': "Men's",  # Default category
                'City': city.strip(),
                'State': state,
                'Zip': None
            }
            
            # Determine category based on tournament name
            name = tournament_name
            if "Amateur" in name:
                tournament['Category'] = "Amateur"
            elif "Senior" in name:
                tournament['Category'] = "Seniors"
            elif "Women" in name or "Ladies" in name:
                tournament['Category'] = "Women's"
            elif "Junior" in name or "Boys'" in name or "Girls'" in name:
                tournament['Category'] = "Junior's"
            
            # Add the tournament to our list
            tournaments.append(tournament)
        
        # Always move forward by 4 lines after processing a group
        i += 4
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in list format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def parse_tabular_format(text):
    """Parse tabular format with columns like 'Date', 'Tournaments', etc."""
    lines = [line for line in text.split('\n')]
    
    tournaments = []
    
    # Skip header line if it exists
    i = 0
    if i < len(lines) and "Date" in lines[i] and "Tournaments" in lines[i]:
        i = 1
    
    while i < len(lines) - 3:  # Need at least 4 lines for a complete tournament entry
        line = lines[i].strip()
        
        # Check for date pattern (Apr 13, May 4, etc.)
        date_match = re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:\-\d{1,2})?', line)
        
        if date_match:
            # We found a date, extract it
            month, day = date_match.groups()
            current_date = ultra_simple_date_extractor(f"{month} {day}", year)
            
            # Store the date and look ahead for tournament info
            tournament_data = {'Date': current_date, 'Name': None, 'Course': None, 'City': None, 'State': None, 'Zip': None, 'Category': "Men's"}
            
            # Look ahead for tournament info
            j = i + 1
            
            # Skip empty lines after date
            while j < len(lines) and not lines[j].strip():
                j += 1
            
            # Next non-empty line should be tournament name
            if j < len(lines) and lines[j].strip():
                # Get tournament name and remove "About" suffix
                tournament_name = lines[j].strip()
                tournament_name = re.sub(r'\s+About$', '', tournament_name)
                tournament_data['Name'] = tournament_name
                j += 1
            
            # Skip empty lines after name
            while j < len(lines) and not lines[j].strip():
                j += 1
            
            # Next line should be course
            if j < len(lines) and lines[j].strip():
                course_line = lines[j].strip()
                # Extract course name (everything before tab or dot)
                course_parts = re.split(r'\t+|\s{2,}·\s{2,}|\s{2,}', course_line)
                if course_parts and course_parts[0].strip():
                    tournament_data['Course'] = course_parts[0].strip()
                j += 1
            
            # Skip empty lines after course
            while j < len(lines) and not lines[j].strip():
                j += 1
            
            # Next line should be location
            if j < len(lines) and lines[j].strip():
                location_line = lines[j].strip()
                location_match = re.search(r'(.*?),\s+([A-Z]{2})(?:\s|$)', location_line)
                if location_match:
                    city, state = location_match.groups()
                    tournament_data['City'] = city.strip()
                    tournament_data['State'] = standardize_state(state.strip())
                j += 1
            
            # Skip ahead to find the next date line
            while j < len(lines):
                if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', lines[j].strip()):
                    i = j
                    break
                j += 1
                
            # Add the tournament if we have at least a name
            if tournament_data['Name']:
                # Determine category based on tournament name
                name = tournament_data['Name']
                if "Amateur" in name:
                    tournament_data['Category'] = "Amateur"
                elif "Senior" in name:
                    tournament_data['Category'] = "Seniors"
                elif "Women" in name or "Ladies" in name:
                    tournament_data['Category'] = "Women's"
                elif "Junior" in name:
                    tournament_data['Category'] = "Junior's"
                
                tournaments.append(tournament_data)
                
            if j >= len(lines):
                break
        else:
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
            yr = yr if yr else year
            current_tournament['Date'] = ultra_simple_date_extractor(f"{month} {day} {yr}")
            i += 1
            continue
        
        # Check for date range (Mon, May 7 - Wed, May 9, 2025)
        date_range_match = re.search(date_range_pattern, line)
        if date_range_match and current_tournament:
            month, day, yr = date_range_match.groups()
            yr = yr if yr else year
            current_tournament['Date'] = ultra_simple_date_extractor(f"{month} {day} {yr}")
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
            current_tournament['Date'] = ultra_simple_date_extractor(f"{month} {day}", year)
            
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

def parse_tournament_text(text):
    """Parse tournament text and extract structured data based on detected format."""
    # Detect format
    format_type = detect_format(text)
    st.write(f"Detected format: {format_type}")
    
    if format_type == "MARKDOWN_FORMAT":
        return parse_markdown_format(text)
    elif format_type == "LIST_FORMAT":
        return parse_list_format(text, year)
    elif format_type == "TABULAR" or format_type == "MANUAL_TABULAR":
        return parse_tabular_format(text)
    elif format_type == "CHAMPIONSHIP":
        return parse_championship_format(text)
    else:
        return parse_simple_format(text)

# Example selector
format_option = st.selectbox(
    "Select an example format:",
    ["Format 1: Simple List", "Format 2: Championship List", "Format 3: Tabular List", "Format 4: List with Date Ranges"]
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

format4_example = """FUTURE TOURNAMENTS
Alabama State Senior & Super Senior Amateur Championship
Musgrove Country Club
Jasper, AL
May 16, 2025 - May 18, 2025
Wilfred Galbraith Invitational
Anniston Country Club
Anniston, AL
May 30 - June 01 2025
Alabama Women's State Mid-Amateur Championship
Valley Hill Country Club
Huntsville, AL
June 02 - 04 2025
Alabama Girls' State Junior Championship
Valley Hill Country Club
Huntsville, AL
June 02 - 04 2025
Alabama State Amateur Championship
Capitol Hill Golf Course - Senator Course
Prattville, AL
June 04 - 07 2025
Mobile Metro Mid-Am & Net Championship
Azalea City Golf Course
Mobile, AL
June 07 - 08 2025"""

# Select the default text based on the chosen format
if format_option == "Format 1: Simple List":
    default_text = format1_example
elif format_option == "Format 2: Championship List":
    default_text = format2_example
elif format_option == "Format 3: Tabular List":
    default_text = format3_example
else:
    default_text = format4_example

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
            
            # Check if DataFrame is empty
            if df.empty:
                st.error("No tournaments could be extracted from the text. Please check the format.")
                # Create an empty DataFrame with all required columns
                df = pd.DataFrame(columns=REQUIRED_COLUMNS)
            else:
                # Ensure all required columns exist
                for col in REQUIRED_COLUMNS:
                    if col not in df.columns:
                        df[col] = None
            
            # Display how many tournaments were found
            st.success(f"Successfully extracted {len(df)} tournaments!")
            
            # Display the full DataFrame without pagination (show all rows)
            st.write("### Extracted Tournament Data")
            st.write(df)
            
            # Also show the raw data in table format to ensure all rows are visible
            st.write("### Tournament Table (All Rows)")
            st.table(df.head(100))  # Show up to 100 rows in table format
            
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
            
        except Exception as e:
            st.error(f"Error processing text: {str(e)}")
            # Show traceback for debugging
            import traceback
            st.code(traceback.format_exc())
    else:
        st.error("Please enter tournament text data.")