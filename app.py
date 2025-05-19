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
    """Convert state names to two-letter abbreviations, handling all 50 states plus DC."""
    if not state_str:
        return None
        
    state_str = str(state_str).strip().upper()
    
    # Dictionary of state names to abbreviations
    state_dict = {
        'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR',
        'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
        'DISTRICT OF COLUMBIA': 'DC', 'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI',
        'IDAHO': 'ID', 'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA',
        'KANSAS': 'KS', 'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME',
        'MARYLAND': 'MD', 'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN',
        'MISSISSIPPI': 'MS', 'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE',
        'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM',
        'NEW YORK': 'NY', 'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH',
        'OKLAHOMA': 'OK', 'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI',
        'SOUTH CAROLINA': 'SC', 'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX',
        'UTAH': 'UT', 'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA',
        'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY',
        # Common variations and abbreviations
        'WASH': 'WA', 'PENN': 'PA', 'PENNA': 'PA', 'MASS': 'MA', 'TENN': 'TN', 
        'CALIF': 'CA', 'COLO': 'CO', 'FLA': 'FL', 'ILL': 'IL', 'MICH': 'MI', 
        'MINN': 'MN', 'MISS': 'MS', 'MONT': 'MT', 'OKLA': 'OK', 'ORE': 'OR', 
        'WASH DC': 'DC', 'D.C.': 'DC', 'WASH D.C.': 'DC',
        # British Columbia and Canadian provinces (since some tournaments are there)
        'BRITISH COLUMBIA': 'BC', 'ALBERTA': 'AB', 'SASKATCHEWAN': 'SK',
        'MANITOBA': 'MB', 'ONTARIO': 'ON', 'QUEBEC': 'QC', 'NEW BRUNSWICK': 'NB',
        'NOVA SCOTIA': 'NS', 'PRINCE EDWARD ISLAND': 'PE', 'NEWFOUNDLAND': 'NL',
        'YUKON': 'YT', 'NORTHWEST TERRITORIES': 'NT', 'NUNAVUT': 'NU'
    }
    
    # If already a valid abbreviation
    if len(state_str) == 2:
        # Check if it's a valid state code
        valid_states = set(state_dict.values())
        if state_str in valid_states:
            return state_str
        return state_str  # Return as-is if not recognized but right length
    
    # If it's a full state name or variation
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
    Parse tournament format with status indicators and explicit tournament names.
    This format handles patterns like:
    OPEN/OPENS/CLOSED
    [optional] closes on
    [optional] DAY, MONTH DATE
    [optional] TIME TIMEZONE
    Tournament Name
    View
    Start Date - End Date
    [optional] Next Round info
    Course
    
    This works for any state, not just Arizona.
    """
    # Split the text into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
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
            if i < len(lines) and re.match(r'^[A-Z]{3},\s+[A-Z]{3}\s+\d{1,2}$', lines[i]):
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
                if i < len(lines) and re.search(r'[A-Za-z]{3},\s+[A-Za-z]{3}\s+\d{1,2}', lines[i]):
                    date_line = lines[i]
                    # Extract first date from date range
                    date_parts = date_line.split('-')[0].strip()
                    date_value = ultra_simple_date_extractor(date_parts, year)
                    tournament_data['Date'] = date_value
                    i += 1
                
                # Skip "Next Round" line
                if i < len(lines) and "Next Round:" in lines[i]:
                    i += 1
                    
                # Extract course information
                if i < len(lines):
                    course_line = lines[i]
                    # If this line looks like a date and we don't have a date yet, use it as date
                    if date_value is None and re.search(r'[A-Za-z]{3},\s+[A-Za-z]{3}\s+\d{1,2}', course_line):
                        date_parts = course_line.split('-')[0].strip()
                        tournament_data['Date'] = ultra_simple_date_extractor(date_parts, year)
                    else:
                        tournament_data['Course'] = course_line.strip()
                    i += 1
                
                # Set default category based on tournament name
                name = tournament_data['Name']
                if name:
                    if "Amateur" in name:
                        tournament_data['Category'] = "Amateur"
                    elif "Senior" in name or "Mid-Amateur" in name:
                        tournament_data['Category'] = "Seniors"
                    elif "Women" in name or "Ladies" in name:
                        tournament_data['Category'] = "Women's"
                    elif "Junior" in name or "Boys'" in name or "Girls'" in name:
                        tournament_data['Category'] = "Junior's"
                    elif any(x in name for x in ["Father", "Son", "Parent", "Child", "Mother", "Daughter", "Family", "Mixed", "Stix"]):
                        tournament_data['Category'] = "Mixed/Couples"
                    elif "EmpowHER" in name:  # Special case for the EmpowHER Classic
                        tournament_data['Category'] = "Women's"
                    else:
                        tournament_data['Category'] = "Men's"  # Default category
                
                # Set default state if provided
                if default_state:
                    tournament_data['State'] = default_state
                    
                # Try to extract state from tournament name
                state_match = re.search(r'\b([A-Z]{2})\b', name) if name else None
                state_name_match = re.search(r'(\b(?:Arizona|Alabama|Alaska|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New\s+Hampshire|New\s+Jersey|New\s+Mexico|New\s+York|North\s+Carolina|North\s+Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode\s+Island|South\s+Carolina|South\s+Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West\s+Virginia|Wisconsin|Wyoming)\b)', name) if name else None
                
                if state_match:
                    potential_state = state_match.group(1)
                    # Verify it's a valid state code
                    valid_states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                                   "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                                   "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                                   "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                                   "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"]
                    if potential_state in valid_states:
                        tournament_data['State'] = potential_state
                elif state_name_match:
                    # Convert state name to code
                    state_name = state_name_match.group(1)
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
                    tournament_data['State'] = state_dict.get(state_name.upper(), None)
                
                # Add tournament to the list if it has at least a name
                if tournament_data['Name']:
                    tournaments.append(tournament_data)
            else:
                # If we don't find what we expect, move to next line
                i += 1
        else:
            # Move to next line if not at a status line
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
    Modified to ensure all tournaments are captured correctly.
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
    
    # Process lines in blocks of 4
    while i + 3 < len(lines):  # Need at least 4 lines for a complete entry
        # Check if this pattern matches the expected format
        if lines[i+1] == "View" and re.search(r'^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),', lines[i+2]):
            # Extract information
            tournament_name = lines[i]
            date_line = lines[i+2]
            course_name = lines[i+3]
            
            # Process date line (Thu, Jun 12, 2025 -> Jun 12, 2025)
            date_value = None
            date_match = re.search(r'^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})$', date_line)
            
            if date_match:
                month, day, yr = date_match.groups()
                date_value = f"{yr}-{month_dict[month]}-{day.zfill(2)}"
            else:
                # Try another date pattern for date ranges
                range_match = re.search(r'^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+-\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+(\d{4})$', date_line)
                if range_match:
                    month, day, yr = range_match.groups()
                    date_value = f"{yr}-{month_dict[month]}-{day.zfill(2)}"
                else:
                    # Try a simpler pattern for date ranges
                    simple_match = re.search(r'^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+-\s+(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+(\d{4})$', date_line)
                    if simple_match:
                        month, day, yr = simple_match.groups()
                        date_value = f"{yr}-{month_dict[month]}-{day.zfill(2)}"
                    else:
                        # Last fallback - use ultra_simple_date_extractor
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
            elif "Four-Ball" in tournament_name or "2-Man" in tournament_name:
                category = "Four-Ball"
            elif "Match Play" in tournament_name:
                category = "Match Play"
            elif "Amateur" in tournament_name and "Mid-Amateur" not in tournament_name:
                category = "Amateur"
                
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
        st.write(f"Found {len(tournaments)} tournaments in USGA qualifier format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
def parse_usga_view_format(text):
    """
    Special parser for USGA format with tournament, View, date, course pattern.
    Handles formats like:
    
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
    
    # Process lines in groups of 4
    while i <= len(lines) - 4:  # Need at least 4 lines
        tournament_name = lines[i]
        view_line = lines[i + 1]
        date_line = lines[i + 2]
        course_name = lines[i + 3]
        
        # Check if this is a USGA tournament entry (second line is "View")
        if view_line == "View":
            # Extract date components from date line
            date_match = re.search(r'^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4})$', date_line)
            
            if date_match:
                month, day, yr = date_match.groups()
                date_value = f"{yr}-{month_dict[month]}-{day.zfill(2)}"
                
                # Determine category based on tournament name
                category = "Amateur"
                if "Senior" in tournament_name and "Women's" not in tournament_name:
                    category = "Seniors"
                elif "Junior" in tournament_name or "Girls'" in tournament_name:
                    category = "Junior's" 
                elif "Mid-Amateur" in tournament_name:
                    category = "Mid-Amateur"
                elif "Four-Ball" in tournament_name:
                    category = "Four-Ball"
                elif "Women's" in tournament_name:
                    category = "Women's"
                
                # Determine gender based on tournament name
                gender = "Men's"
                if "Women's" in tournament_name or "Girls'" in tournament_name:
                    gender = "Women's"
                
                # Create tournament entry
                tournament = {
                    'Date': date_value,
                    'Name': tournament_name,
                    'Course': course_name,
                    'Category': category,
                    'Gender': gender,
                    'City': None,
                    'State': default_state if default_state else None,
                    'Zip': None
                }
                
                tournaments.append(tournament)
            
            # Always move to next group of 4 lines if the pattern matched
            i += 4
        else:
            # Try next line if pattern doesn't match
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Found {len(tournaments)} tournaments in USGA view format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
        
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
def parse_amateur_golf_format_improved(text, default_year="2025", default_state=None):
    """
    Improved parser for amateur golf tournaments with the 5-line repeating pattern:
    
    Line 1: Course Name
    Line 2: Tournament Name
    Line 3: Course Name (repeated)
    Line 4: City, State
    Line 5: Date Range
    
    This format is common across many state golf associations.
    
    Arguments:
    text -- The raw tournament text
    default_year -- Default year to use if not specified in text
    default_state -- Default state to use if not specified in text
    
    Returns:
    DataFrame with parsed tournament data
    """
    import re
    import pandas as pd
    
    # Process text into lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Month mapping
    month_map = {
        'Jan': '01', 'January': '01',
        'Feb': '02', 'February': '02',
        'Mar': '03', 'March': '03',
        'Apr': '04', 'April': '04',
        'May': '05',
        'Jun': '06', 'June': '06',
        'Jul': '07', 'July': '07',
        'Aug': '08', 'August': '08',
        'Sep': '09', 'Sept': '09', 'September': '09',
        'Oct': '10', 'October': '10',
        'Nov': '11', 'November': '11',
        'Dec': '12', 'December': '12'
    }
    
    tournaments = []
    
    # Debug output
    st.write(f"Amateur Golf format parser: Processing {len(lines)} lines")
    
    # Process in blocks of 5 lines
    total_blocks = len(lines) // 5
    st.write(f"Found {total_blocks} potential tournament blocks")
    
    # Process each block of 5 lines
    for i in range(0, len(lines), 5):
        # Skip if we don't have a complete block of 5 lines
        if i + 4 >= len(lines):
            break
            
        try:
            # Extract the 5 lines for this tournament
            course1 = lines[i]
            tournament_name = lines[i+1]
            course2 = lines[i+2]
            location = lines[i+3]
            date_range = lines[i+4]
            
            # Debug the current block
            if i < 30 or i % 50 == 0:  # Show details for first few blocks and then periodically
                st.write(f"Processing block {i//5 + 1}:")
                st.write(f"  Course: {course1}")
                st.write(f"  Name: {tournament_name}")
                st.write(f"  Location: {location}")
                st.write(f"  Date: {date_range}")
            
            # Extract city and state from location line
            city = None
            state = default_state
            
            location_match = re.search(r'(.*?),\s+([A-Z]{2})$', location)
            if location_match:
                city = location_match.group(1).strip()
                state = location_match.group(2).strip()
            
            # Extract date from date range
            date_value = None
            
            # Try different date patterns
            # Pattern 1: "May 28, 2025 - May 28, 2025"
            date_match1 = re.search(r'([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})', date_range)
            
            # Pattern 2: "May 28 - May 29, 2025"
            date_match2 = re.search(r'([A-Za-z]+)\s+(\d{1,2})\s+-\s+[A-Za-z]+\s+\d{1,2},\s+(\d{4})', date_range)
            
            # Pattern 3: "May 28 - 29, 2025"
            date_match3 = re.search(r'([A-Za-z]+)\s+(\d{1,2})\s+-\s+\d{1,2},\s+(\d{4})', date_range)
            
            if date_match1:
                month_name = date_match1.group(1)
                day = date_match1.group(2)
                year = date_match1.group(3)
                
                # Get month number
                month = month_map.get(month_name[:3], '01')
                
                # Format date
                date_value = f"{year}-{month}-{day.zfill(2)}"
            elif date_match2:
                parts = date_range.split(" - ")
                first_date = parts[0].strip()
                month_day = first_date.split(" ")
                month_name = month_day[0]
                day = month_day[1]
                year_match = re.search(r'(\d{4})', date_range)
                year = year_match.group(1) if year_match else default_year
                
                # Get month number
                month = month_map.get(month_name[:3], '01')
                
                # Format date
                date_value = f"{year}-{month}-{day.zfill(2)}"
            elif date_match3:
                parts = date_range.split(" - ")
                first_date = parts[0].strip()
                month_day = first_date.split(" ")
                month_name = month_day[0]
                day = month_day[1]
                year_match = re.search(r'(\d{4})', date_range)
                year = year_match.group(1) if year_match else default_year
                
                # Get month number
                month = month_map.get(month_name[:3], '01')
                
                # Format date
                date_value = f"{year}-{month}-{day.zfill(2)}"
            else:
                # Fallback: try a simple extraction
                for month_name in month_map.keys():
                    if month_name in date_range:
                        day_match = re.search(fr'{month_name}\s+(\d{{1,2}})', date_range)
                        if day_match:
                            day = day_match.group(1)
                            year_match = re.search(r'(\d{4})', date_range)
                            year = year_match.group(1) if year_match else default_year
                            month = month_map.get(month_name[:3], '01')
                            date_value = f"{year}-{month}-{day.zfill(2)}"
                            break
            
            # Only proceed if we have a valid date
            if date_value:
                # Determine category and gender
                name_lower = tournament_name.lower()
                
                # Default values
                category = "Open"
                gender = "Men's"
                
                # Specific category detection
                if "u.s. open" in name_lower and "qualifier" in name_lower and "senior" not in name_lower:
                    category = "Qualifier"
                    gender = "Men's"
                elif "u.s. senior open" in name_lower or "senior open" in name_lower:
                    category = "Seniors"
                    gender = "Men's"
                elif "u.s. women's open" in name_lower:
                    category = "Qualifier"
                    gender = "Women's"
                elif "mid-amateur" in name_lower or "mid amateur" in name_lower:
                    category = "Mid-Amateur"
                    gender = "Men's"
                elif "match play" in name_lower:
                    category = "Match Play"
                    gender = "Men's"
                elif "senior" in name_lower and "women" not in name_lower:
                    category = "Seniors"
                    gender = "Men's"
                elif "super senior" in name_lower:
                    category = "Super Senior"
                    gender = "Men's"
                elif "junior" in name_lower and "girls" not in name_lower and "boys" in name_lower:
                    category = "Junior's"
                    gender = "Men's"
                elif "junior boys" in name_lower or "boys junior" in name_lower or "boys'" in name_lower:
                    category = "Junior's"
                    gender = "Men's"
                elif "junior girls" in name_lower or "girls junior" in name_lower or "girls'" in name_lower:
                    category = "Junior's"
                    gender = "Women's"
                elif "women" in name_lower or "ladies" in name_lower or "women's" in name_lower:
                    category = "Women's"
                    gender = "Women's"
                elif "girls" in name_lower:
                    category = "Junior's"
                    gender = "Women's"
                elif "amateur" in name_lower and "mid-amateur" not in name_lower:
                    category = "Amateur"
                    gender = "Men's"
                elif "four-ball" in name_lower:
                    category = "Four-Ball"
                    gender = "Men's"
                elif "father-son" in name_lower or "father & son" in name_lower:
                    category = "Father & Son"
                    gender = "Mixed"
                elif "parent-child" in name_lower:
                    category = "Parent & Child"
                    gender = "Mixed"
                
                # Create tournament entry
                tournament = {
                    "Date": date_value,
                    "Name": tournament_name,
                    "Course": course1,
                    "Category": category,
                    "Gender": gender,
                    "City": city,
                    "State": state,
                    "Zip": None
                }
                
                tournaments.append(tournament)
                
                # Only show success messages for some tournaments to avoid flooding the output
                if len(tournaments) <= 10 or len(tournaments) % 20 == 0:
                    st.write(f"✓ Added tournament: {tournament_name}")
            else:
                st.write(f"❌ Couldn't extract date from: {date_range}")
        
        except Exception as e:
            st.write(f"❌ Error processing block at index {i}: {str(e)}")
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Amateur Golf format parser: Found {len(tournaments)} tournaments")
        df = pd.DataFrame(tournaments)
        
        # Ensure columns exist in the correct order
        columns = ["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"]
        for col in columns:
            if col not in df.columns:
                df[col] = None
        
        return df[columns]
    else:
        # Return empty DataFrame with required columns
        st.write("Amateur Golf format parser: No tournaments found")
        return pd.DataFrame(columns=["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"])

