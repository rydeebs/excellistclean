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

def parse_usga_qualifier_format(text):
    """
    Parse USGA qualifier format without status indicators.
    This format handles patterns like:
    Tournament Name
    View
    Date
    Course
    """
    # Split the text into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    i = 0
    
    while i < len(lines):
        # Look for tournament name followed by "View"
        if i < len(lines) and i+1 < len(lines) and lines[i+1] == "View":
            tournament_data = {col: None for col in REQUIRED_COLUMNS}
            
            # This is a tournament name
            tournament_data['Name'] = lines[i].strip()
            i += 2  # Skip "View" line
            
            # Next line should be date
            if i < len(lines):
                date_line = lines[i]
                tournament_data['Date'] = ultra_simple_date_extractor(date_line, year)
                i += 1
            
            # Next line should be course
            if i < len(lines):
                tournament_data['Course'] = lines[i].strip()
                i += 1
            
            # Set default category based on tournament name
            name = tournament_data['Name']
            if name:
                if "Women's" in name or "Ladies" in name or "Girls'" in name:
                    tournament_data['Category'] = "Women's"
                elif "Junior" in name or "Boys'" in name:
                    tournament_data['Category'] = "Junior's"
                elif "Senior" in name:
                    tournament_data['Category'] = "Seniors"
                elif "Mid-Amateur" in name:
                    tournament_data['Category'] = "Mid-Amateur"
                elif "Amateur" in name:
                    tournament_data['Category'] = "Amateur"
                elif "Four-Ball" in name:
                    tournament_data['Category'] = "Four-Ball"
                else:
                    tournament_data['Category'] = "Men's"  # Default category
            
            # Extract qualifier type
            qualifier_match = re.search(r'(Qualifier|Final Qualifier|Local Qualifier)', name) if name else None
            if qualifier_match:
                tournament_data['Type'] = qualifier_match.group(1)
            else:
                tournament_data['Type'] = "Tournament"
            
            # Set default state if provided
            if default_state:
                tournament_data['State'] = default_state
            
            # Try to extract state from course name or tournament name
            course = tournament_data['Course']
            name = tournament_data['Name']
            
            # Look for state code in tournament name
            state_match = re.search(r' - ([A-Za-z\s]+)$', name) if name else None
            if state_match:
                location = state_match.group(1).strip()
                # Check if this is a known course or city in a state
                # For now, we just use the default state
            
            # Add tournament to the list
            if tournament_data['Name'] and tournament_data['Date']:
                tournaments.append(tournament_data)
            else:
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
            re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+[A-Za-z]{3}\s+\d{1,2},\s+\d{4}$', lines[i+1])):
            
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
        
        # Try to match a consistent pattern:
        # Date (May 18, 2025), followed by Course, followed by City
        date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4})'
        date_match = re.match(date_pattern, line)
        
        if date_match:
            date_text = date_match.group(1)
            # Remove the date part from the line
            remaining_text = line[len(date_text):].strip()
            
            # First try to see if we can split by tabs
            tab_parts = remaining_text.split('\t')
            
            if len(tab_parts) >= 2:
                # Split by tabs worked
                course_name = tab_parts[0].strip()
                city_name = tab_parts[1].strip()
            else:
                # Try to find the last 1-2 words which are likely the city
                words = remaining_text.split()
                if len(words) <= 2:
                    # Not enough words to separate course and city
                    course_name = remaining_text
                    city_name = ""
                else:
                    # Assume the last word is the city
                    city_name = words[-1]
                    # And everything else is the course
                    course_name = " ".join(words[:-1])
                    
                    # If the city name is very short, it might include the previous word too
                    if len(city_name) <= 3 and len(words) > 2:
                        city_name = words[-2] + " " + words[-1]
                        course_name = " ".join(words[:-2])
            
            # Process the date
            date_value = ultra_simple_date_extractor(date_text, year)
            
            # Check if city includes "Golf Club" or similar which suggests incorrect parsing
            golf_terms = ["Golf", "Club", "Course", "Resort", "CC", "GC", "G&CC"]
            if any(term in city_name for term in golf_terms):
                # Parsing error - city contains golf terms
                # Try a different approach - check if line has any common city names
                common_cities = ["Orlando", "Tampa", "Miami", "Jacksonville", "Tallahassee", 
                                "Naples", "Fort Lauderdale", "Palm Beach", "Daytona", "Sandestin",
                                "Port Orange", "St. Augustine", "Gainesville", "Port St. Lucie"]
                
                city_found = False
                for city in common_cities:
                    if city in remaining_text:
                        city_pos = remaining_text.find(city)
                        city_name = city
                        course_name = remaining_text[:city_pos].strip()
                        city_found = True
                        break
                
                if not city_found:
                    # Last resort - just leave the city blank
                    course_name = remaining_text
                    city_name = ""
            
            # For state, use default state if provided
            state = default_state if default_state else ""
            
            if date_value:
                # Create tournament entry with empty name
                tournament = {
                    'Date': date_value,
                    'Name': "",  # Empty string instead of None
                    'Course': course_name.strip(),
                    'City': city_name.strip(),
                    'State': state,
                    'Category': "",  # Empty string
                    'Gender': "",    # Empty string
                    'Zip': None
                }
                
                tournaments.append(tournament)
        
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in simple tabular format")
        
        # Convert to DataFrame with explicit empty strings for text columns
        tournaments_df = pd.DataFrame(tournaments)
        
        # Ensure all required columns exist
        for col in REQUIRED_COLUMNS:
            if col not in tournaments_df.columns:
                tournaments_df[col] = None
            elif col in ['Name', 'Category', 'Gender']:
                # Use empty strings explicitly for these columns
                tournaments_df[col] = ""
                
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
    lines = [line.strip() for line in text.split('\n')]
    
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
                'Gender': determine_gender(tournament_name),  # Determine gender from name
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

