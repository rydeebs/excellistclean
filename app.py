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
    """Convert various date formats to YYYY-MM-DD format, always using the first date in a range."""
    if not date_str:
        return None

    date_str = str(date_str).strip()

    # Handle full date range: "June 1, 2025 - June 3, 2025" or "June 1 - 3, 2025"
    # This will always extract the first date
    range_patterns = [
        # "June 1, 2025 - June 3, 2025" or "June 1, 2025 - 3, 2025"
        r'^(January|February|March|April|May|June|July|August|September|October|November|December|'
        r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s*(\d{4})?\s*-\s*'
        r'((January|February|March|April|May|June|July|August|September|October|November|December|'
        r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+)?(\d{1,2}),?\s*(\d{4})?$',
        # "June 1 - 3, 2025"
        r'^(January|February|March|April|May|June|July|August|September|October|November|December|'
        r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s*-\s*(\d{1,2}),?\s*(\d{4})?$',
        # "May 30 - June 1, 2025"
        r'^(January|February|March|April|May|June|July|August|September|October|November|December|'
        r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s*-\s*'
        r'(January|February|March|April|May|June|July|August|September|October|November|December|'
        r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s*(\d{4})?$'
    ]
    for pat in range_patterns:
        match = re.match(pat, date_str, re.IGNORECASE)
        if match:
            # Always extract the first date
            month = match.group(1)
            day = match.group(2)
            yr = match.group(3)
            current_year = yr if yr else year
            month_dict = {
                'January': '01', 'Jan': '01', 'February': '02', 'Feb': '02', 'March': '03', 'Mar': '03',
                'April': '04', 'Apr': '04', 'May': '05', 'June': '06', 'Jun': '06', 'July': '07',
                'Jul': '07', 'August': '08', 'Aug': '08', 'September': '09', 'Sep': '09',
                'October': '10', 'Oct': '10', 'November': '11', 'Nov': '11', 'December': '12', 'Dec': '12'
            }
            month_num = month_dict.get(month.capitalize(), '01')
            day_padded = day.zfill(2)
            return f"{current_year}-{month_num}-{day_padded}"

    # Handle single full date like "June 1, 2025"
    full_date_pattern = r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:,\s+(\d{4}))?$'
    match = re.match(full_date_pattern, date_str, re.IGNORECASE)
    if match:
        month, day, yr = match.groups()
        current_year = yr if yr else year
        month_dict = {
            'January': '01', 'Jan': '01', 'February': '02', 'Feb': '02', 'March': '03', 'Mar': '03',
            'April': '04', 'Apr': '04', 'May': '05', 'June': '06', 'Jun': '06', 'July': '07',
            'Jul': '07', 'August': '08', 'Aug': '08', 'September': '09', 'Sep': '09',
            'October': '10', 'Oct': '10', 'November': '11', 'Nov': '11', 'December': '12', 'Dec': '12'
        }
        month_num = month_dict.get(month.capitalize(), '01')
        day_padded = day.zfill(2)
        return f"{current_year}-{month_num}-{day_padded}"

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
    
    # Check for list format with tournament info and date ranges
    if len(lines) >= 4:
        date_range_count = 0
        for i in range(3, len(lines), 4):  # Check every 4th line for date patterns
            if i < len(lines) and re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s*-\s*', lines[i]):
                date_range_count += 1
                
        if date_range_count >= 2:
            return "LIST_FORMAT"
    
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
    
    # Check for manual input without header (just dates)
    date_count = 0
    for line in lines[:20]:
        if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', line):
            date_count += 1
    
    if date_count >= 2:
        return "MANUAL_TABULAR"
    
    # Otherwise assume it's the simple format (Format 1)
    return "SIMPLE"