def parse_golf_genius_format(text, default_year="2025", default_state=None):
    """
    Specialized parser for Golf Genius schedule format.
    
    Format:
    Tournament Name
    View
    Date
    Course Name
    Status Lines (OPEN/OPENS/CLOSED)
    Date/Time information
    ...
    
    Handles unlimited number of tournaments with no character or row limitations.
    
    Arguments:
    text -- The raw tournament text
    default_year -- Default year to use if not specified in text
    default_state -- Default state to use if not specified in text
    
    Returns:
    DataFrame with parsed tournament data
    """
    import re
    import pandas as pd
    
    # Process text into lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Month mapping
    month_map = {
        'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 
        'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
        'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12',
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12',
        'January': '01', 'February': '02', 'March': '03', 'April': '04', 
        'May': '05', 'June': '06', 'July': '07', 'August': '08',
        'September': '09', 'October': '10', 'November': '11', 'December': '12'
    }
    
    tournaments = []
    
    # Debug output
    st.write(f"Golf Genius format parser: Processing {len(lines)} lines")
    
    # Process the lines to find tournaments
    i = 0
    while i < len(lines):
        if i + 2 < len(lines) and lines[i+1] == "View":
            # Found a tournament entry
            tournament_name = lines[i]
            # The date line is after "View"
            date_line = lines[i+2]
            # The course name is after the date
            course_name = lines[i+3] if i+3 < len(lines) else None
            
            # Skip to next tournament
            next_tournament_idx = len(lines)
            for j in range(i+4, len(lines)):
                if j+1 < len(lines) and lines[j+1] == "View":
                    next_tournament_idx = j
                    break
            
            # Extract date from date line
            date_value = None
            
            # Handle various date formats
            # Single day format: Mon, Jun 2, 2025
            date_match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})', date_line)
            
            # Date range format: Sat, Sep 13 - Sun, Sep 14, 2025
            date_range_match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+([A-Za-z]+)\s+(\d{1,2})\s+-\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(?:[A-Za-z]+)\s+(?:\d{1,2}),\s+(\d{4})', date_line)
            
            # Next round format: Next Round: Sat, Sep 13, 2025
            next_round_match = re.search(r'Next Round:\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})', date_line)
            
            if date_match:
                month_name = date_match.group(1)
                day = date_match.group(2)
                year = date_match.group(3)
                
                # Get month number
                month = month_map.get(month_name, '01')
                
                # Format date
                date_value = f"{year}-{month}-{day.zfill(2)}"
            elif date_range_match:
                month_name = date_range_match.group(1)
                day = date_range_match.group(2)
                year = date_range_match.group(3)
                
                # Get month number
                month = month_map.get(month_name, '01')
                
                # Format date (use first date of range)
                date_value = f"{year}-{month}-{day.zfill(2)}"
            elif next_round_match:
                # For "Next Round" format, check if there's a date line before it
                if i+1 < len(lines):
                    prev_date_line = lines[i+1]
                    prev_date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2})\s+-\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})', prev_date_line)
                    if prev_date_match:
                        month_name = prev_date_match.group(1)
                        day = prev_date_match.group(2)
                        year = prev_date_match.group(5)
                        
                        # Get month number
                        month = month_map.get(month_name, '01')
                        
                        # Format date
                        date_value = f"{year}-{month}-{day.zfill(2)}"
                    else:
                        # Use the next round date if no other date found
                        month_name = next_round_match.group(1)
                        day = next_round_match.group(2)
                        year = next_round_match.group(3)
                        
                        # Get month number
                        month = month_map.get(month_name, '01')
                        
                        # Format date
                        date_value = f"{year}-{month}-{day.zfill(2)}"
            else:
                # Try other date formats if the above didn't match
                other_date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2})(?:\s*[-,]\s*\d{1,2})?,\s+(\d{4})', date_line)
                if other_date_match:
                    month_name = other_date_match.group(1)
                    day = other_date_match.group(2)
                    year = other_date_match.group(3)
                    
                    # Get month number
                    month = month_map.get(month_name, '01')
                    
                    # Format date
                    date_value = f"{year}-{month}-{day.zfill(2)}"
            
            if date_value and course_name:
                # Determine tournament type and format
                name_lower = tournament_name.lower()
                category = "Men's"  # Default
                format_type = "Individual"  # Default
                
                # Format detection
                if "four ball" in name_lower or "four-ball" in name_lower:
                    format_type = "Four-Ball"
                elif "individual" in name_lower:
                    format_type = "Individual"
                elif "championship" in name_lower and not "four-ball" in name_lower and not "individual" in name_lower:
                    format_type = "Championship"
                
                # Category detection (based on the name or other indicators)
                if "senior" in name_lower:
                    category = "Seniors"
                elif "junior" in name_lower:
                    category = "Junior's"
                elif "women" in name_lower or "ladies" in name_lower:
                    category = "Women's"
                    gender = "Women's"
                else:
                    # Default for these tournaments is Men's
                    category = "Men's"
                    gender = "Men's"
                
                # Extract any special notes (like *RESCHEDULED* or *Lottery Registration*)
                notes = None
                notes_match = re.search(r'\*(.*?)\*', tournament_name)
                if notes_match:
                    notes = notes_match.group(1).strip()
                
                # Create tournament entry
                tournament = {
                    "Date": date_value,
                    "Name": tournament_name,
                    "Course": course_name,
                    "Format": format_type,
                    "Category": category,
                    "Gender": "Men's",  # Default for these tournaments
                    "City": None,  # No city info in this format
                    "State": default_state,
                    "Zip": None,
                    "Notes": notes
                }
                
                tournaments.append(tournament)
                
                # Only print for the first few tournaments to avoid flooding the output
                if len(tournaments) <= 5 or len(tournaments) % 10 == 0:
                    st.write(f"✓ Added tournament #{len(tournaments)}: {tournament_name}")
            
            # Move to next tournament 
            i = next_tournament_idx
        else:
            # Not a tournament start, move to next line
            i += 1
    
    # Convert to DataFrame - with specific column ordering
    if tournaments:
        st.write(f"Golf Genius parser: Found {len(tournaments)} tournaments")
        df = pd.DataFrame(tournaments)
        
        # Ensure specific column order, including the new Format column
        columns = ["Date", "Name", "Course", "Format", "Category", "Gender", "City", "State", "Zip", "Notes"]
        for col in columns:
            if col not in df.columns:
                df[col] = None
        
        # Return DataFrame with defined column order
        return df[columns]
    else:
        # Return empty DataFrame with required columns
        st.write("Golf Genius parser: No tournaments found")
        return pd.DataFrame(columns=["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip", "Notes"])

