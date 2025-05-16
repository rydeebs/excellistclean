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
REQUIRED_COLUMNS = ["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"]

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

def determine_gender(tournament_name):
    """
    Determine gender from tournament name by looking for specific keywords.
    Returns "Women's" or "Men's" based on analysis.
    """
    if not tournament_name:
        return "Men's"  # Default to Men's if no name provided
        
    tournament_name = str(tournament_name).lower()
    
    # Keywords that indicate women's tournaments
    women_keywords = [
        "women", "women's", "womens", "ladies", "ladies'", "girls", "girls'", 
        "empowher", "female", "women's championship", "ladies championship",
        "women's amateur", "ladies amateur", "women's open", "ladies open"
    ]
    
    # Keywords that indicate men's tournaments
    men_keywords = [
        "men", "men's", "mens", "boys", "boys'", "male", "men's championship",
        "men's amateur", "men's open", "senior men", "super senior men"
    ]
    
    # Check for women's indicators first
    for keyword in women_keywords:
        if keyword in tournament_name:
            return "Women's"
    
    # Then check for men's indicators
    for keyword in men_keywords:
        if keyword in tournament_name:
            return "Men's"
    
    # Default to Men's if no gender is specified
    # (this is common in golf where unmarked tournaments are typically men's events)
    return "Men's"

def update_tournament_with_gender_and_type(tournament_data):
    """
    Helper function to add Gender and Type to existing tournament data.
    Can be called from other parsers to standardize this functionality.
    """
    name = tournament_data.get('Name', '')
    
    # Set Gender
    tournament_data['Gender'] = determine_gender(name)
    
    # Set Type if not already set
    if 'Type' not in tournament_data or not tournament_data['Type']:
        if "Championship" in name:
            tournament_data['Type'] = "Championship"
        elif "Qualifier" in name:
            tournament_data['Type'] = "Qualifier"
        else:
            tournament_data['Type'] = "Tournament"
            
    return tournament_data

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