def parse_schedule_format(text):
    """
    Parse schedule-style format with date ranges and tournaments on the same line.
    Format example: 'May 31-June 1 Hot Springs CC Designated Hot Springs CC'
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    tournaments = []
    
    # Month abbreviations and full names
    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", 
                  "September", "October", "November", "December", "Jan", "Feb", "Mar", 
                  "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Pattern to identify date at start of line: May 31, June 2, Aug. 7-10, etc.
    date_prefix_pattern = r'^(' + '|'.join(month_names) + r'\.?\s+\d{1,2}(?:[^\w]|$))'
    
    for line in lines:
        # Skip lines without a date prefix or that are too short (likely notes)
        if not re.match(date_prefix_pattern, line) or len(line) < 10:
            continue
            
        # Find date section
        date_match = re.match(r'^(.*?)(?=[A-Z][a-z]+\s+(?:CC|G&AC|GC|Championship|Qualifier|Park|Valley|Creek|Hills|Club))', line)
        if not date_match:
            continue
            
        date_text = date_match.group(1).strip()
        
        # Extract first date from any range (May 31-June 1 -> May 31)
        if '-' in date_text:
            first_date = date_text.split('-')[0].strip()
        else:
            first_date = date_text
            
        # Clean up date (remove abbreviation periods)
        first_date = first_date.replace(".", "")
        
        # Get the formatted date
        date_value = ultra_simple_date_extractor(first_date, year)
        if not date_value:
            continue
            
        # Extract tournament name and course
        rest_of_line = line[len(date_text):].strip()
        
        # Try to find the tournament name and course
        # Common patterns include:
        # - Tournament type followed by location (State Am. Qualifier #1 Lost Springs G&AC)
        # - Championship name followed by course (Men's Match-Play Championship Burns Park GC)
        # - Course followed by modifier and course again (Hot Springs CC Designated Hot Springs CC)
        
        # Special case for simple "Tournament Course" pattern
        if " CC " in rest_of_line or " GC " in rest_of_line or " Park " in rest_of_line:
            # Find first course indicator and split there
            course_indicators = ["CC", "GC", "G&AC", "Park", "Creek", "Hills", "Valley", "Club"]
            split_positions = []
            
            for indicator in course_indicators:
                pos = rest_of_line.find(f" {indicator} ")
                if pos > 0:
                    split_positions.append(pos)
            
            if split_positions:
                split_pos = min(split_positions)
                tournament_name = rest_of_line[:split_pos].strip()
                course_info = rest_of_line[split_pos:].strip()
                
                # Clean up course name (extract first part if multiple courses)
                if "&" in course_info and not course_info.startswith("G&"):
                    course_name = course_info.split("&")[0].strip()
                else:
                    course_name = course_info
            else:
                # Default split halfway through
                tournament_name = rest_of_line[:len(rest_of_line)//2].strip()
                course_name = rest_of_line[len(rest_of_line)//2:].strip()
        else:
            # Try to split at last word before a 2+ capital letters word (like "CC", "GC")
            parts = rest_of_line.split()
            split_idx = len(parts) - 1  # Default to last word
            
            for i in range(len(parts) - 1, 0, -1):
                if re.match(r'^[A-Z]{2,}$', parts[i]) or parts[i] in ["CC", "GC", "G&AC"]:
                    split_idx = i - 1
                    break
            
            tournament_name = " ".join(parts[:split_idx]).strip()
            course_name = " ".join(parts[split_idx:]).strip()
            
            # If parsing failed, use a simple ratio-based split
            if not tournament_name or not course_name:
                split_point = int(len(rest_of_line) * 0.6)  # 60/40 split favoring tournament name
                tournament_name = rest_of_line[:split_point].strip()
                course_name = rest_of_line[split_point:].strip()
        
        # Create tournament entry
        tournament = {
            'Date': date_value,
            'Name': tournament_name,
            'Course': course_name,
            'Category': "Men's",  # Default category
            'City': None,
            'State': default_state if default_state else None,
            'Zip': None
        }
        
        # Set category based on tournament name
        name = tournament_name.lower()
        if "amateur" in name or "am." in name:
            tournament['Category'] = "Amateur"
        elif "senior" in name:
            tournament['Category'] = "Seniors"
        elif "women" in name or "ladies" in name or "girls" in name:
            tournament['Category'] = "Women's"
        elif "junior" in name or "boys" in name:
            tournament['Category'] = "Junior's"
        elif "mid-amateur" in name or "mid-am" in name:
            tournament['Category'] = "Mid-Amateur"
        elif "four-ball" in name:
            tournament['Category'] = "Four-Ball"
        elif "father" in name and "son" in name:
            tournament['Category'] = "Mixed/Couples"
        
        # Set gender based on tournament name
        tournament['Gender'] = determine_gender(tournament_name)
        
        tournaments.append(tournament)
    
    # Convert to DataFrame
    if tournaments:
        st.write(f"Debug: Found {len(tournaments)} tournaments in schedule format")
        
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
    
    if format_type == "EVENTS_WITH_SECTIONS_FORMAT":
        return parse_events_with_sections_format(text)
    elif format_type == "SIMPLE_DATE_CLUB_CITY_FORMAT":
        return parse_simple_date_club_city_format(text)
    elif format_type == "ENTRIES_CLOSE_FORMAT":
        return parse_entries_close_format(text)
    elif format_type == "CHAMPIONSHIP_TABLE_FORMAT":
        return parse_championship_table_format(text)
    elif format_type == "FOUR_LINE_FORMAT":
        return parse_four_line_format(text)
    elif format_type == "BULLETED_MARKDOWN_FORMAT":
        return parse_bulleted_markdown_format(text)
    elif format_type == "SCHEDULE_FORMAT":
        return parse_schedule_format(text)
    elif format_type == "USGA_QUALIFIER_EXPANDED_FORMAT":
        return parse_usga_qualifier_expanded_format(text)
    elif format_type == "USGA_QUALIFIER_FORMAT":
        return parse_usga_qualifier_format(text)
    elif format_type == "STATUS_BASED_FORMAT":
        return parse_status_based_format(text)
    elif format_type == "CUSTOM_FORMAT":
        return parse_custom_format(text)
    elif format_type == "MARKDOWN_FORMAT":
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
    ["Format 1: Simple List", "Format 2: Championship List", "Format 3: Tabular List", 
     "Format 4: List with Date Ranges", "Format 5: USGA Qualifier Format"]
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

format5_example = """2025 U.S. Senior Open Final Qualifier - Mesa CC
Mon, Jun 2, 2025
Course: Mesa Country Club
Golfers: 0
View
2025 U.S. Girls' Junior Amateur Qualifier - Alta Mesa
Mon, Jun 9, 2025
Course: Alta Mesa Golf Club
Golfers: 0
View
2025 U.S. Junior Amateur Qualifier - Tatum Ranch
Mon, Jun 9, 2025
Course: Tatum Ranch Golf Club
Golfers: 0
View
2025 U.S. Senior Women's Open Qualifier - Terravita
Mon, Jun 23, 2025
Course: Terravita Golf Club
Golfers: 0
View
2025 U.S. Amateur Local Qualifier - Sterling Grove
Mon, Jun 30, 2025
Course: Sterling Grove Golf & Country Club
Golfers: 0
View
2025 U.S. Women's Amateur Qualifier - Moon Valley
Thu, Jul 10, 2025
Course: Moon Valley Country Club
Golfers: 0
View"""

# Select the default text based on the chosen format
if format_option == "Format 1: Simple List":
    default_text = format1_example
elif format_option == "Format 2: Championship List":
    default_text = format2_example
elif format_option == "Format 3: Tabular List":
    default_text = format3_example
elif format_option == "Format 5: USGA Qualifier Format":
    default_text = format5_example
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
                
                # Ensure Gender is set for all rows
                df['Gender'] = df['Name'].apply(determine_gender)
                
                # Ensure columns are in the correct order
                df = ensure_column_order(df)
            
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