def parse_robust_nnga_tournaments(text, year="2025", default_state=None):
    """
    Robust parser for NNGA tournament format that handles variable line spacing.
    This parser anchors on "View" lines and handles extra information like "OPEN", "closes on", etc.
    """
    # Process text into lines
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    
    # Month dictionary for date conversion
    month_dict = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    # Find all tournament entries by looking for "View" lines
    for i in range(len(lines) - 1):
        # Check if this is a "View" line
        if lines[i] == "View":
            # Tournament name is in the line before "View"
            if i > 0:
                name = lines[i - 1]
                
                # Date line is right after "View"
                if i + 1 < len(lines):
                    date_line = lines[i + 1]
                    
                    # Extract course name (could be after "Next Round:" line)
                    course_line = None
                    if i + 2 < len(lines):
                        if lines[i + 2].startswith("Next Round:"):
                            # Skip the "Next Round:" line
                            if i + 3 < len(lines):
                                course_line = lines[i + 3]
                        else:
                            course_line = lines[i + 2]
                    
                    # Extract date value
                    date_value = None
                    
                    # Handle date ranges by taking first date
                    if "-" in date_line:
                        first_date_part = date_line.split("-")[0].strip()
                        # Extract month and day
                        date_match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})', first_date_part)
                        if date_match:
                            month, day = date_match.groups()
                            date_value = f"{year}-{month_dict[month]}-{day.zfill(2)}"
                    else:
                        # Handle single date
                        date_match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})', date_line)
                        if date_match:
                            month, day = date_match.groups()
                            date_value = f"{year}-{month_dict[month]}-{day.zfill(2)}"
                    
                    # If we have all necessary pieces, create a tournament entry
                    if date_value and course_line:
                        # Determine category and gender
                        category = "Men's"  # Default
                        gender = "Men's"    # Default
                        
                        # Category detection
                        name_lower = name.lower()
                        if "mid-amateur" in name_lower:
                            category = "Mid-Amateur"
                        elif "match play" in name_lower:
                            category = "Match Play"
                        elif "senior" in name_lower and "net" not in name_lower:
                            category = "Seniors"
                        elif "junior" in name_lower:
                            category = "Junior's"
                        elif "amateur" in name_lower and "mid-amateur" not in name_lower:
                            category = "Amateur"
                        elif "team" in name_lower or "2-man" in name_lower:
                            category = "Four-Ball"
                        elif "net" in name_lower:
                            category = "Net"
                        elif "champions" in name_lower:
                            category = "Champions"
                        
                        # Gender detection
                        if "women's" in name_lower or "ladies" in name_lower:
                            gender = "Women's"
                        
                        # Create and add tournament entry
                        tournament = {
                            'Date': date_value,
                            'Name': name,
                            'Course': course_line,
                            'Category': category,
                            'Gender': gender,
                            'City': None,
                            'State': default_state,
                            'Zip': None
                        }
                        
                        tournaments.append(tournament)
    
    # Convert to DataFrame
    if tournaments:
        return pd.DataFrame(tournaments)
    else:
        # Return empty DataFrame with required columns
        return pd.DataFrame(columns=["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"])

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
    