def parse_status_based_format(text):
    """
    Enhanced parser for status-based format with OPEN/CLOSED indicators.
    Specifically handles patterns like:
    OPEN
    closes on
    MON, MAY 26
    5:00 PM PDT
    [Tournament Name]
    View
    [Date]
    [Optional] Next Round
    [Course]
    """
    # Split the text into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    # Define golf course indicators to better distinguish courses from tournament names
    course_indicators = [
        "Golf Course", "GC", "CC", "Country Club", "Golf Club", "Ranch", 
        "Hills Course", "Links", "Resort", "Municipal", "National",
        "Park", "Valley", "Creek", "Dunes", "Trails", "Club"
    ]
    
    while i < len(lines):
        tournament_data = {col: None for col in REQUIRED_COLUMNS}
        
        # Check for status line (OPEN, OPENS, CLOSED, etc.)
        status_keywords = ["OPEN", "OPENS", "CLOSED", "REGISTRATION OPEN", "SOLD OUT", "INVITATION LIST"]
        if i < len(lines) and any(lines[i] == keyword for keyword in status_keywords):
            status = lines[i]  # Store status but don't use it as the name
            i += 1
            
            # Skip "closes on" line if present
            if i < len(lines) and ("closes on" in lines[i].lower() or "registration" in lines[i].lower()):
                i += 1
                
            # Skip date line (usually in format DAY, MONTH DATE)
            if i < len(lines) and re.match(r'^[A-Z]{3},\s+[A-Z]{3,4}\s+\d{1,2}$', lines[i], re.IGNORECASE):
                i += 1
                
            # Skip time line (usually in format TIME TIMEZONE)
            if i < len(lines) and re.match(r'^\d{1,2}:\d{2}\s+[AP]M\s+[A-Z]{3,4}$', lines[i]):
                i += 1
                
            # Now we should be at the tournament name
            # It should not be "View" and not look like a date
            if i < len(lines) and lines[i] != "View" and not re.match(r'^[A-Za-z]{3},\s+[A-Za-z]{3}\s+\d{1,2}', lines[i]):
                tournament_data['Name'] = lines[i].strip()
                i += 1
                
                # Skip "View" link or other action buttons
                if i < len(lines) and (lines[i] == "View" or lines[i] == "Register" or lines[i] == "Details"):
                    i += 1
                    
                # Extract date from date range
                date_value = None
                if i < len(lines) and re.search(r'[A-Za-z]{3},\s+[A-Za-z]{3,4}\s+\d{1,2}', lines[i], re.IGNORECASE):
                    date_line = lines[i]
                    # Extract first date from date range
                    date_parts = date_line.split('-')[0].strip()
                    date_value = ultra_simple_date_extractor(date_parts, year)
                    tournament_data['Date'] = date_value
                    i += 1
                
                # Skip "Next Round" line
                if i < len(lines) and "Next Round:" in lines[i]:
                    i += 1
                    
                # Extract course information with improved logic
                if i < len(lines):
                    course_line = lines[i]
                    
                    # Check if this is a course by looking for course indicators
                    is_likely_course = False
                    for indicator in course_indicators:
                        if indicator in course_line:
                            is_likely_course = True
                            break
                    
                    # If this line looks like a date and we don't have a date yet, use it as date
                    if date_value is None and re.search(r'[A-Za-z]{3},\s+[A-Za-z]{3,4}\s+\d{1,2}', course_line, re.IGNORECASE):
                        date_parts = course_line.split('-')[0].strip()
                        tournament_data['Date'] = ultra_simple_date_extractor(date_parts, year)
                    # If it has course indicators or ends with "Course", it's likely a course
                    elif is_likely_course or course_line.endswith("Course") or course_line.endswith("CC"):
                        tournament_data['Course'] = course_line.strip()
                    # If it doesn't look like a course and we already have a name, it might be additional name info
                    elif tournament_data['Name'] and not tournament_data['Course']:
                        # Check if it's not a "Next Round" line that wasn't caught
                        if "Next Round" not in course_line:
                            # Append to existing name or set as course
                            if any(word in course_line for word in ["Championship", "Tournament", "Series", "Amateur"]):
                                # This looks like part of the tournament name
                                tournament_data['Name'] += " - " + course_line.strip()
                            else:
                                # Assume it's a course
                                tournament_data['Course'] = course_line.strip()
                    # Fallback - treat as course
                    else:
                        tournament_data['Course'] = course_line.strip()
                    i += 1
                
                # Try to determine category from tournament name
                name = tournament_data['Name']
                if name:
                    # Set gender first
                    tournament_data['Gender'] = determine_gender(name)
                    
                    # Now set category
                    name_lower = name.lower()
                    if "amateur" in name_lower and "mid-amateur" not in name_lower:
                        tournament_data['Category'] = "Amateur"
                    elif "mid-amateur" in name_lower:
                        tournament_data['Category'] = "Mid-Amateur"
                    elif "senior" in name_lower and "super senior" not in name_lower:
                        tournament_data['Category'] = "Seniors"
                    elif "super senior" in name_lower:
                        tournament_data['Category'] = "Super Senior"
                    elif "women" in name_lower or "ladies" in name_lower or "girls" in name_lower:
                        tournament_data['Category'] = "Women's"
                    elif "junior" in name_lower or "boys" in name_lower:
                        tournament_data['Category'] = "Junior's"
                    elif "team" in name_lower or "2-man" in name_lower or "four-ball" in name_lower:
                        tournament_data['Category'] = "Team"
                    elif "match play" in name_lower:
                        tournament_data['Category'] = "Match Play"
                    elif "net" in name_lower:
                        tournament_data['Category'] = "Net"
                    elif any(x in name_lower for x in ["championship", "championchip"]):
                        tournament_data['Category'] = "Championship"
                    else:
                        tournament_data['Category'] = "Men's"  # Default category
                
                # Set default state if provided
                if default_state:
                    tournament_data['State'] = default_state
                    
                # Try to extract state from tournament name or course name
                for field in ['Name', 'Course']:
                    if tournament_data[field]:
                        # Look for state name in the field
                        state_name_match = re.search(r'\b(Nevada|NV|California|CA|Oregon|OR|Arizona|AZ|Utah|UT|Idaho|ID)\b', 
                                                   tournament_data[field], re.IGNORECASE)
                        if state_name_match:
                            state_name = state_name_match.group(1).upper()
                            # Convert full state names to codes
                            state_dict = {
                                'NEVADA': 'NV', 'CALIFORNIA': 'CA', 'OREGON': 'OR', 
                                'ARIZONA': 'AZ', 'UTAH': 'UT', 'IDAHO': 'ID'
                            }
                            if state_name in state_dict:
                                tournament_data['State'] = state_dict[state_name]
                            elif len(state_name) == 2:
                                tournament_data['State'] = state_name
                
                # Add tournament to the list if it has at least a name
                if tournament_data['Name']:
                    tournaments.append(tournament_data)
        else:
            # Try to detect tournament entry without OPEN/CLOSED status
            # This handles entries like "2025 Nevada State Men's Net & Senior Men's Net Championship"
            if i < len(lines) and any(keyword in lines[i] for keyword in ["Championship", "Tournament", "Amateur"]):
                tournament_data['Name'] = lines[i].strip()
                i += 1
                
                # Skip "View" line
                if i < len(lines) and lines[i] == "View":
                    i += 1
                
                # Extract date
                if i < len(lines) and re.search(r'[A-Za-z]{3},\s+[A-Za-z]{3,4}\s+\d{1,2}', lines[i], re.IGNORECASE):
                    date_line = lines[i]
                    # Extract first date from date range
                    date_parts = date_line.split('-')[0].strip()
                    tournament_data['Date'] = ultra_simple_date_extractor(date_parts, year)
                    i += 1
                
                # Skip "Next Round" line
                if i < len(lines) and "Next Round:" in lines[i]:
                    i += 1
                
                # Extract course
                if i < len(lines):
                    course_line = lines[i]
                    tournament_data['Course'] = course_line.strip()
                    i += 1
                    
                # Process category and gender
                if tournament_data['Name']:
                    # Set gender
                    tournament_data['Gender'] = determine_gender(tournament_data['Name'])
                    
                    # Set category
                    name_lower = tournament_data['Name'].lower()
                    if "amateur" in name_lower and "mid-amateur" not in name_lower:
                        tournament_data['Category'] = "Amateur"
                    elif "mid-amateur" in name_lower:
                        tournament_data['Category'] = "Mid-Amateur"
                    elif "senior" in name_lower and "super senior" not in name_lower:
                        tournament_data['Category'] = "Seniors"
                    elif "match play" in name_lower:
                        tournament_data['Category'] = "Match Play"
                    elif "net" in name_lower:
                        tournament_data['Category'] = "Net"
                    else:
                        tournament_data['Category'] = "Men's"  # Default category
                    
                    # Set default state
                    tournament_data['State'] = default_state
                    
                    # Add to tournament list
                    tournaments.append(tournament_data)
            else:
                # Move to next line if not a tournament start
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