def parse_tournament_text(text):
    """Parse tournament text and extract structured data based on detected format."""
    # Detect format
    format_type = detect_format(text)
    st.write(f"Detected format: {format_type}")
    
    if format_type == "TABULAR" or format_type == "MANUAL_TABULAR":
        return parse_tabular_format(text)
    elif format_type == "CHAMPIONSHIP":
        return parse_championship_format(text)
    elif format_type == "LIST_FORMAT":
        return parse_list_format(text)
    else:
        return parse_simple_format(text)

def parse_list_format(text):
    """Parse the list format with tournament name, course, location, and date range."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    # Skip header line if it exists (e.g., "FUTURE TOURNAMENTS")
    if i < len(lines) and ("TOURNAMENT" in lines[i].upper() or "FUTURE" in lines[i].upper()):
        i += 1
    
    while i < len(lines) - 3:  # Need at least 4 lines for a complete entry
        # Assume pattern: Tournament Name, Course, Location, Date Range
        tournament_name = lines[i]
        
        # Skip to next entry if this doesn't look like a tournament name
        if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', tournament_name):
            i += 1
            continue
            
        if i + 3 < len(lines):
            course_name = lines[i+1]
            location_line = lines[i+2]
            date_line = lines[i+3]
            
            # Parse location for city and state
            location_match = re.search(r'(.*?),\s+([A-Z]{2})(?:\s|$)', location_line)
            city = location_match.group(1) if location_match else ""
            state = location_match.group(2) if location_match else ""
            
            # Check if the next line is a date range
            date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', date_line)
            
            if date_match:
                # Create tournament entry
                tournament = {
                    'Date': standardize_date(date_line),
                    'Name': tournament_name.strip(),
                    'Course': course_name.strip(),
                    'Category': "Men's",  # Default category
                    'City': city.strip(),
                    'State': standardize_state(state.strip()),
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
                
                tournaments.append(tournament)
                
                # Move to next entry (skip the 4 lines we just processed)
                i += 4
            else:
                # Not a valid entry, move to next line
                i += 1
        else:
            # Not enough lines left, move to next line
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
            current_date = standardize_date(f"{month} {day}", "2025")
            
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
            
            # For multi-course tournaments, check if there's another course/location pair
            # This handles special cases like "Apr 28-29" tournaments
            has_another_course = False
            
            # Skip "Leaderboard" and similar lines
            while j < len(lines) and j < i + 10 and lines[j].strip() and ('Leaderboard' in lines[j] or 'View' in lines[j] or 'Info' in lines[j] or 'Register' in lines[j]):
                j += 1
            
            # If we're not at the next date entry, check if there's another course
            if j < len(lines) and j < i + 10 and lines[j].strip():
                next_line = lines[j].strip()
                # If this isn't a date line, it might be another course
                if not re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', next_line):
                    course_parts = re.split(r'\t+|\s{2,}·\s{2,}|\s{2,}', next_line)
                    if course_parts and course_parts[0].strip():
                        # This is likely another course for the same tournament
                        has_another_course = True
            
            # Add the tournament if we have at least a name
            if tournament_data['Name']:
                # Set default category based on name
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
            
            # If this has multiple courses, skip ahead to the next date
            if has_another_course:
                # Skip ahead until we find the next date line
                while j < len(lines):
                    if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', lines[j].strip()):
                        i = j
                        break
                    j += 1
                
                if j >= len(lines):
                    break
            else:
                # Move to next entry which is the next date line
                i = j
                
                # Skip ahead if we're not already at a date line
                if i < len(lines) and not re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', lines[i].strip()):
                    while i < len(lines):
                        if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', lines[i].strip()):
                            break
                        i += 1
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
        # Try alternative parser if the standard one failed
        st.warning("No tournaments found in standard tabular format. Attempting alternative parsing...")
        return parse_tabular_greedy(text)

def parse_tabular_greedy(text):
    """Greedy parser that looks for any date and location patterns in the text."""
    lines = text.split('\n')
    
    tournaments = []
    
    # Start parsing
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for date pattern
        date_match = None
        if line:
            date_match = re.search(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:\-\d{1,2})?', line)
        
        if date_match:
            month, day = date_match.groups()
            current_date = standardize_date(f"{month} {day}", "2025")
            
            # Initialize tournament data
            tournament = {
                'Date': current_date,
                'Name': None,
                'Course': None,
                'City': None,
                'State': None,
                'Zip': None,
                'Category': "Men's"
            }
            
            # Track parsing state
            name_found = False
            course_found = False
            location_found = False
            
            # Look ahead for tournament data within the next 10 lines
            j = i + 1
            while j < min(i + 10, len(lines)) and not (name_found and course_found and location_found):
                next_line = lines[j].strip()
                
                # Skip empty lines and markers
                if not next_line:
                    j += 1
                    continue
                
                # Check if this is another date (new tournament)
                if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', next_line):
                    break
                
                # Skip markers like Leaderboard, Info, etc.
                if next_line in ["Leaderboard", "Info", "T", "M", "View leaderboard", "Register"] or \
                   next_line.startswith("View") or next_line.startswith("Register") or \
                   next_line.startswith("Info") or next_line.startswith("Leaderboard"):
                    j += 1
                    continue
                
                # This might be a tournament name if not found yet and doesn't look like location/course
                if not name_found and not '\t' in next_line and not '  ·  ' in next_line and not ',' in next_line:
                    # Remove "About" suffix
                    tournament['Name'] = re.sub(r'\s+About$', '', next_line)
                    name_found = True
                    j += 1
                    continue
                
                # Look for course name (line with tabs or dot separators)
                if not course_found and ('\t' in next_line or '  ·  ' in next_line):
                    parts = re.split(r'\t+|\s{2,}·\s{2,}|\s{2,}', next_line)
                    if parts and parts[0].strip():
                        tournament['Course'] = parts[0].strip()
                        course_found = True
                    j += 1
                    continue
                
                # Look for city/state pattern if not found yet
                if not location_found and ',' in next_line:
                    location_match = re.search(r'(.*?),\s+([A-Z]{2})(?:\s|$)', next_line)
                    if location_match:
                        city, state = location_match.groups()
                        tournament['City'] = city.strip()
                        tournament['State'] = standardize_state(state.strip())
                        location_found = True
                    j += 1
                    continue
                
                # If we can't categorize this line, just move on
                j += 1
            
            # If we have at least name or course, add the tournament
            if tournament['Name'] or tournament['Course']:
                # If name is missing but course exists, use course as name
                if not tournament['Name'] and tournament['Course']:
                    tournament['Name'] = tournament['Course']
                
                # Determine category based on tournament name
                name = tournament['Name'] or ""
                if "Amateur" in name:
                    tournament['Category'] = "Amateur"
                elif "Senior" in name:
                    tournament['Category'] = "Seniors"
                elif "Women" in name or "Ladies" in name:
                    tournament['Category'] = "Women's"
                elif "Junior" in name:
                    tournament['Category'] = "Junior's"
                
                tournaments.append(tournament)
            
            # Skip ahead to find the next date
            i = j
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
    simple_date_pattern = r'^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})'
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

# Main application layout
st.subheader("Enter Tournament Text Data")

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
May 16 - 18 2025
Wilfred Galbraith Invitational
Anniston Country Club
Anniston, AL
May 30 - June 01 2025
Alabama Women's State Mid-Amateur Championship
Valley Hill Country Club
Huntsville, AL
June 02 - 04 2025"""

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
            
            # Display the raw parsed data
            st.subheader("Parsed Tournament Data")
            st.write(f"Found {len(df)} tournaments")
            
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
            
            # Standardize names
            df = standardize_tournament_names(df)
            
            # Standardize all dates in the Date column (this is the key step!)
            df["Date"] = df["Date"].apply(lambda x: standardize_date(x, year))
            
            # Display parsed data
            st.dataframe(df)
            
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