def parse_championship_table_format(text):
    """
    Parse format with championships listed in a table-like structure with:
    Championship Name, Site, Dates
    
    Example:
    GROSS
    CHAMPIONSHIPS SITE DATES
    Foursomes Wood Ranch GC 3/3 - 3/4
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    
    # Skip header lines (like "GROSS", "CHAMPIONSHIPS SITE DATES")
    start_index = 0
    for i, line in enumerate(lines):
        if "CHAMPIONSHIPS" in line.upper() and "SITE" in line.upper() and "DATES" in line.upper():
            start_index = i + 1
            break
    
    # If no header found, try to start from beginning
    if start_index == 0 and len(lines) > 1:
        start_index = 1  # Skip first line which might be a header
    
    # Keep track of continued lines
    continued_tournament = None
    
    # Process tournament lines
    i = start_index
    while i < len(lines):
        line = lines[i]
        i += 1
        
        # Skip very short lines or likely headers
        if len(line) < 5 or (line.isupper() and len(line.split()) <= 3):
            continued_tournament = None  # Reset continuation
            continue
        
        # Check if this line has a date pattern
        date_match = re.search(r'(\d{1,2}/\d{1,2})(?:\s*-\s*(?:\d{1,2}/\d{1,2}|\d{1,2}))?$', line)
        
        if date_match:
            # This is a line with a tournament entry
            date_text = date_match.group(0)
            line_before_date = line[:date_match.start()].strip()
            
            # Try to split into tournament name and course
            # First check if there are clear course indicators
            course_indicators = ["GC", "CC", "Golf", "Club", "Course", "Pines", "Ranch", 
                                 "Park", "Hills", "Valley", "Creek", "Springs", "Resort"]
            
            course_name = ""
            tournament_name = ""
            
            # Find the last course indicator position
            last_indicator_pos = -1
            for indicator in course_indicators:
                pos = line_before_date.rfind(indicator)
                if pos > last_indicator_pos:
                    last_indicator_pos = pos
            
            if last_indicator_pos > 0:
                # Search backwards from the indicator to find likely start of course name
                # Look for capital letter preceded by space
                course_start = last_indicator_pos
                while course_start > 0 and not (line_before_date[course_start-1].isspace() and 
                                               line_before_date[course_start].isupper()):
                    course_start -= 1
                
                # If we couldn't find a clear boundary, use word boundary
                if course_start == 0:
                    words = line_before_date.split()
                    for j in range(len(words)-1, -1, -1):
                        if any(indicator in words[j] for indicator in course_indicators):
                            # Count backwards to include a reasonable course name
                            course_words = words[max(0, j-3):j+1]
                            tournament_words = words[:max(0, j-3)]
                            
                            course_name = " ".join(course_words)
                            tournament_name = " ".join(tournament_words)
                            break
                else:
                    # Extract course and tournament names
                    course_name = line_before_date[course_start:].strip()
                    tournament_name = line_before_date[:course_start].strip()
            else:
                # No clear course indicators, try a simple split
                words = line_before_date.split()
                mid_point = len(words) // 2
                tournament_name = " ".join(words[:mid_point])
                course_name = " ".join(words[mid_point:])
            
            # Check for continuation from previous line
            if continued_tournament and (not tournament_name or len(tournament_name.split()) <= 1):
                tournament_name = continued_tournament
            
            # If course name is very short or empty, check next line for continuation
            if len(course_name.split()) <= 1 and i < len(lines):
                next_line = lines[i]
                if not re.search(r'\d{1,2}/\d{1,2}', next_line) and len(next_line) > 3:
                    # Next line looks like a continuation
                    course_name += " " + next_line
                    i += 1  # Skip this line in next iteration
            
            # Format the date - for M/D format, convert to YYYY-MM-DD
            date_value = None
            if '/' in date_text:
                # For M/D format like 3/3 - 3/4
                month, day = date_text.split('/')[0], date_text.split('/')[1].split(' ')[0]
                date_value = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                # For month name format
                date_value = ultra_simple_date_extractor(date_text, year)
            
            if date_value and (tournament_name or continued_tournament) and course_name:
                # Create tournament entry
                final_name = tournament_name if tournament_name else continued_tournament
                
                tournament = {
                    'Date': date_value,
                    'Name': final_name.strip(),
                    'Course': course_name.strip(),
                    'Category': "Men's",  # Default category
                    'Gender': determine_gender(final_name),
                    'City': None,  # No city info in this format
                    'State': default_state if default_state else None,
                    'Zip': None
                }
                
                # Determine category based on tournament name
                name_lower = final_name.lower()
                if "amateur" in name_lower and "junior" not in name_lower:
                    tournament['Category'] = "Amateur"
                elif "senior" in name_lower and "super" not in name_lower:
                    tournament['Category'] = "Seniors"
                elif "super senior" in name_lower:
                    tournament['Category'] = "Super Senior"
                elif "women" in name_lower or "ladies" in name_lower or "girls" in name_lower:
                    tournament['Category'] = "Women's"
                elif "junior" in name_lower or "boys" in name_lower or "high school" in name_lower:
                    tournament['Category'] = "Junior's"
                elif "mid-amateur" in name_lower:
                    tournament['Category'] = "Mid-Amateur"
                elif "four-ball" in name_lower:
                    tournament['Category'] = "Four-Ball"
                elif "mixed" in name_lower or ("men" in name_lower and "women" in name_lower):
                    tournament['Category'] = "Mixed/Couples"
                
                tournaments.append(tournament)
                continued_tournament = None  # Reset continuation
        else:
            # This line doesn't have a date, might be a continuation or a tournament name
            # Check if it looks like a tournament name (starts with capital letter)
            if line and line[0].isupper():
                # Might be a tournament name for next line
                continued_tournament = line
            else:
                # Might be continuation of previous tournament/course
                continued_tournament = None
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in championship table format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
def parse_entries_close_format(text):
    """
    Parse format with date range, 'Entries Close' line, tournament name, and location.
    Example:
    May 31 - Jun 1
    Entries Close: May 21, 2025
    Forty & Over Four-Ball Championship (North)
    Country Club of Ocala - Ocala, FL
    Tee Times & Info
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    while i < len(lines):
        # Look for a date range pattern at the start of a line
        date_range_pattern = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+-\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$'
        date_range_pattern2 = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}-\d{1,2}$'
        date_range_pattern3 = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:-|\s+-\s+)(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*\d{1,2}$'
        date_single_pattern = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$'
        date_multiday_pattern = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}-\d{1,2}$'
        
        # Combined pattern for all date formats
        date_pattern = f"({date_range_pattern}|{date_range_pattern2}|{date_range_pattern3}|{date_single_pattern}|{date_multiday_pattern})"
        
        date_match = re.match(date_pattern, lines[i])
        
        if date_match:
            date_text = lines[i]
            
            # Check if we have enough lines for a complete entry
            if i + 1 < len(lines) and "Entries Close:" in lines[i+1]:
                # This looks like a tournament entry
                
                # Skip the "Entries Close" line
                i += 2
                
                # Next line should be tournament name
                tournament_name = lines[i] if i < len(lines) else ""
                i += 1
                
                # Next line should be course and location
                course_location = lines[i] if i < len(lines) else ""
                i += 1
                
                # Skip any "Tee Times & Info" or similar lines
                while i < len(lines) and ("Tee Times" in lines[i] or "Results" in lines[i] or len(lines[i]) < 15):
                    i += 1
                
                # Extract first date from date range
                if "-" in date_text:
                    first_date = date_text.split("-")[0].strip()
                else:
                    first_date = date_text
                
                # Process the date
                date_value = ultra_simple_date_extractor(first_date, year)
                
                # Process course and location
                course_name = ""
                city = ""
                state = ""
                
                if "-" in course_location:
                    # Format might be "Course Name - City, State"
                    parts = course_location.rsplit(" - ", 1)
                    if len(parts) == 2:
                        course_name = parts[0].strip()
                        location = parts[1].strip()
                        
                        # Extract city and state from location
                        location_match = re.search(r'(.*?),\s+([A-Z]{2})$', location)
                        if location_match:
                            city = location_match.group(1).strip()
                            state = location_match.group(2).strip()
                else:
                    # No clear separator, try to find city and state pattern
                    location_match = re.search(r'(.*?),\s+([A-Z]{2})$', course_location)
                    if location_match:
                        # Extract backwards from state
                        city = location_match.group(1).strip()
                        state = location_match.group(2).strip()
                        
                        # Try to find something that looks like a course name
                        course_indicators = ["Club", "CC", "GC", "G&CC", "Golf", "Course", "Resort", "Ranch", "National"]
                        
                        for indicator in course_indicators:
                            if indicator in course_location and indicator not in city:
                                # Find the last occurrence of the indicator
                                pos = course_location.rfind(indicator)
                                if pos > 0:
                                    # Find the start of the course name (looking for capital letter after space)
                                    start_pos = 0
                                    for j in range(pos, 0, -1):
                                        if course_location[j].isspace() and j > 0 and course_location[j-1] not in [',', '.', '-', '&']:
                                            start_pos = j + 1
                                            break
                                    
                                    course_name = course_location[start_pos:pos+len(indicator)].strip()
                                    break
                        
                        # If no course indicators found, use the whole string before city
                        if not course_name:
                            course_pos = course_location.find(city)
                            if course_pos > 0:
                                course_name = course_location[:course_pos].rstrip(' ,-').strip()
                
                # If course name is still empty, use the whole string
                if not course_name:
                    course_name = course_location.strip()
                
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
                    elif "senior" in name and "super" not in name:
                        tournament['Category'] = "Seniors"
                    elif "super-senior" in name or "super senior" in name:
                        tournament['Category'] = "Super Senior"
                    elif "women" in name or "ladies" in name:
                        tournament['Category'] = "Women's"
                    elif "junior" in name or "girls" in name or "boys" in name:
                        tournament['Category'] = "Junior's"
                    elif "mid-amateur" in name:
                        tournament['Category'] = "Mid-Amateur"
                    elif "four-ball" in name or "4-ball" in name:
                        tournament['Category'] = "Four-Ball"
                    elif "parent-child" in name or "parent child" in name:
                        tournament['Category'] = "Mixed/Couples"
                    elif "forty & over" in name or "40 & over" in name:
                        tournament['Category'] = "Mid-Amateur"
                    
                    tournaments.append(tournament)
            else:
                # Not enough lines or wrong format, skip to next line
                i += 1
        else:
            # Not a date line, skip
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in entries close format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def parse_simple_date_club_city_format(text):
    """
    Parse format with Date, Club, City columns (often used for qualifiers).
    Example:
    May 18, 2025    Sandestin Resort & Club - Raven Course    Sandestin
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Check if first line looks like headers and skip it
    if len(lines) > 1 and ("Date" in lines[0] and "Club" in lines[0] and "City" in lines[0]):
        lines = lines[1:]
    
    tournaments = []
    
    for line in lines:
        # Skip very short lines
        if len(line) < 10:
            continue
        
        # Step 1: Extract the date which is the most reliable part
        date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4})'
        date_match = re.search(date_pattern, line)
        
        if date_match:
            date_text = date_match.group(1)
            date_value = ultra_simple_date_extractor(date_text, year)
            
            # Step 2: Remove the date from the line
            rest_line = line[date_match.end():].strip()
            
            # Step 3: Try to find the last tab or multiple spaces to split course and city
            last_tab_pos = rest_line.rfind('\t')
            if last_tab_pos > 0:
                # Tab found, split at this position
                course_name = rest_line[:last_tab_pos].strip()
                city_name = rest_line[last_tab_pos+1:].strip()
            else:
                # No tab found, look for multiple spaces at the end
                match = re.search(r'\s{2,}([A-Za-z\s]+)$', rest_line)
                if match:
                    city_name = match.group(1).strip()
                    course_name = rest_line[:match.start()].strip()
                else:
                    # Last resort: Try to identify known cities
                    common_cities = ["Orlando", "Tampa", "Miami", "Jacksonville", "Tallahassee", 
                                     "Naples", "Fort Lauderdale", "Palm Beach", "Daytona", "Sandestin",
                                     "Port Orange", "St. Augustine", "Gainesville", "Port St. Lucie",
                                     "Lakewood Ranch"]
                    
                    city_found = False
                    for city in common_cities:
                        if rest_line.endswith(city):
                            city_name = city
                            course_name = rest_line[:-len(city)].strip()
                            city_found = True
                            break
                    
                    if not city_found:
                        # Can't reliably split, use the whole string as course
                        course_name = rest_line
                        city_name = ""
            
            # Step 4: Clean up the course name and city
            if course_name.endswith('-'):
                course_name = course_name[:-1].strip()
            
            # Step 5: Create tournament entry
            if date_value and course_name:
                tournament = {
                    'Date': date_value,
                    'Name': "",  # Empty string for name column
                    'Course': course_name,
                    'City': city_name,
                    'State': default_state if default_state else "",
                    'Category': "",  # Empty string for category
                    'Gender': "",    # Empty string for gender
                    'Zip': None
                }
                tournaments.append(tournament)
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in simple tabular format")
        
        # Create DataFrame with specific empty columns
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
        
        # Explicitly set certain columns to empty string
        for col in ['Name', 'Category', 'Gender']:
            tournaments_df[col] = ""
        
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        return empty_df
    
def parse_missouri_tournament_format(text):
    """
    Parse Missouri golf tournament format with day/month on separate lines.
    Example:
    19
    May
    Senior Four Ball Championship
    May 19, 2025 - May 20, 2025
    Oakwood Country Club, Kansas City, Missouri
    Men's Tournament
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    # Process in groups of 6 lines
    while i + 5 < len(lines):
        try:
            # Check if this is the expected pattern
            day = lines[i]
            month = lines[i+1]
            tournament_name = lines[i+2]
            date_range = lines[i+3]
            course_location = lines[i+4]
            tournament_type = lines[i+5]
            
            # Basic validation - check if first line is a number (day) and second is a month
            month_names = ["January", "February", "March", "April", "May", "June", "July", "August", 
                           "September", "October", "November", "December", "Jan", "Feb", "Mar", 
                           "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            
            is_day_number = day.isdigit() and 1 <= int(day) <= 31
            is_month_name = any(m == month for m in month_names)
            
            if is_day_number and is_month_name:
                # This pattern matches, extract tournament data
                
                # Parse the date range
                if "-" in date_range:
                    first_date = date_range.split("-")[0].strip()
                else:
                    first_date = date_range.strip()
                
                date_value = ultra_simple_date_extractor(first_date, year)
                
                # Parse course and location
                course = ""
                city = ""
                state = ""
                
                if "," in course_location:
                    parts = course_location.split(",")
                    course = parts[0].strip()
                    
                    if len(parts) >= 3:
                        city = parts[1].strip()
                        state = parts[2].strip()
                    elif len(parts) == 2:
                        # The last part might have both city and state
                        location_part = parts[1].strip()
                        
                        # Try to extract state
                        state_match = re.search(r'\b(Missouri|MO|Iowa|IL|Illinois|Kansas|KS|Arkansas|AR|Oklahoma|OK|Tennessee|TN|Kentucky|KY|Nebraska|NE)\b', location_part)
                        if state_match:
                            state = state_match.group(0)
                            # Convert full state names to abbreviations
                            if state == "Missouri":
                                state = "MO"
                            elif state == "Illinois":
                                state = "IL"
                            elif state == "Kansas":
                                state = "KS"
                            elif state == "Arkansas":
                                state = "AR"
                            elif state == "Oklahoma":
                                state = "OK"
                            elif state == "Tennessee":
                                state = "TN"
                            elif state == "Kentucky":
                                state = "KY"
                            elif state == "Nebraska":
                                state = "NE"
                            
                            # City is what's left after removing the state
                            city = location_part.replace(state_match.group(0), "").strip()
                            if city.endswith(","):
                                city = city[:-1]
                        else:
                            city = location_part
                else:
                    course = course_location
                
                # Determine gender from tournament type
                gender = "Men's"
                if "Women's" in tournament_type:
                    if "Men's" in tournament_type:
                        gender = "Mixed"
                    else:
                        gender = "Women's"
                
                # Determine category based on tournament name
                name_lower = tournament_name.lower()
                category = "Men's"  # Default
                
                if "senior" in name_lower:
                    category = "Seniors"
                elif "amateur" in name_lower and "qualifier" not in name_lower:
                    category = "Amateur"
                elif "four ball" in name_lower:
                    category = "Four-Ball"
                elif "mid-amateur" in name_lower:
                    category = "Mid-Amateur"
                elif "parent child" in name_lower:
                    category = "Mixed/Couples"
                elif "adaptive" in name_lower:
                    category = "Adaptive"
                elif "qualifier" in name_lower:
                    category = "Qualifier"
                elif "match play" in name_lower:
                    category = "Match Play"
                elif "stroke play" in name_lower:
                    category = "Stroke Play"
                
                # Create tournament entry
                if date_value:
                    tournament = {
                        'Date': date_value,
                        'Name': tournament_name,
                        'Course': course,
                        'Category': category,
                        'Gender': gender,
                        'City': city,
                        'State': state if state else (default_state if default_state else None),
                        'Zip': None
                    }
                    tournaments.append(tournament)
                
                # Move to next group of 6 lines
                i += 6
            else:
                # Not a match for our pattern, skip to next line
                i += 1
        except Exception as e:
            # Error processing this group, skip to next line
            st.write(f"Error processing group at index {i}: {str(e)}")
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in Missouri format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
def parse_montana_format(text):
    """
    Parse Montana golf tournament format with 3-line pattern:
    Line 1: Tournament name
    Line 2: Date - Course, City, State
    Line 3: Categories (seniors, mens, womens, juniors, team event, pro am)
    
    Example:
    WMC Larchmont Pro-Am
    May 19, 2025 - Larchmont GC, Missoula, MT
    team event pro am
    """
    # Display version for debugging
    st.write("Running Montana parser v2.1")
    
    # Split into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    st.write(f"Total lines after cleaning: {len(lines)}")
    
    # Create a raw data display that we'll use for debugging
    debug_data = []
    
    # Skip month headers like "june", "july", etc.
    month_headers = ["january", "february", "march", "april", "may", "june", 
                   "july", "august", "september", "october", "november", "december"]
    
    # Process the text
    tournaments = []
    i = 0
    
    while i < len(lines):
        try:
            # Skip month headers
            if lines[i].lower() in month_headers and len(lines[i]) < 10:
                st.write(f"Skipping month header: '{lines[i]}'")
                i += 1
                continue
            
            # Get 3 lines for a potential tournament entry
            if i + 2 < len(lines):
                # Extract the three lines
                line1 = lines[i]
                line2 = lines[i+1]
                line3 = lines[i+2]
                
                # Verify the second line has a date and dash
                date_dash_pattern = r'^([A-Za-z]+ \d{1,2}, \d{4})\s+-\s+(.+)$'
                date_match = re.search(date_dash_pattern, line2)
                
                # Check if the third line has category keywords
                category_keywords = ["mens", "men", "womens", "women", "seniors", "senior", 
                                  "juniors", "junior", "team", "event", "pro", "am"]
                has_categories = any(keyword in line3.lower() for keyword in category_keywords)
                
                if date_match and has_categories:
                    # This looks like a valid tournament entry
                    # Line 1: Tournament name
                    tournament_name = line1
                    
                    # Line 2: Date - Course, City, State
                    date_text = date_match.group(1)  # Date part
                    location_text = date_match.group(2)  # Everything after the dash
                    
                    # Format the date
                    date_value = ultra_simple_date_extractor(date_text, year)
                    
                    # Split location into parts
                    course = ""
                    city = ""
                    state = ""
                    
                    # First extract the course (before first comma)
                    location_parts = location_text.split(',')
                    if location_parts:
                        course = location_parts[0].strip()
                    
                    # Then extract city and state
                    if len(location_parts) >= 3:
                        # Format: Course, City, State
                        city = location_parts[1].strip()
                        state = location_parts[2].strip()
                    elif len(location_parts) == 2:
                        # Format: Course, City State
                        location_part = location_parts[1].strip()
                        
                        # Look for state code at the end
                        state_match = re.search(r'([A-Z]{2})$', location_part)
                        if state_match:
                            state = state_match.group(1)
                            city = location_part[:-len(state)].strip()
                        else:
                            # No state code found, might be full state name
                            city = location_part
                            
                            # Check for known state names
                            state_names = {
                                "Montana": "MT", "Idaho": "ID", "Wyoming": "WY", 
                                "Washington": "WA", "Oregon": "OR", "North Dakota": "ND"
                            }
                            for name, code in state_names.items():
                                if name in location_part:
                                    state = code
                                    city = location_part.replace(name, "").strip()
                                    break
                    
                    # Line 3: Categories
                    category_line = line3.lower()
                    
                    # Determine primary category
                    primary_category = "Men's"  # Default
                    if "juniors" in category_line or "junior" in category_line:
                        primary_category = "Junior's"
                    elif "seniors" in category_line or "senior" in category_line:
                        primary_category = "Seniors"
                    elif "pro am" in category_line or "pro-am" in category_line:
                        primary_category = "Pro-Am"
                    elif "team event" in category_line or "scramble" in category_line:
                        primary_category = "Team"
                    
                    # Tournament name might override category
                    name_lower = tournament_name.lower()
                    if "match play" in name_lower:
                        primary_category = "Match Play"
                    elif "amateur" in name_lower and "qualifier" not in name_lower:
                        primary_category = "Amateur"
                    elif "junior" in name_lower:
                        primary_category = "Junior's"
                    elif "senior" in name_lower:
                        primary_category = "Seniors"
                    
                    # Determine gender
                    gender = "Men's"  # Default
                    if ("womens" in category_line or "women" in category_line) and not ("mens" in category_line or "men" in category_line):
                        gender = "Women's"
                    elif ("womens" in category_line or "women" in category_line) and ("mens" in category_line or "men" in category_line):
                        gender = "Mixed"
                    
                    # Tournament name might indicate women's event
                    if "women" in name_lower or "ladies" in name_lower:
                        gender = "Women's"
                    
                    # Create tournament entry
                    if date_value:
                        # Create a dictionary with all tournament data
                        tournament_data = {
                            'Date': date_value,
                            'Name': tournament_name.strip(),
                            'Course': course,
                            'Category': primary_category,
                            'Gender': gender,
                            'City': city,
                            'State': state if state else (default_state if default_state else None),
                            'Zip': None
                        }
                        
                        # Add to debug data
                        debug_data.append({
                            'Index': i,
                            'Line1': line1,
                            'Line2': line2,
                            'Line3': line3,
                            'TournamentName': tournament_name,
                            'DateText': date_text,
                            'DateValue': date_value,
                            'Course': course
                        })
                        
                        # Add to tournaments list
                        tournaments.append(tournament_data)
                        
                        # Debug output
                        st.write(f"Added tournament #{len(tournaments)}: {tournament_name}")
                        st.write(f"  Date: {date_value} | Course: {course}")
                        
                        # Skip to next tournament (3 lines)
                        i += 3
                    else:
                        # Invalid date
                        st.write(f"Skipping line {i} - invalid date: {date_text}")
                        i += 1
                else:
                    # Not a tournament entry
                    st.write(f"Skipping line {i} - not a tournament entry: {lines[i]}")
                    i += 1
            else:
                # Not enough lines left
                i += 1
        except Exception as e:
            st.write(f"Error at line {i}: {str(e)}")
            i += 1
    
    # Display debugging information
    if debug_data:
        st.write("### Raw Parsed Data (for debugging)")
        for entry in debug_data[:5]:  # Show first 5 entries
            st.write(f"Tournament from line {entry['Index']+1}:")
            st.write(f"  Line 1 (Name): {entry['Line1']}")
            st.write(f"  Line 2 (Date-Course): {entry['Line2']}")
            st.write(f"  Line 3 (Categories): {entry['Line3']}")
            st.write(f"  Extracted Name: {entry['TournamentName']}")
            st.write(f"  Extracted Date: {entry['DateText']} → {entry['DateValue']}")
            st.write(f"  Extracted Course: {entry['Course']}")
            st.write("---")
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Montana parser found {len(tournaments)} tournaments")
        
        # Important: Create DataFrame with explicit column ordering
        columns_order = ['Date', 'Name', 'Course', 'Category', 'Gender', 'City', 'State', 'Zip']
        tournaments_df = pd.DataFrame(tournaments, columns=columns_order)
        
        # Show the first few rows for verification
        st.write("First few tournaments extracted:")
        st.write(tournaments_df.head(3))
        
        return tournaments_df
    else:
        st.write("No tournaments found in Montana format")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
def parse_name_date_course_format(text):
    """
    Parse format with tournament name, date in MM.DD format, and course with city.
    Example:
    Spring Triple Threat
    04.16
    Sycamore Ridge Golf Club, Spring Hill
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    while i < len(lines):
        # Need at least 3 lines for a complete entry (name, date, course+city)
        if i + 2 >= len(lines):
            i += 1
            continue
            
        # First line should be tournament name
        tournament_name = lines[i]
        i += 1
        
        # Second line should be date in MM.DD format or MM.DD / MM.DD for multiple days
        date_line = lines[i]
        
        # Check if this is a date line in MM.DD format
        date_pattern = r'^\d{2}\.\d{2}$'
        date_range_pattern = r'^\d{2}\.\d{2}\s*/\s*\d{2}\.\d{2}$'
        
        date_match = re.match(date_pattern, date_line) or re.match(date_range_pattern, date_line)
        
        if date_match:
            # Process date - convert from MM.DD format to proper date
            if "/" in date_line:
                # This is a date range (e.g., 06.16 / 06.17)
                first_date = date_line.split("/")[0].strip()
                month = first_date.split(".")[0]
                day = first_date.split(".")[1]
            else:
                # Single date (e.g., 04.16)
                month = date_line.split(".")[0]
                day = date_line.split(".")[1]
            
            # Convert month and day to integers to remove leading zeros
            try:
                month_int = int(month)
                day_int = int(day)
                
                # Map month number to month name
                month_names = ["January", "February", "March", "April", "May", "June", 
                              "July", "August", "September", "October", "November", "December"]
                month_name = month_names[month_int - 1]  # -1 because list is 0-indexed
                
                # Construct date string in a format that ultra_simple_date_extractor can handle
                formatted_date = f"{month_name} {day_int}, {year}"
                date_value = ultra_simple_date_extractor(formatted_date, year)
            except (ValueError, IndexError):
                # If month/day conversion fails, try as-is
                date_value = None
            
            i += 1
            
            # Third line should be course + city
            course_city_line = lines[i] if i < len(lines) else ""
            i += 1
            
            # Extract course and city/state
            if "," in course_city_line:
                parts = course_city_line.split(",", 1)
                course_name = parts[0].strip()
                
                # Check if we have city and state
                location_parts = parts[1].strip().split(",")
                if len(location_parts) > 1:
                    city = location_parts[0].strip()
                    state = location_parts[1].strip()
                    # Check if state is a 2-letter code
                    if len(state) > 2:
                        # If not, it might be part of the city
                        city = parts[1].strip()
                        state = default_state if default_state else ""
                else:
                    # Only city, no state
                    city = parts[1].strip()
                    
                    # Check if the "city" contains state code
                    state_match = re.search(r'([A-Z]{2})$', city)
                    if state_match:
                        # Extract state code at the end
                        state = state_match.group(1)
                        city = city[:-len(state)].strip()
                    else:
                        # Use default state
                        state = default_state if default_state else ""
            else:
                # No comma separator, use whole line as course name
                course_name = course_city_line
                city = ""
                state = default_state if default_state else ""
            
            if date_value:
                # Create tournament entry
                tournament = {
                    'Date': date_value,
                    'Name': tournament_name.strip(),
                    'Course': course_name,
                    'Category': "Women's",  # Default to Women's based on the example
                    'Gender': "Women's",    # Default to Women's based on the example
                    'City': city,
                    'State': state,
                    'Zip': None
                }
                
                # Determine category based on tournament name
                name_lower = tournament_name.lower()
                if "amateur" in name_lower and "mid-amateur" not in name_lower and "senior" not in name_lower:
                    tournament['Category'] = "Amateur"
                elif "senior" in name_lower:
                    tournament['Category'] = "Seniors"
                elif "mid-amateur" in name_lower:
                    tournament['Category'] = "Mid-Amateur"
                elif "women" in name_lower or "ladies" in name_lower:
                    tournament['Category'] = "Women's"
                elif "junior" in name_lower or "girls" in name_lower:
                    tournament['Category'] = "Junior's"
                
                tournaments.append(tournament)
        else:
            # Not a date line, skip to next line
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in name-date-course format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
def parse_monthly_entries_format(text, default_year="2025", default_state=None):
    """
    Parser for format with month headers and entry details:
    
    [Month Year] (optional header)
    Mon DD, YYYY
    Tournament Name - Course
    Entry Status
    Course Name — City
    
    Arguments:
    text -- The raw tournament text
    default_year -- Default year to use if not specified in text
    default_state -- Default state to use if not specified in text
    
    Returns:
    DataFrame with parsed tournament data
    """
    # Process text into lines
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # Month mapping for date conversion
    month_map = {
        'Jan': '01', 'January': '01', 
        'Feb': '02', 'February': '02', 
        'Mar': '03', 'March': '03', 
        'Apr': '04', 'April': '04', 
        'May': '05', 
        'Jun': '06', 'June': '06', 
        'Jul': '07', 'July': '07', 
        'Aug': '08', 'August': '08', 
        'Sep': '09', 'Sept': '09', 'September': '09', 
        'Oct': '10', 'October': '10', 
        'Nov': '11', 'November': '11', 
        'Dec': '12', 'December': '12'
    }
    
    # List to store parsed tournaments
    tournaments = []
    st.write(f"Monthly-Entries parser: processing {len(lines)} lines")
    
    # Process the data
    i = 0
    current_month = None
    
    while i < len(lines):
        # Check if this is a month header line (e.g., "May 2025" or "June 2025")
        month_year_match = re.match(r'^([A-Za-z]+)\s+(\d{4})$', lines[i])
        if month_year_match:
            current_month = month_year_match.group(1)
            i += 1
            continue
        
        # Check if this is a date line (e.g., "May 19, 2025" or "Jun 3–5, 2025")
        date_match = re.match(r'^([A-Za-z]+)\s+(\d{1,2})(?:–\d{1,2})?,\s+(\d{4})$', lines[i])
        date_match2 = re.match(r'^([A-Za-z]+)\s+(\d{1,2})–(\d{1,2}),\s+(\d{4})$', lines[i])
        date_match3 = re.match(r'^([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})$', lines[i])
        
        if date_match or date_match2 or date_match3:
            # Extract date components
            if date_match:
                month_name, day, year = date_match.groups()
            elif date_match2:
                month_name, day, _, year = date_match2.groups()
            else:
                month_name, day, year = date_match3.groups()
            
            month = month_map.get(month_name[:3], '01')
            date_value = f"{year}-{month}-{day.zfill(2)}"
            
            # Tournament name should be on the next line
            if i + 1 < len(lines):
                tournament_name = lines[i + 1]
                
                # Entry status on next line
                entry_status = None
                if i + 2 < len(lines):
                    if lines[i + 2].startswith("Entry Deadline:") or lines[i + 2].startswith("Entries "):
                        entry_status = lines[i + 2]
                    
                    # Course and location info
                    course_location_idx = i + 3 if entry_status else i + 2
                    course_location = None
                    
                    if course_location_idx < len(lines):
                        # Check if this line is a date (which would mean we're at the next tournament)
                        next_date_check = re.match(r'^([A-Za-z]+)\s+\d{1,2}', lines[course_location_idx])
                        if not next_date_check:
                            course_location = lines[course_location_idx]
                    
                    # Parse course and location
                    course_name = None
                    city = None
                    
                    if course_location:
                        # Format is typically "Course Name — City"
                        if "—" in course_location:
                            parts = course_location.split("—")
                            course_name = parts[0].strip()
                            city = parts[1].strip() if len(parts) > 1 else None
                        else:
                            course_name = course_location
                    
                    # If tournament name includes course, extract it
                    if " - " in tournament_name:
                        # Format "Tournament Name - Course Name"
                        name_parts = tournament_name.split(" - ")
                        tournament_name_only = name_parts[0].strip()
                        if not course_name:
                            course_name = name_parts[1].strip()
                    else:
                        tournament_name_only = tournament_name
                    
                    # Determine category and gender
                    name_lower = tournament_name_only.lower()
                    category = "Men's"  # Default
                    gender = "Men's"    # Default
                    
                    # Category detection
                    if "mid-amateur" in name_lower:
                        category = "Mid-Amateur"
                    elif "match play" in name_lower:
                        category = "Match Play"
                    elif "senior" in name_lower and "super" not in name_lower and "women" not in name_lower:
                        category = "Seniors"
                    elif "super-senior" in name_lower:
                        category = "Super Senior"
                    elif "junior" in name_lower:
                        category = "Junior's"
                    elif "amateur" in name_lower and "mid-amateur" not in name_lower:
                        category = "Amateur"
                    elif "open" in name_lower and "championship" in name_lower:
                        category = "Open"
                    elif "father" in name_lower and "son" in name_lower:
                        category = "Father & Son"
                        gender = "Men's"
                    elif "parent" in name_lower and "child" in name_lower:
                        category = "Parent & Child"
                        gender = "Mixed"
                    elif "mixed" in name_lower:
                        category = "Mixed/Couples"
                        gender = "Mixed"
                    elif "women" in name_lower or "ladies" in name_lower:
                        category = "Women's"
                        gender = "Women's"
                    elif "public links" in name_lower:
                        category = "Public Links"
                    elif "member golf day" in name_lower:
                        category = "Member Day"
                    
                    # Create tournament record
                    tournament = {
                        "Date": date_value,
                        "Name": tournament_name_only,
                        "Course": course_name,
                        "Category": category,
                        "Gender": gender,
                        "City": city,
                        "State": default_state,
                        "Zip": None
                    }
                    
                    tournaments.append(tournament)
                    st.write(f"✓ Added tournament: {tournament_name_only} at {course_name} on {date_value}")
                    
                    # Advance to next tournament
                    i = course_location_idx + 1 if course_location else i + 2
                else:
                    i += 1
            else:
                i += 1
        else:
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Monthly-Entries parser: found {len(tournaments)} tournaments")
        df = pd.DataFrame(tournaments)
        # Ensure all required columns exist
        for col in ["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"]:
            if col not in df.columns:
                df[col] = None
        return df
    else:
        # Return empty DataFrame with required columns
        st.write("Monthly-Entries parser: NO tournaments found")
        return pd.DataFrame(columns=["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"])
    
def parse_cdga_format(text):
    """
    Parse format with tournament name, date, day+course location, and status information.
    Example:
    CDGA Amateur Qualifying
    May 20, 2025
    TuesdayPalatine Hills Golf Course (Palatine, IL)
    Details  Tee Times
    Closed
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    while i < len(lines):
        # Skip if we don't have enough lines left for a complete entry
        if i + 2 >= len(lines):
            i += 1
            continue
        
        # First line should be tournament name
        tournament_name = lines[i]
        i += 1
        
        # Second line should be date
        date_line = lines[i]
        
        # Check if this is a date line
        date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,?\s+\d{4})?'
        date_range_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\s*-\s*\d{1,2},?\s+\d{4}'
        multi_month_range_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\s*-\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{1,2},?\s+\d{4}'
        simple_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s*-\s*\d{1,2},?\s+\d{4}'
        
        # Check various date formats
        if (re.match(date_pattern, date_line) or 
            re.match(date_range_pattern, date_line) or 
            re.match(multi_month_range_pattern, date_line) or
            re.match(simple_pattern, date_line)):
            
            # Process date line
            if "-" in date_line:
                # This is a date range
                date_parts = date_line.split("-")
                first_date = date_parts[0].strip()
                
                # Extract first date
                date_value = ultra_simple_date_extractor(first_date, year)
            else:
                # Single date
                date_value = ultra_simple_date_extractor(date_line, year)
            
            i += 1
            
            # Third line should be day+course+location
            day_course_line = lines[i] if i < len(lines) else ""
            i += 1
            
            # Extract day of week
            day_match = re.match(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)', day_course_line)
            
            if day_match:
                # Remove day from the line
                course_location = day_course_line[day_match.end():].strip()
            else:
                course_location = day_course_line
            
            # Look for course name and location in parentheses
            location_match = re.search(r'(.*?)\s*\(([^,]+),\s*([A-Z]{2})\)', course_location)
            
            course_name = ""
            city = ""
            state = ""
            
            if location_match:
                course_name = location_match.group(1).strip()
                city = location_match.group(2).strip()
                state = location_match.group(3).strip()
            else:
                # Try another format - sometimes the location doesn't have parentheses
                # Look for a comma followed by a state code
                state_match = re.search(r',\s*([A-Z]{2})(?:\s|$)', course_location)
                
                if state_match:
                    state = state_match.group(1)
                    # Try to extract city and course
                    parts = course_location[:state_match.start()].split(',')
                    if len(parts) >= 2:
                        course_name = ','.join(parts[:-1]).strip()
                        city = parts[-1].strip()
                    else:
                        course_name = parts[0].strip()
                else:
                    # No location info, just use the whole line as course name
                    course_name = course_location
            
            # Skip lines like "Details", "Tee Times", etc.
            while i < len(lines) and (lines[i].startswith("  Details") or 
                                     lines[i].startswith("  Tee Times") or 
                                     lines[i].startswith("  Confirmations")):
                i += 1
            
            # Status info might be on next line
            status = ""
            if i < len(lines) and (lines[i] == "Closed" or 
                                 lines[i] == "Wait List" or 
                                 lines[i] == "Online Entry" or
                                 lines[i] == "Entry Info" or
                                 lines[i] == "Invitation Only" or
                                 "Entry" in lines[i]):
                status = lines[i]
                i += 1
            
            # Create tournament entry
            if date_value:
                # Add course details if included on a separate line
                if i < len(lines) and "Course" in lines[i]:
                    course_name += " - " + lines[i]
                    i += 1
                
                tournament = {
                    'Date': date_value,
                    'Name': tournament_name.strip(),
                    'Course': course_name,
                    'Category': "Men's",  # Default category
                    'Gender': determine_gender(tournament_name),
                    'City': city,
                    'State': state if state else (default_state if default_state else ""),
                    'Zip': None
                }
                
                # Determine category based on tournament name
                name_lower = tournament_name.lower()
                if "amateur" in name_lower and "four-ball" not in name_lower and "senior" not in name_lower:
                    tournament['Category'] = "Amateur"
                elif "senior amateur" in name_lower:
                    tournament['Category'] = "Seniors"
                elif "mid-amateur" in name_lower:
                    tournament['Category'] = "Mid-Amateur"
                elif "four-ball" in name_lower:
                    tournament['Category'] = "Four-Ball"
                elif "women" in name_lower or "ladies" in name_lower:
                    tournament['Category'] = "Women's"
                elif "junior" in name_lower:
                    tournament['Category'] = "Junior's"
                
                tournaments.append(tournament)
        else:
            # Not a date line, skip
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in CDGA format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
def parse_events_with_sections_format(text):
    """
    Parse format with "Dates" and "Event Information" sections.
    Example:
    Dates
    Event Information
    May 10-14
    Entries Close: August 7, 2024
    U.S. Women's Amateur Four-Ball Championship
    Oklahoma City Golf & Country Club, Nichols Hills, OK
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Check if the format includes "Dates" and "Event Information" headers
    has_sections = False
    for i in range(len(lines)):
        if lines[i] == "Dates" and i+1 < len(lines) and lines[i+1] == "Event Information":
            has_sections = True
            # Skip the header lines
            lines = lines[i+2:]
            break
    
    tournaments = []
    i = 0
    
    while i < len(lines):
        # Look for date patterns
        date_pattern = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:-\d{1,2})?$'
        date_range_pattern = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+-\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$'
        
        date_match = re.match(date_pattern, lines[i]) or re.match(date_range_pattern, lines[i])
        
        if date_match:
            date_text = lines[i]
            i += 1
            
            # Skip "Entries Close" line if present
            if i < len(lines) and "Entries Close:" in lines[i]:
                i += 1
            
            # Next line should be tournament name
            tournament_name = lines[i] if i < len(lines) else ""
            i += 1
            
            # Next line should be course and location
            course_location = lines[i] if i < len(lines) else ""
            i += 1
            
            # Skip any "Tee Times & Info" or similar lines
            while i < len(lines) and ("Tee Times" in lines[i] or "Results" in lines[i] or len(lines[i]) < 15):
                i += 1
            
            # Extract first date from date range
            if "-" in date_text:
                first_date_part = date_text.split("-")[0].strip()
                if " - " in date_text:
                    first_date_part = date_text.split(" - ")[0].strip()
            else:
                first_date_part = date_text
            
            # Process the date
            date_value = ultra_simple_date_extractor(first_date_part, year)
            
            # Process course and location
            course_name = ""
            city = ""
            state = ""
            
            # Extract location information (City, State)
            location_match = re.search(r'(.*?),\s+(.*?),\s+([A-Z]{2})$', course_location)
            if location_match:
                course_name = location_match.group(1).strip()
                city = location_match.group(2).strip()
                state = location_match.group(3).strip()
            else:
                # Try alternative pattern
                location_match = re.search(r'(.*?),\s+([A-Z]{2})$', course_location)
                if location_match:
                    parts = location_match.group(1).strip().rsplit(",", 1)
                    if len(parts) == 2:
                        course_name = parts[0].strip()
                        city = parts[1].strip()
                    else:
                        course_name = parts[0].strip()
                    state = location_match.group(2).strip()
                else:
                    # No clear pattern, use the whole string as course name
                    course_name = course_location
            
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
                if "amateur" in name and "four-ball" not in name:
                    tournament['Category'] = "Amateur"
                elif "senior" in name and "open" not in name:
                    tournament['Category'] = "Seniors"
                elif "women" in name or "ladies" in name or "girls" in name:
                    tournament['Category'] = "Women's"
                elif "junior" in name or "boys" in name:
                    tournament['Category'] = "Junior's"
                elif "mid-amateur" in name:
                    tournament['Category'] = "Mid-Amateur"
                elif "four-ball" in name:
                    tournament['Category'] = "Four-Ball"
                elif "open championship" in name:
                    tournament['Category'] = "Open"
                elif "adaptive" in name:
                    tournament['Category'] = "Adaptive"
                
                tournaments.append(tournament)
        else:
            # Not a date line, skip
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in events with sections format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def detect_format(text):
    """Detect which format the text is in."""
    # Split the text into lines and check for patterns
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Check for Amateur Golf format with 5-line pattern
    amateur_golf_format = False
    if len(lines) >= 10:  # Need at least 10 lines (2 blocks)
        # Check if the data follows a pattern where every 5th line is a date
        date_patterns = 0
        location_patterns = 0
        
        # Check if blocks of 5 lines follow the pattern
        for i in range(0, min(len(lines) - 4, 50), 5):
            # Line 4 should have City, State pattern
            if i + 3 < len(lines) and re.search(r'.*,\s+[A-Z]{2}$', lines[i + 3]):
                location_patterns += 1
                
            # Line 5 should have a date pattern
            date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}'
            if i + 4 < len(lines) and re.search(date_pattern, lines[i + 4]):
                date_patterns += 1
        
        # If we have enough matches, it's likely the Amateur Golf format
        blocks_checked = min(len(lines) // 5, 10)
        if date_patterns >= blocks_checked * 0.6 and location_patterns >= blocks_checked * 0.6:
            amateur_golf_format = True
    
    if amateur_golf_format:
        return "AMATEUR_GOLF_FORMAT"

    # Check for Montana format with 3-line pattern: name, date-course, categories
    montana_pattern_count = 0
    for i in range(len(lines) - 2):
        if (len(lines[i]) > 5 and  # Tournament name
            re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\s+-', lines[i+1]) and  # Date - Course
            any(category in lines[i+2].lower() for category in ["mens", "womens", "seniors", "juniors", "team", "pro", "am"])):  # Categories
            montana_pattern_count += 1
    
    if montana_pattern_count >= 1:
        return "MONTANA_FORMAT"

    # Check for Missouri format with day/month on separate lines followed by tournament name
    missouri_pattern_count = 0
    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", 
                 "September", "October", "November", "December", "Jan", "Feb", "Mar", 
                 "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    for i in range(len(lines) - 5):
        if (lines[i].isdigit() and 1 <= int(lines[i]) <= 31 and
            lines[i+1] in month_names and
            len(lines[i+2]) > 5 and  # Tournament name
            any(month in lines[i+3] for month in month_names) and  # Date with month
            "," in lines[i+4] and  # Course, City, State
            "Tournament" in lines[i+5]):  # Tournament type
            missouri_pattern_count += 1
    
    if missouri_pattern_count >= 1:
        return "MISSOURI_FORMAT"

    # Check for GAM championship format with Type, Format, Age Group, Gender on separate lines
    type_format_count = 0
    registration_count = 0
    
    for line in lines:
        if line.startswith("Type:") or line.startswith("Format:") or line.startswith("Age Group:") or line.startswith("Gender:"):
            type_format_count += 1
        if line.startswith("Registration Opens:") or line.startswith("Registration Deadline:"):
            registration_count += 1
    
    if type_format_count >= 3 and registration_count >= 2:
        return "GAM_CHAMPIONSHIP_FORMAT"
    
    # Check for course-first format (course, tournament, course again, city/state, date)
    course_repeat_count = 0
    for i in range(len(lines) - 2):
        if lines[i] == lines[i+2]:  # Course name repeats
            course_repeat_count += 1
    
    if course_repeat_count >= 3:
        return "COURSE_FIRST_FORMAT"
    
    # Check for name-date-course format with dates in MM.DD format
    mm_dd_date_count = 0
    club_count = 0
    
    for i in range(len(lines)):
        if re.match(r'^\d{2}\.\d{2}$', lines[i]) or re.match(r'^\d{2}\.\d{2}\s*/\s*\d{2}\.\d{2}$', lines[i]):
            mm_dd_date_count += 1
        if i > 0 and i + 1 < len(lines) and (
            "Club" in lines[i] or "Course" in lines[i] or "Golf" in lines[i]) and "," in lines[i]:
            club_count += 1
    
    if mm_dd_date_count >= 3 and club_count >= 3:
        return "NAME_DATE_COURSE_FORMAT"
    
    # Check for CDGA format with "Details", "Tee Times", "Closed", etc.
    cdga_pattern_count = 0
    qualifying_count = 0
    details_count = 0
    
    for i in range(len(lines)):
        if "Qualifying" in lines[i] or "Championship" in lines[i]:
            qualifying_count += 1
        if "  Details" in lines[i] or "  Tee Times" in lines[i]:
            details_count += 1
        if i > 0 and (lines[i] == "Closed" or lines[i] == "Wait List" or 
                      lines[i] == "Online Entry" or lines[i] == "Entry Info"):
            cdga_pattern_count += 1
    
    if (qualifying_count >= 3 and details_count >= 3) or cdga_pattern_count >= 3:
        return "CDGA_FORMAT"
    
    # Check for events with sections format (Dates and Event Information)
    if len(lines) > 1 and lines[0] == "Dates" and lines[1] == "Event Information":
        return "EVENTS_WITH_SECTIONS_FORMAT"
    
    # Check for simple date, club, city tabular format
    if len(lines) > 1 and "Date" in lines[0] and "Club" in lines[0] and "City" in lines[0]:
        return "SIMPLE_DATE_CLUB_CITY_FORMAT"
    
    # Check for entries close format
    entries_close_count = 0
    date_range_count = 0
    for i in range(len(lines)):
        if i > 0 and "Entries Close:" in lines[i] and re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', lines[i-1]):
            entries_close_count += 1
        
        # Also count date ranges
        if re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+-\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', lines[i]):
            date_range_count += 1
    
    if entries_close_count >= 3:
        return "ENTRIES_CLOSE_FORMAT"
    
    # Check for championship table format with CHAMPIONSHIPS SITE DATES header
    championship_header = False
    for line in lines:
        if "CHAMPIONSHIPS" in line.upper() and "SITE" in line.upper() and "DATES" in line.upper():
            championship_header = True
            break
    
    if championship_header:
        # Check for date patterns like 3/3 - 3/4
        date_pattern_count = 0
        for line in lines:
            if re.search(r'\d{1,2}/\d{1,2}(?:\s*-\s*(?:\d{1,2}/\d{1,2}|\d{1,2}))?$', line):
                date_pattern_count += 1
        
        if date_pattern_count >= 3:
            return "CHAMPIONSHIP_TABLE_FORMAT"
    
    # Alternative check for championship table format without explicit header
    # Look for consistent date patterns at the end of lines
    date_pattern_lines = 0
    for line in lines:
        if re.search(r'\d{1,2}/\d{1,2}(?:\s*-\s*(?:\d{1,2}/\d{1,2}|\d{1,2}))?$', line):
            date_pattern_lines += 1
    
    if date_pattern_lines >= 5 and date_pattern_lines > len(lines) * 0.25:
        return "CHAMPIONSHIP_TABLE_FORMAT"
    
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
    
    if four_line_pattern_count >= 2:
        return "FOUR_LINE_FORMAT"
    
    # Check for bulleted markdown format (with * and ** and *)
    bulleted_markdown_count = 0
    for line in lines:
        if line.strip().startswith('*') and '**' in line and '*' in line.replace('**', ''):
            bulleted_markdown_count += 1
    
    if bulleted_markdown_count >= 3:
        return "BULLETED_MARKDOWN_FORMAT"
    
    # Check for schedule format with dates followed by event name on same line
    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", 
                  "September", "October", "November", "December", "Jan", "Feb", "Mar", 
                  "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    date_prefix_pattern = r'^(' + '|'.join(month_names) + r'\.?\s+\d{1,2}(?:[^\w]|$))'
    
    schedule_format_count = 0
    for line in lines:
        if re.match(date_prefix_pattern, line.strip()) and len(line) > 20:
            schedule_format_count += 1
    
    if schedule_format_count >= 3:
        return "SCHEDULE_FORMAT"
    
    # Check for expanded USGA qualifier format with "Course:" and "Golfers:" lines
    course_prefix_count = 0
    golfers_prefix_count = 0
    date_with_year_count = 0
    view_count = 0
    
    for i in range(len(lines)):
        if lines[i].startswith("Course:"):
            course_prefix_count += 1
        if lines[i].startswith("Golfers:"):
            golfers_prefix_count += 1
        if i < len(lines) - 1 and re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+[A-Za-z]{3}\s+\d{1,2},\s+\d{4}$', lines[i]):
            date_with_year_count += 1
        if lines[i] == "View":
            view_count += 1
    
    # If we have several "Course:" lines and date lines with year, it's likely the expanded USGA format
    if course_prefix_count >= 2 and date_with_year_count >= 2:
        return "USGA_QUALIFIER_EXPANDED_FORMAT"
    
    # Check for USGA qualifier format (standard)
    qualifier_count = 0
    for i in range(len(lines)):
        if lines[i] == "View":
            view_count += 1
        if i > 0 and "Qualifier" in lines[i-1]:
            qualifier_count += 1
    
    # If many "View" lines and some qualifier references, it's likely the USGA format
    if view_count >= 3 and (qualifier_count >= 1 or "U.S." in text):
        return "USGA_QUALIFIER_FORMAT"
    
    # Check for status-based format (OPEN/OPENS/CLOSED with View)
    status_keywords = ["OPEN", "OPENS", "CLOSED", "REGISTRATION OPEN", "SOLD OUT", "INVITATION LIST"]
    status_count = 0
    action_count = 0
    
    for line in lines:
        if any(line == keyword for keyword in status_keywords):
            status_count += 1
        if line == "View" or line == "Register" or line == "Details":
            action_count += 1
    
    if status_count >= 2 and action_count >= 2:
        return "STATUS_BASED_FORMAT"
    
    # Special case for custom format
    date_range_count = 0
    for line in lines:
        if " - " in line and any(month in line for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
            date_range_count += 1
    
    if date_range_count >= 3:
        return "CUSTOM_FORMAT"
        
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

def parse_custom_format(text):
    """Custom parser for the specific format observed in the data."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    
    # This parser looks for date lines and then works backwards
    for i in range(len(lines)):
        line = lines[i]
        
        # Identify date range lines
        if " - " in line and any(month in line for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
            # We found a date line, now go back to find tournament details
            if i >= 3:  # Need at least 3 lines before this (name, course, location)
                name = lines[i-3]
                course = lines[i-2]
                location = lines[i-1]
                date_range = line
                
                # Parse location for city and state
                location_match = re.search(r'(.*?),\s+([A-Z]{2})', location)
                city = ""
                state = ""
                if location_match:
                    city = location_match.group(1).strip()
                    state = location_match.group(2).strip()
                
                # Extract first date
                first_date = ultra_simple_date_extractor(date_range.split(" - ")[0], year)
                
                if first_date:
                    # Create tournament entry
                    tournament = {
                        'Date': first_date,
                        'Name': name.strip(),
                        'Course': course.strip(),
                        'Category': "Men's",  # Default category
                        'City': city,
                        'State': state,
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
        st.write(f"Debug: Found {len(tournaments)} tournaments in custom format")
        
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
                
        return tournaments_df
    else:
        # Return empty DataFrame with all required columns
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
def parse_course_tournament_format(text, year="2025", default_state=None):
    """
    Parser for format with this pattern:
    
    Course Name
    Tournament Name
    Course Name (repeated)
    City, State
    Date Range
    
    Arguments:
    text -- The raw tournament text
    year -- Default year to use if not specified in text
    default_state -- Default state to use if not specified in text
    
    Returns:
    DataFrame with parsed tournament data
    """
    # Process text into lines
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # Month mapping for date conversion
    month_map = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    # List to store parsed tournaments
    tournaments = []
    st.write(f"Course-Tournament parser: processing {len(lines)} lines")
    
    # Process in chunks of 5 lines
    i = 0
    while i + 4 < len(lines):
        try:
            # Extract the 5 lines for this potential tournament
            course1 = lines[i]
            tournament_name = lines[i+1]
            course2 = lines[i+2]
            location = lines[i+3]
            date_range = lines[i+4]
            
            # Debugging output
            st.write(f"Checking lines {i}-{i+4}: Course1='{course1}', Course2='{course2}'")
            
            # Determine if courses match or are similar
            courses_match = False
            if course1 == course2:
                courses_match = True
            elif len(course1) > 5 and len(course2) > 5:
                # Check for partial matches
                if course1 in course2 or course2 in course1:
                    courses_match = True
                # Check for Golf Club variations
                elif ("Golf Club" in course1 and "Golf Club" in course2) or \
                     ("Golf Course" in course1 and "Golf Course" in course2) or \
                     ("Country Club" in course1 and "Country Club" in course2):
                    courses_match = True
            
            if courses_match:
                st.write(f"✓ Courses match at line {i}")
                
                # Extract city and state from location line
                location_match = re.search(r'(.*?),\s+([A-Z]{2})$', location)
                city = ""
                state = default_state
                
                if location_match:
                    city = location_match.group(1).strip()
                    state = location_match.group(2).strip()
                
                # Process date range
                date_value = None
                if "-" in date_range:
                    # Get first date from range
                    first_part = date_range.split("-")[0].strip()
                    
                    # Try standard format first (May 17, 2025)
                    date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', first_part)
                    if date_match:
                        month_name, day, yr = date_match.groups()
                        month = month_map.get(month_name[:3], '01')  # Get month number
                        date_value = f"{yr}-{month}-{day.zfill(2)}"
                else:
                    # Single date
                    date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', date_range)
                    if date_match:
                        month_name, day, yr = date_match.groups()
                        month = month_map.get(month_name[:3], '01')  # Get month number
                        date_value = f"{yr}-{month}-{day.zfill(2)}"
                
                # Only add if we have a valid date
                if date_value:
                    # Determine category and gender
                    name_lower = tournament_name.lower()
                    category = "Men's"  # Default
                    gender = "Men's"    # Default
                    
                    # Category detection
                    if "mid-amateur" in name_lower:
                        category = "Mid-Amateur"
                    elif "match play" in name_lower:
                        category = "Match Play"
                    elif "senior" in name_lower and "women" not in name_lower:
                        category = "Seniors"
                    elif "junior" in name_lower:
                        category = "Junior's"
                    elif "amateur" in name_lower and "mid-amateur" not in name_lower:
                        category = "Amateur"
                    elif "two-man" in name_lower or "ii-man" in name_lower:
                        category = "Four-Ball"
                    elif "women" in name_lower:
                        category = "Women's"
                        gender = "Women's"
                    elif "ladies" in name_lower:
                        category = "Women's"
                        gender = "Women's"
                    
                    # Create tournament record
                    tournament = {
                        "Date": date_value,
                        "Name": tournament_name,
                        "Course": course1,
                        "Category": category,
                        "Gender": gender,
                        "City": city,
                        "State": state,
                        "Zip": None
                    }
                    
                    tournaments.append(tournament)
                    st.write(f"✓ Added tournament at line {i}: {tournament_name}")
                
                # Move to next block of 5 lines
                i += 5
            else:
                # If pattern doesn't match, move forward by 1 line
                i += 1
        except Exception as e:
            st.write(f"Error processing tournament at line {i}: {str(e)}")
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Course-Tournament parser: found {len(tournaments)} tournaments")
        df = pd.DataFrame(tournaments)
        # Ensure all required columns exist
        for col in ["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"]:
            if col not in df.columns:
                df[col] = None
        return df
    else:
        # Return empty DataFrame with required columns
        st.write("Course-Tournament parser: NO tournaments found")
        return pd.DataFrame(columns=["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"])
    
def parse_day_month_tournament_format(text, year="2025", default_state=None):
    """
    Parser for format with this pattern:
    
    Day (number)
    Month (name)
    Tournament Name
    Course Name
    [LEARN MORE] (optional)
    
    Arguments:
    text -- The raw tournament text
    year -- Default year to use if not specified in text
    default_state -- Default state to use if not specified in text
    
    Returns:
    DataFrame with parsed tournament data
    """
    # Process text into lines
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # Month mapping for date conversion
    month_map = {
        'Jan': '01', 'January': '01',
        'Feb': '02', 'February': '02',
        'Mar': '03', 'March': '03',
        'Apr': '04', 'April': '04',
        'May': '05', 
        'Jun': '06', 'June': '06',
        'Jul': '07', 'July': '07',
        'Aug': '08', 'August': '08',
        'Sep': '09', 'September': '09',
        'Oct': '10', 'October': '10',
        'Nov': '11', 'November': '11',
        'Dec': '12', 'December': '12'
    }
    
    # List to store parsed tournaments
    tournaments = []
    st.write(f"Day-Month-Tournament parser: processing {len(lines)} lines")
    
    # Process the data
    i = 0
    while i < len(lines):
        # Check if this line is a day (number)
        if lines[i].isdigit() and 1 <= int(lines[i]) <= 31:
            day = lines[i].zfill(2)  # Pad with leading zero if needed
            
            # Check if next line is a month
            if i+1 < len(lines) and lines[i+1] in month_map:
                month = month_map[lines[i+1]]
                
                # Check for tournament name and course
                if i+3 < len(lines):
                    tournament_name = lines[i+2]
                    course_name = lines[i+3]
                    
                    # Skip "LEARN MORE" line if present
                    next_i = i+4
                    if next_i < len(lines) and lines[next_i] == "LEARN MORE":
                        next_i += 1
                    
                    # Create date string
                    date_value = f"{year}-{month}-{day}"
                    
                    st.write(f"Found tournament: Day {day}, Month {month}, Name: {tournament_name}")
                    
                    # Determine category and gender
                    name_lower = tournament_name.lower()
                    category = "Men's"  # Default
                    gender = "Men's"    # Default
                    
                    # Category detection
                    if "mid amateur" in name_lower or "mid-amateur" in name_lower:
                        category = "Mid-Amateur"
                    elif "match play" in name_lower:
                        category = "Match Play"
                    elif "senior" in name_lower and "women" not in name_lower:
                        category = "Seniors"
                    elif "junior" in name_lower:
                        category = "Junior's"
                    elif "amateur" in name_lower and "mid" not in name_lower:
                        category = "Amateur"
                    elif "four-ball" in name_lower or "4-ball" in name_lower:
                        category = "Four-Ball"
                    elif "stroke play" in name_lower:
                        category = "Stroke Play"
                    elif "team" in name_lower:
                        category = "Team"
                    elif "mixed" in name_lower:
                        category = "Mixed/Couples"
                        gender = "Mixed"
                    elif "women" in name_lower or "ladies" in name_lower:
                        category = "Women's"
                        gender = "Women's"
                    elif "open" in name_lower and "championship" in name_lower:
                        category = "Open"
                    
                    # Create tournament record
                    tournament = {
                        "Date": date_value,
                        "Name": tournament_name,
                        "Course": course_name,
                        "Category": category,
                        "Gender": gender,
                        "City": None,
                        "State": default_state,
                        "Zip": None
                    }
                    
                    tournaments.append(tournament)
                    st.write(f"✓ Added tournament: {tournament_name} at {course_name} on {date_value}")
                    
                    # Move to next potential tournament
                    i = next_i
                else:
                    i += 1
            else:
                i += 1
        else:
            i += 1
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Day-Month-Tournament parser: found {len(tournaments)} tournaments")
        df = pd.DataFrame(tournaments)
        # Ensure all required columns exist
        for col in ["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"]:
            if col not in df.columns:
                df[col] = None
        return df
    else:
        # Return empty DataFrame with required columns
        st.write("Day-Month-Tournament parser: NO tournaments found")
        return pd.DataFrame(columns=["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"])
    
def parse_nnga_data(text_input, default_year="2025", default_state=None):
    """
    Standalone parser for NNGA tournament data.
    """
    # Process input text
    lines = text_input.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # Define month mapping
    month_map = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    # Initialize result list
    tournaments = []
    
    # Find all "View" lines - they're our anchor points
    view_indices = [i for i, line in enumerate(lines) if line == "View"]
    
    # Process each tournament based on View line positions
    for view_idx in view_indices:
        try:
            # Tournament name is the line before "View"
            if view_idx > 0:
                name = lines[view_idx - 1]
                
                # Date line is right after "View"
                date_line = lines[view_idx + 1]
                
                # Course line determination
                course_idx = view_idx + 2
                # If there's a "Next Round" line, skip it
                if course_idx < len(lines) and lines[course_idx].startswith("Next Round:"):
                    course_idx += 1
                
                # Get course name if index is valid
                if course_idx < len(lines):
                    course = lines[course_idx]
                    
                    # Extract date
                    date_value = None
                    
                    # Check if it's a date range
                    if "-" in date_line:
                        # Get first date from range
                        first_part = date_line.split("-")[0].strip()
                        date_match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})', first_part)
                        if date_match:
                            month, day = date_match.groups()
                            date_value = f"{default_year}-{month_map[month]}-{day.zfill(2)}"
                    else:
                        # Single date
                        date_match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})', date_line)
                        if date_match:
                            month, day = date_match.groups()
                            date_value = f"{default_year}-{month_map[month]}-{day.zfill(2)}"
                    
                    # Only add if we have all required data
                    if date_value:
                        # Determine category and gender
                        name_lower = name.lower()
                        category = "Men's"  # Default
                        gender = "Men's"    # Default
                        
                        # Category detection
                        if "mid-amateur" in name_lower:
                            category = "Mid-Amateur"
                        elif "match play" in name_lower:
                            category = "Match Play"
                        elif "senior" in name_lower and "net" not in name_lower:
                            category = "Seniors"
                        elif "junior" in name_lower:
                            category = "Junior's"
                        elif "amateur" in name_lower and "mid-amateur" not in name_lower:
                            category = "Amateur"
                        elif "team" in name_lower or "2-man" in name_lower:
                            category = "Four-Ball"
                        elif "net" in name_lower:
                            category = "Net"
                        
                        # Gender detection
                        if "women's" in name_lower or "ladies" in name_lower:
                            gender = "Women's"
                        
                        # Create tournament record
                        tournament = {
                            "Date": date_value,
                            "Name": name,
                            "Course": course,
                            "Category": category,
                            "Gender": gender,
                            "City": None,
                            "State": default_state,
                            "Zip": None
                        }
                        
                        tournaments.append(tournament)
        except Exception as e:
            st.error(f"Error processing tournament at View index {view_idx}: {str(e)}")
    
    # Convert to DataFrame
    if tournaments:
        df = pd.DataFrame(tournaments)
        return df
    else:
        # Return empty DataFrame with required columns
        return pd.DataFrame(columns=["Date", "Name", "Course", "Category", "Gender", "City", "State", "Zip"])