def parse_gam_championship_format(text):
    """
    Parse format with tournament details in a structured format, 
    with tournament name and date on same line.
    Example:
    2nd GAM Girls' ChampionshipApr 26, 2025 - Apr 27, 2025
    WASHTENAW GOLF CLUB - Ypsilanti
    Type: Junior Championships
    Format: Tournament
    Age Group: Junior
    Gender: Female
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    while i < len(lines):
        # Look for line with tournament name and date together
        # Pattern: Name followed by month abbreviation and day
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        date_pattern = '|'.join(month_names)
        name_date_pattern = f'(.*?)({date_pattern}\\s+\\d{{1,2}},?\\s+\\d{{4}}.*)'
        
        name_date_match = re.search(name_date_pattern, lines[i])
        
        if name_date_match:
            # Extract tournament name and date from combined line
            tournament_name = name_date_match.group(1).strip()
            date_text = name_date_match.group(2).strip()
            
            # Extract first date from date range
            if "-" in date_text:
                first_date = date_text.split("-")[0].strip()
            else:
                first_date = date_text
            
            # Get formatted date
            date_value = ultra_simple_date_extractor(first_date, year)
            
            i += 1
            
            # Skip any note lines about sold out or waitlist
            if i < len(lines) and ("SOLD OUT" in lines[i] or "WAITLIST" in lines[i]):
                i += 1
            
            # Next line should be course and location
            course_location = ""
            course_name = ""
            city = ""
            
            if i < len(lines):
                course_location = lines[i]
                
                # Extract course name and city
                if " - " in course_location:
                    parts = course_location.split(" - ", 1)
                    course_name = parts[0].strip()
                    city = parts[1].strip() if len(parts) > 1 else ""
                else:
                    course_name = course_location
                
                i += 1
            
            # Initialize category and gender with defaults
            category = "Men's"  # Default category
            gender = "Men's"    # Default gender
            
            # Look for Type, Format, Age Group, Gender lines
            while i < len(lines) and i < i + 4:  # Check next 4 lines at most
                if "Type:" in lines[i]:
                    type_line = lines[i].replace("Type:", "").strip()
                    if "Junior" in type_line:
                        category = "Junior's"
                    elif "Qualifier" in type_line:
                        category = "Qualifier"
                    elif "Team" in type_line:
                        category = "Team"
                    i += 1
                    continue
                
                if "Age Group:" in lines[i]:
                    age_line = lines[i].replace("Age Group:", "").strip()
                    if "Junior" in age_line:
                        category = "Junior's"
                    elif "Senior" in age_line:
                        category = "Seniors"
                    elif "Mid" in age_line:
                        category = "Mid-Amateur"
                    elif "Open" in age_line:
                        category = "Open"
                    elif "Mixed" in age_line:
                        category = "Mixed/Couples"
                    i += 1
                    continue
                
                if "Gender:" in lines[i]:
                    gender_line = lines[i].replace("Gender:", "").strip()
                    if "Female" in gender_line or "Women" in gender_line:
                        gender = "Women's"
                    elif "Male" in gender_line or "Men" in gender_line:
                        gender = "Men's"
                    i += 1
                    continue
                
                if "Format:" in lines[i]:
                    i += 1
                    continue
                
                if "Registration" in lines[i]:
                    i += 1
                    continue
                
                # Not a metadata line, break out of this loop
                break
            
            # If we didn't find a gender from metadata, try to determine from tournament name
            if gender == "Men's":
                name_gender = determine_gender(tournament_name)
                if name_gender != "Men's":  # Only override if not default
                    gender = name_gender
            
            # If we didn't find a category from metadata, try to determine from tournament name
            if category == "Men's":
                name_lower = tournament_name.lower()
                if "amateur" in name_lower and "mid-amateur" not in name_lower:
                    category = "Amateur"
                elif "mid-amateur" in name_lower:
                    category = "Mid-Amateur"
                elif "senior" in name_lower:
                    category = "Seniors"
                elif "women" in name_lower or "ladies" in name_lower or "girls" in name_lower:
                    category = "Women's"
                elif "junior" in name_lower or "boys" in name_lower or "girls" in name_lower:
                    category = "Junior's"
                elif "qualifier" in name_lower:
                    category = "Qualifier"
            
            # Determine state from context or default
            state = ""
            # Try to extract state code from city
            if city:
                state_match = re.search(r',\s+([A-Z]{2})$', city)
                if state_match:
                    state = state_match.group(1)
                    city = city[:state_match.start()].strip()
                else:
                    state = default_state if default_state else ""
            else:
                state = default_state if default_state else ""
            
            # Create tournament entry if we have key information
            if tournament_name and date_value:
                tournament = {
                    'Date': date_value,
                    'Name': tournament_name,
                    'Course': course_name,
                    'Category': category,
                    'Gender': gender,
                    'City': city,
                    'State': state,
                    'Zip': None
                }
                
                tournaments.append(tournament)
                
                # Skip remaining registration and event details lines
                while i < len(lines) and ("Registration" in lines[i] or "Deadline" in lines[i]):
                    i += 1
        else:
            # Not a tournament name/date line, move to next line
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in GAM championship format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def parse_usga_qualifier_format(text):
    """
    Parse USGA qualifier format with tournament name, View, date, and course.
    Example:
    2025 US Girls' Junior Amateur Qualifying
    View
    Thu, Jun 12, 2025
    Oak Glen Golf Course
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    # Month dictionary for date conversion
    month_dict = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    while i + 3 < len(lines):  # Need at least 4 lines for a complete entry
        # Check if this looks like a tournament entry (second line is "View")
        if i + 1 < len(lines) and lines[i + 1] == "View":
            # Extract information
            tournament_name = lines[i]
            date_line = lines[i + 2] if i + 2 < len(lines) else ""
            course_name = lines[i + 3] if i + 3 < len(lines) else ""
            
            # Process date line (Thu, Jun 12, 2025 -> Jun 12, 2025)
            date_value = None
            date_match = re.search(r'^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4}), date_line)
            if date_match:
                month, day, yr = date_match.groups()
                date_value = f"{yr}-{month_dict[month]}-{day.zfill(2)}"
            else:
                # Fallback to general date extractor
                date_value = ultra_simple_date_extractor(date_line, year)
            
            # Determine category and gender based on name
            category = "Amateur"
            gender = "Men's"
            
            if "Women's" in tournament_name or "Girls'" in tournament_name:
                gender = "Women's"
                if "Girls'" in tournament_name:
                    category = "Junior's"
                elif "Senior Women's" in tournament_name:
                    category = "Seniors"
                else:
                    category = "Women's"
            
            if "Senior" in tournament_name and "Women's" not in tournament_name:
                category = "Seniors"
            elif "Junior" in tournament_name and "Girls'" not in tournament_name:
                category = "Junior's"
            elif "Mid-Amateur" in tournament_name:
                category = "Mid-Amateur"
            elif "Four-Ball" in tournament_name:
                category = "Four-Ball"
                
            # Create tournament entry
            if date_value and course_name:
                tournament = {
                    'Date': date_value,
                    'Name': tournament_name.strip(),
                    'Course': course_name.strip(),
                    'Category': category,
                    'Gender': gender,
                    'City': None,
                    'State': default_state if default_state else None,
                    'Zip': None
                }
                
                tournaments.append(tournament)
            
            # Move to the next entry (skip 4 lines)
            i += 4
        else:
            # Pattern doesn't match, try next line
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in USGA qualifier format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def parse_usga_qualifier_expanded_format(text):
    """
    Parse expanded USGA qualifier format with tournament name, date, course and golfers.
    This handles the pattern:
    Tournament Name
    Date Line (like Mon, Jun 2, 2025)
    Course: <Course Name>
    Golfers: <Count>
    View
    """
    # Split the text into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    while i < len(lines):
        # Look for tournament name followed by date line with day of week
        if (i < len(lines) and 
            i+1 < len(lines) and 
            i+2 < len(lines) and 
            re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+[A-Za-z]{3}\s+\d{1,2},\s+\d{4}, lines[i+1])):
            
            tournament_data = {col: None for col in REQUIRED_COLUMNS}
            
            # This is a tournament name
            tournament_data['Name'] = lines[i].strip()
            
            # Next line is date
            date_line = lines[i+1]
            tournament_data['Date'] = ultra_simple_date_extractor(date_line, year)
            
            # Look for course information
            course_line_idx = -1
            for j in range(i+2, min(i+5, len(lines))):
                if lines[j].startswith("Course:"):
                    course_line_idx = j
                    course_name = lines[j][len("Course:"):].strip()
                    tournament_data['Course'] = course_name
                    break
            
            # Set default category and gender based on tournament name
            name = tournament_data['Name']
            if name:
                # Category
                if "Amateur" in name and "Four-Ball" not in name:
                    tournament_data['Category'] = "Amateur"
                elif "Senior" in name:
                    tournament_data['Category'] = "Seniors"
                elif "Women" in name or "Ladies" in name or "Girls'" in name:
                    tournament_data['Category'] = "Women's"
                elif "Junior" in name or "Boys'" in name:
                    tournament_data['Category'] = "Junior's"
                elif "Mid-Amateur" in name:
                    tournament_data['Category'] = "Mid-Amateur"
                elif "Four-Ball" in name:
                    tournament_data['Category'] = "Four-Ball"
                else:
                    tournament_data['Category'] = "Men's"  # Default category
                
                # Gender
                tournament_data['Gender'] = determine_gender(name)
            
            # Set default state if provided
            if default_state:
                tournament_data['State'] = default_state
            
            # Skip ahead to after the View line or end of this entry
            view_line_idx = -1
            for j in range(i+2, min(i+7, len(lines))):
                if lines[j] == "View":
                    view_line_idx = j
                    i = j + 1  # Set i to after the View line
                    break
            
            # If we didn't find a View line, just skip ahead a reasonable amount
            if view_line_idx == -1:
                i += 5
            
            # Add tournament to the list if we have essential data
            if tournament_data['Name'] and tournament_data['Date']:
                tournaments.append(tournament_data)
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