def parse_tournament_text(text):
    """
    Main function to detect format and parse tournament text.
    Uses format detection to determine which parser to use.
    """
    # Detect the format
    format_type = detect_format(text)
    st.write(f"Detected format: {format_type}")
    
    # Parse based on detected format
    if format_type == "MONTANA_FORMAT":
        return parse_montana_format(text)
    elif format_type == "MISSOURI_FORMAT":
        return parse_missouri_tournament_format(text)
    elif format_type == "GAM_CHAMPIONSHIP_FORMAT":
        return parse_gam_championship_format(text)
    elif format_type == "COURSE_FIRST_FORMAT":
        return parse_course_first_format(text)
    elif format_type == "NAME_DATE_COURSE_FORMAT":
        return parse_name_date_course_format(text)
    elif format_type == "CDGA_FORMAT":
        return parse_cdga_format(text)
    elif format_type == "EVENTS_WITH_SECTIONS_FORMAT":
        return parse_events_with_sections_format(text)
    elif format_type == "SIMPLE_DATE_CLUB_CITY_FORMAT":
        return parse_simple_date_club_city_format(text)
    elif format_type == "ENTRIES_CLOSE_FORMAT":
        return parse_entries_close_format(text)
    elif format_type == "CHAMPIONSHIP_TABLE_FORMAT":
        return parse_championship_table_format(text)
    elif format_type == "FOUR_LINE_FORMAT":
        return parse_four_line_format(text)
    elif format_type == "MARKDOWN_FORMAT":
        return parse_markdown_format(text)
    elif format_type == "CUSTOM_FORMAT":
        return parse_custom_format(text)
    elif format_type == "STATUS_BASED_FORMAT":
        return parse_status_based_format(text)
    else:
        # If no specific format is detected, try the most generic parser
        st.write("No specific format detected, trying generic parser")
        return parse_status_based_format(text)  # Use status-based format as fallback

# Define the Streamlit app
st.title("NNGA Tournament Parser")
st.write("Paste NNGA tournament data below to parse it into a structured format.")

# Text area for input
tournament_text = st.text_area(
    "Paste your tournament text here:", 
    height=400,
    help="Paste the raw text containing tournament information.",
    key="tournament_text_input"  # Added unique key
)

# Year and state inputs
year = st.text_input(
    "Tournament Year (if not specified in text):", 
    "2025",
    key="tournament_year_input"  # Added unique key
)

default_state = st.selectbox(
    "Default State for Tournaments:",
    ["", "NV", "AZ", "CA", "ID", "OR", "WA", "UT", "CO", "NM", "TX"],
    index=1,
    key="default_state_select"  # Added unique key
)

# File naming option
output_filename = st.text_input(
    "Output Filename (without extension):", 
    "golf_tournaments",
    key="output_filename_input"  # Added unique key
)

def ensure_column_order(df):
    """Ensure DataFrame columns are in the correct order."""
    # Get all columns that exist in the DataFrame
    existing_columns = [col for col in REQUIRED_COLUMNS if col in df.columns]
    
    # Add any additional columns that might exist
    other_columns = [col for col in df.columns if col not in REQUIRED_COLUMNS]
    
    # Reorder columns
    return df[existing_columns + other_columns]