def parse_four_line_format(text):
    """
    Parse format with tournament details on four separate lines:
    Line 1: Tournament name
    Line 2: Course name
    Line 3: City, State
    Line 4: Date
    
    Tournaments are separated by blank lines.
    """
    # Split the text into lines
    lines = [line.strip() for line in text.split('\n')]
    
    tournaments = []
    i = 0
    
    while i < len(lines):
        # Skip blank lines
        if not lines[i]:
            i += 1
            continue
        
        # Check if we have at least 4 more lines (name, course, location, date)
        if i + 3 < len(lines):
            tournament_name = lines[i]
            course_name = lines[i+1]
            location = lines[i+2]
            date_line = lines[i+3]
            
            # Make sure we have actual content in each line
            if tournament_name and course_name and location and date_line:
                # Parse location for city and state
                location_match = re.search(r'(.*?),\s+([A-Z]{2})', location)
                city = ""
                state = ""
                if location_match:
                    city = location_match.group(1).strip()
                    state = location_match.group(2).strip()
                else:
                    # If no match, use default state if provided
                    state = default_state if default_state else ""
                
                # Extract date
                date_value = ultra_simple_date_extractor(date_line, year)
                
                if date_value:
                    # Create tournament entry
                    tournament = {
                        'Date': date_value,
                        'Name': tournament_name.strip(),
                        'Course': course_name.strip(),
                        'Category': "Men's",  # Default category
                        'Gender': determine_gender(tournament_name),
                        'City': city,
                        'State': state,
                        'Zip': None
                    }
                    
                    # Determine category based on tournament name
                    name = tournament_name.lower()
                    if "amateur" in name:
                        tournament['Category'] = "Amateur"
                    elif "senior" in name:
                        tournament['Category'] = "Seniors"
                    elif "women" in name or "ladies" in name:
                        tournament['Category'] = "Women's"
                    elif "junior" in name or "boys" in name or "girls" in name:
                        tournament['Category'] = "Junior's"
                    elif "mid-amateur" in name:
                        tournament['Category'] = "Mid-Amateur"
                    elif "four-ball" in name:
                        tournament['Category'] = "Four-Ball"
                    elif "father" in name and "son" in name:
                        tournament['Category'] = "Mixed/Couples"
                    
                    tournaments.append(tournament)
            
            # Move to the next block (skip the 4 lines we just processed)
            i += 4
        else:
            # Not enough lines left to form a complete entry
            break
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in four-line format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def parse_montana_format_direct(text):
    """
    Direct manual parser for Montana format that carefully handles the dash separator.
    Pattern:
    Line 1: Tournament name
    Line 2: Date - Course, City, State  (with dash separator after date)
    Line 3: Categories
    """
    # Split into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Create result container
    tournaments = []
    
    # Skip month headers
    month_headers = ["january", "february", "march", "april", "may", "june", 
                   "july", "august", "september", "october", "november", "december"]
    
    # Process in strict groups of 3 lines
    i = 0
    while i < len(lines):
        # Skip month headers
        if i < len(lines) and lines[i].lower() in month_headers and len(lines[i]) < 10:
            i += 1
            continue
        
        # Check if we have enough lines for a complete tournament
        if i + 2 < len(lines):
            # Get the three lines
            tournament_name = lines[i]
            date_course_line = lines[i+1]
            category_line = lines[i+2]
            
            # KEY PART: Split the second line at the dash
            dash_parts = date_course_line.split(" - ", 1)  # Split at first dash only
            
            if len(dash_parts) == 2:
                # Successfully split at the dash
                date_part = dash_parts[0].strip()
                location_part = dash_parts[1].strip()
                
                # Process date
                date_value = ultra_simple_date_extractor(date_part, year)
                
                # Parse location: Course, City, State
                course = ""
                city = ""
                state = ""
                
                location_parts = location_part.split(",")
                if location_parts:
                    course = location_parts[0].strip()
                    
                    if len(location_parts) >= 3:
                        city = location_parts[1].strip() 
                        state = location_parts[2].strip()
                    elif len(location_parts) == 2:
                        last_part = location_parts[1].strip()
                        state_match = re.search(r'([A-Z]{2}), last_part)
                        if state_match:
                            state = state_match.group(1)
                            city = last_part[:-(len(state))].strip()
                        else:
                            city = last_part
                
                # Process category line
                category_line_lower = category_line.lower()
                
                # Default values
                primary_category = "Men's"
                gender = "Men's"
                
                # Determine category
                if "juniors" in category_line_lower or "junior" in category_line_lower:
                    primary_category = "Junior's"
                elif "seniors" in category_line_lower or "senior" in category_line_lower:
                    primary_category = "Seniors"
                elif "pro am" in category_line_lower or "pro-am" in category_line_lower:
                    primary_category = "Pro-Am"
                elif "team event" in category_line_lower:
                    primary_category = "Team"
                
                # Determine gender
                if "womens" in category_line_lower and not "mens" in category_line_lower:
                    gender = "Women's"
                elif "womens" in category_line_lower and "mens" in category_line_lower:
                    gender = "Mixed"
                
                # Check tournament name for overrides
                name_lower = tournament_name.lower()
                if "women" in name_lower or "ladies" in name_lower:
                    gender = "Women's"
                if "amateur" in name_lower:
                    primary_category = "Amateur"
                if "match play" in name_lower:
                    primary_category = "Match Play"
                
                # Create tournament entry with the correct Name
                if date_value:
                    tournament = {
                        'Date': date_value,
                        'Name': tournament_name,  # Name from first line
                        'Course': course,
                        'Category': primary_category,
                        'Gender': gender,
                        'City': city,
                        'State': state if state else (default_state if default_state else None),
                        'Zip': None
                    }
                    
                    tournaments.append(tournament)
                    
                    # Skip to next tournament (3 lines)
                    i += 3
                else:
                    i += 1
            else:
                i += 1
        else:
            # Not enough lines left
            i += 1
    
    # Check if we found any tournaments
    if tournaments:
        # Create the DataFrame with a specific column order
        columns = ['Date', 'Name', 'Course', 'Category', 'Gender', 'City', 'State', 'Zip']
        tournaments_df = pd.DataFrame(tournaments, columns=columns)
        
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def detect_format(text):
    """Detect which format the text is in."""
    # Split the text into lines and check for patterns
    lines = [line.strip() for line in text.split('\n')]
    
    # Check for status-based format with OPEN/CLOSED and View patterns
    open_count = 0
    view_count = 0
    closes_on_count = 0
    
    for i in range(len(lines)):
        if lines[i] == "OPEN" or lines[i] == "CLOSED":
            open_count += 1
        if lines[i] == "View":
            view_count += 1
        if i > 0 and "closes on" in lines[i].lower():
            closes_on_count += 1
    
    # Strong indicator for status-based format like the example provided
    if open_count >= 1 and view_count >= 1 and closes_on_count >= 1:
        return "STATUS_BASED_FORMAT"

    # Check for Montana format with 3-line pattern: name, date-course, categories
    montana_pattern_count = 0
    for i in range(len(lines) - 2):
        if (len(lines[i]) > 5 and  # Tournament name
            " - " in lines[i+1] and  # Date - Course with dash separator
            re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\s+-', lines[i+1]) and  # Date format before dash
            any(category in lines[i+2].lower() for category in ["mens", "womens", "seniors", "juniors", "team", "pro", "am"])):  # Categories
            montana_pattern_count += 1
    
    if montana_pattern_count >= 1:
        return "MONTANA_FORMAT"

    # Check for USGA qualifier format (tournament, View, date, course)
    usga_pattern_count = 0
    for i in range(len(lines) - 3):
        if (len(lines[i]) > 5 and 
            i+1 < len(lines) and lines[i+1] == "View" and
            i+2 < len(lines) and re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+', lines[i+2]) and
            i+3 < len(lines) and len(lines[i+3]) > 5):
            usga_pattern_count += 1
    
    if usga_pattern_count >= 1:
        return "USGA_QUALIFIER_FORMAT"
        
    # Check for expanded USGA qualifier format with "Course:" and "Golfers:" lines
    course_prefix_count = 0
    golfers_prefix_count = 0
    
    for i in range(len(lines)):
        if lines[i].startswith("Course:"):
            course_prefix_count += 1
        if lines[i].startswith("Golfers:"):
            golfers_prefix_count += 1
    
    if course_prefix_count >= 1 and golfers_prefix_count >= 1:
        return "USGA_QUALIFIER_EXPANDED_FORMAT"
        
    # Check for GAM championship format with Type, Format, Age Group, Gender on separate lines
    type_format_count = 0
    registration_count = 0
    
    for line in lines:
        if line.startswith("Type:") or line.startswith("Format:") or line.startswith("Age Group:") or line.startswith("Gender:"):
            type_format_count += 1
        if line.startswith("Registration Opens:") or line.startswith("Registration Deadline:"):
            registration_count += 1
    
    if type_format_count >= 3:
        return "GAM_CHAMPIONSHIP_FORMAT"

    # Check for four-line format (name, course, location, date)
    four_line_pattern_count = 0
    i = 0
    
    while i < len(lines):
        # Skip blank lines
        if not lines[i]:
            i += 1
            continue
            
        # Check if we have 4 non-empty lines followed by a blank line or end of text
        if (i + 3 < len(lines) and 
            all(lines[i+j] for j in range(4)) and  # All 4 lines have content
            (i + 4 >= len(lines) or not lines[i+4])):  # Followed by blank line or end
            
            # Check if 3rd line looks like a location (City, ST)
            if re.search(r'.*?,\s+[A-Z]{2}', lines[i+2]):
                # Check if 4th line looks like a date
                date_line = lines[i+3]
                month_names = ["January", "February", "March", "April", "May", "June", "July", "August", 
                              "September", "October", "November", "December", "Jan", "Feb", "Mar", 
                              "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                if any(month in date_line for month in month_names):
                    four_line_pattern_count += 1
            
            # Skip ahead to the next block
            i += 5
        else:
            i += 1
    
    if four_line_pattern_count >= 1:
        return "FOUR_LINE_FORMAT"
    
    # Default to status-based format if we have "Championship" and "View" patterns
    championship_count = 0
    for line in lines:
        if "Championship" in line:
            championship_count += 1
    
    if championship_count >= 1 and view_count >= 1:
        return "STATUS_BASED_FORMAT"
    
    # Fallback to STATUS_BASED_FORMAT if there's a decent number of "View" lines
    # This is a good general parser for many tournament formats
    if view_count >= 2:
        return "STATUS_BASED_FORMAT"
    
    # If all else fails, try status-based format (it's the most robust general parser)
    return "STATUS_BASED_FORMAT"

def parse_tournament_text(text):
    """Parse tournament text and extract structured data based on detected format."""
    # Detect format
    format_type = detect_format(text)
    st.write(f"Detected format: {format_type}")
    
    # Parse based on detected format
    if format_type == "STATUS_BASED_FORMAT":
        return parse_status_based_format(text)
    elif format_type == "MONTANA_FORMAT":
        return parse_montana_format_direct(text)
    elif format_type == "USGA_QUALIFIER_FORMAT":
        return parse_usga_qualifier_format(text)
    elif format_type == "USGA_QUALIFIER_EXPANDED_FORMAT":
        return parse_usga_qualifier_expanded_format(text)
    elif format_type == "GAM_CHAMPIONSHIP_FORMAT":
        return parse_gam_championship_format(text)
    elif format_type == "FOUR_LINE_FORMAT":
        return parse_four_line_format(text)
    else:
        # Fallback to status-based format (most robust)
        return parse_status_based_format(text)

def ensure_column_order(df):
    """
    Ensure DataFrame columns are in the correct order and all required columns exist.
    """
    # Make sure all required columns exist
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = None
    
    # Reorder columns - put required columns first, then any additional columns
    ordered_columns = REQUIRED_COLUMNS + [col for col in df.columns if col not in REQUIRED_COLUMNS]
    
    # Return the properly ordered DataFrame
    return df[ordered_columns]

# Example selector
format_option = st.selectbox(
    "Select an example format:",
    ["NNGA Schedule Format", "USGA Qualifiers Format", "Montana Format", 
     "Four-Line Format", "GAM Championship Format"]
)

# Default text examples
nnga_format_example = """OPEN
closes on
MON, MAY  26
5:00 PM PDT
2025 Men's NNGA Team Series - BattleBorn 2-Man
View
Sat, May 31, 2025
Empire Ranch Golf Course
OPEN
closes on
MON, JUN  02
5:00 PM PDT
2025 NNGA Men's Mid-Amateur Championship & Final qualifying event for PAC Coast Amateur Champ
View
Sat, Jun 7 - Sun, Jun 8, 2025
Next Round: Sat, Jun 7, 2025
Sierra Sage Golf Course
OPEN
closes on
TUE, JUN  10
5:00 PM PDT
2025 NNGA Team Series at Winnemucca
View
Sat, Jun 14 - Sun, Jun 15, 2025
Next Round: Sat, Jun 14, 2025
Winnemucca Golf Course
2025 Nevada State Men's Net & Senior Men's Net Championship
View
Sat, Jul 12 - Mon, Jul 14, 2025
Next Round: Sat, Jul 12, 2025
Red Hawk - Hills Course"""

usga_format_example = """2025 U.S. Senior Open Final Qualifier - Mesa CC
View
Mon, Jun 2, 2025
Mesa Country Club
2025 U.S. Girls' Junior Amateur Qualifier - Alta Mesa
View
Mon, Jun 9, 2025
Alta Mesa Golf Club
2025 U.S. Junior Amateur Qualifier - Tatum Ranch
View
Mon, Jun 9, 2025
Tatum Ranch Golf Club"""

montana_format_example = """Montana State Amateur
July 17, 2025 - Riverside Country Club, Bozeman, MT
Mens Amateur Championship
Montana Women's Amateur
July 17, 2025 - Riverside Country Club, Bozeman, MT
Womens Amateur Championship
Montana Mid-Amateur Championship
August 7, 2025 - Bill Roberts Golf Course, Helena, MT
Mens Mid-Amateur Championship"""

four_line_format_example = """Alabama State Senior & Super Senior Amateur Championship
Musgrove Country Club
Jasper, AL
May 16, 2025

Wilfred Galbraith Invitational
Anniston Country Club
Anniston, AL
May 30, 2025

Alabama Women's State Mid-Amateur Championship
Valley Hill Country Club
Huntsville, AL
June 02, 2025"""

gam_format_example = """2nd GAM Girls' ChampionshipApr 26, 2025 - Apr 27, 2025
WASHTENAW GOLF CLUB - Ypsilanti
Type: Junior Championships
Format: Tournament
Age Group: Junior
Gender: Female

Michigan Mid-Amateur ChampionshipJul 19, 2025 - Jul 21, 2025
Eagle Eye Golf Club - East Lansing
Type: Mid-Amateur
Format: Tournament
Age Group: Mid-Amateur
Gender: Male"""

# Select the default text based on the chosen format
if format_option == "NNGA Schedule Format":
    default_text = nnga_format_example
elif format_option == "USGA Qualifiers Format":
    default_text = usga_format_example
elif format_option == "Montana Format":
    default_text = montana_format_example
elif format_option == "Four-Line Format":
    default_text = four_line_format_example
else:  # GAM Championship Format
    default_text = gam_format_example

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
            # Add a separator for clarity
            st.markdown("---")
            st.markdown("## Processing Tournament Data")
            
            # Parse the tournament text
            df = parse_tournament_text(tournament_text)
            
            # Check if DataFrame is empty
            if df.empty:
                st.error("No tournaments could be extracted from the text. Please check the format.")
                # Create an empty DataFrame with all required columns
                df = pd.DataFrame(columns=REQUIRED_COLUMNS)
            else:
                # Print DataFrame information
                st.write("### DataFrame Details")
                st.write(f"DataFrame shape: {df.shape}")
                st.write(f"DataFrame columns: {df.columns.tolist()}")
                
                # Ensure all required columns exist
                for col in REQUIRED_COLUMNS:
                    if col not in df.columns:
                        st.warning(f"Adding missing column: {col}")
                        df[col] = None
                
                # Ensure Name column has values
                if 'Name' in df.columns:
                    empty_names = df['Name'].isnull() | (df['Name'] == '')
                    if empty_names.any():
                        st.warning(f"Found {empty_names.sum()} rows with empty Name values")
                        # Fix empty names with Course values if available
                        if 'Course' in df.columns:
                            df.loc[empty_names, 'Name'] = df.loc[empty_names, 'Course'] + " Tournament"
                
                # Ensure correct column order
                df = ensure_column_order(df)
            
            # Add a separator for clarity
            st.markdown("---")
            st.markdown("## Final Results")
            
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
        st.error("Please enter tournament text data.")import streamlit as st