# Process button
if st.button("Process Tournament Data"):
    if tournament_text:
        try:
            # Detect format
            format_type = detect_format(tournament_text)
            st.write(f"Detected format: {format_type}")
            
            # Parse based on detected format
            if format_type == "AMATEUR_GOLF_FORMAT":
                df = parse_amateur_golf_format_improved(tournament_text, year, default_state)
            elif format_type == "MONTANA_FORMAT":
                df = parse_montana_format(tournament_text)
            elif format_type == "MISSOURI_FORMAT":
                df = parse_missouri_tournament_format(tournament_text)
            elif format_type == "GAM_CHAMPIONSHIP_FORMAT":
                df = parse_gam_championship_format(tournament_text)
            elif format_type == "COURSE_FIRST_FORMAT":
                df = parse_course_tournament_format(tournament_text, year, default_state)
            elif format_type == "NAME_DATE_COURSE_FORMAT":
                df = parse_name_date_course_format(tournament_text)
            elif format_type == "CDGA_FORMAT":
                df = parse_cdga_format(tournament_text)
            elif format_type == "EVENTS_WITH_SECTIONS_FORMAT":
                df = parse_events_with_sections_format(tournament_text)
            elif format_type == "SIMPLE_DATE_CLUB_CITY_FORMAT":
                df = parse_simple_date_club_city_format(tournament_text)
            elif format_type == "ENTRIES_CLOSE_FORMAT":
                df = parse_entries_close_format(tournament_text)
            elif format_type == "CHAMPIONSHIP_TABLE_FORMAT":
                df = parse_championship_table_format(tournament_text)
            elif format_type == "FOUR_LINE_FORMAT":
                df = parse_four_line_format(tournament_text)
            elif format_type == "MARKDOWN_FORMAT":
                df = parse_markdown_format(tournament_text)
            elif format_type == "CUSTOM_FORMAT":
                df = parse_custom_format(tournament_text)
            elif format_type == "STATUS_BASED_FORMAT":
                df = parse_status_based_format(tournament_text)
            elif format_type == "USGA_QUALIFIER_FORMAT":
                # Try to use USGA parser
                if 'parse_usga_qualifier_format' in globals():
                    df = parse_usga_qualifier_format(tournament_text)
                elif 'parse_usga_view_format' in globals():
                    df = parse_usga_view_format(tournament_text)
                else:
                    # Fall back to generic parser
                    df = parse_status_based_format(tournament_text)
            else:
                # If no specific format is detected, try the most generic parser
                st.write("No specific format detected, trying generic parser")
                df = parse_status_based_format(tournament_text)  # Use status-based format as fallback
            
            # Check if DataFrame is empty
            if df.empty:
                st.error("No tournaments could be extracted from the text. Please check the format.")
                # Create an empty DataFrame with all required columns
                df = pd.DataFrame(columns=REQUIRED_COLUMNS)
            else:
                # Show detailed information about the raw extracted data for debugging
                st.write("### Raw Extracted Data (First few rows)")
                display_df = df.head(5).copy()
                # Convert any complex objects to strings for display
                for col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: str(x) if x is not None else None)
                st.write(display_df)
                
                # Ensure all required columns exist
                for col in REQUIRED_COLUMNS:
                    if col not in df.columns:
                        df[col] = None
                
                # Ensure Name column is populated - Check if we have empty names but valid courses
                if 'Name' in df.columns and 'Course' in df.columns:
                    empty_names = df['Name'].isnull() | (df['Name'] == '')
                    if empty_names.any() and df.loc[empty_names, 'Course'].notna().any():
                        st.warning(f"Found {empty_names.sum()} entries with missing names but valid courses. Using course names as tournament names.")
                        df.loc[empty_names, 'Name'] = df.loc[empty_names, 'Course'] + " Tournament"
                
                # Ensure Gender is set for all rows
                if 'Name' in df.columns and 'Gender' in df.columns:
                    df['Gender'] = df.apply(lambda row: row['Gender'] if pd.notna(row['Gender']) else determine_gender(row['Name']), axis=1)
                
                # Ensure columns are in the correct order
                if 'Format' in df.columns:
                    # Include Format column if it exists
                    custom_columns = ["Date", "Name", "Course", "Format", "Category", "Gender", "City", "State", "Zip"]
                    for col in custom_columns:
                        if col not in df.columns:
                            df[col] = None
                    
                    # Add any additional required columns
                    for col in REQUIRED_COLUMNS:
                        if col not in custom_columns and col not in df.columns:
                            df[col] = None
                    
                    # Set column order
                    column_order = [col for col in custom_columns if col in df.columns]
                    extra_columns = [col for col in df.columns if col not in custom_columns]
                    df = df[column_order + extra_columns]
                else:
                    # Use standard column order
                    df = ensure_column_order(df)
            
            # Display how many tournaments were found
            st.success(f"Successfully extracted {len(df)} tournaments!")
            
            # Display the DataFrame with pagination controls for large datasets
            if len(df) > 20:
                st.write("### Processed Tournament Data (Paginated)")
                page_size = st.selectbox("Rows per page:", [10, 20, 50, 100, 500, 1000], index=3)
                total_pages = (len(df) + page_size - 1) // page_size
                page = st.number_input("Page:", min_value=1, max_value=max(1, total_pages), value=1)
                
                start_idx = (page - 1) * page_size
                end_idx = min(start_idx + page_size, len(df))
                
                st.write(f"Showing rows {start_idx+1}-{end_idx} of {len(df)}")
                st.write(df.iloc[start_idx:end_idx])
            else:
                # For smaller datasets, just show everything
                st.write("### Processed Tournament Data")
                st.write(df)
            
            # Also show the raw data in table format to ensure all rows are visible
            with st.expander("Show full data table view"):
                max_rows = min(1000, len(df))  # Show up to 1000 rows max
                st.write(f"Showing first {max_rows} rows of {len(df)} total tournaments")
                st.dataframe(df.head(max_rows), height=500)
            
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