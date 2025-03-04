"""
This module contains Gwendolyn Vials Moore's personal and family information.
"""

PATIENT_INFO = {
    "name": "Gwendolyn (Gwen) Vials Moore",
    "dob": "2014-08-22",
    "birth_location": "Liverpool Women's Hospital",
    "family": [
        {"name": "Adam Vials Moore", "relation": "Father", "notes": "Has a doctorate but is NOT a medical practitioner"},
        {"name": "Cora Vials Moore", "relation": "Mother"},
        {"name": "Isaac Vials Moore", "relation": "Brother (older)"}
    ],
    "key_dates": [
        {"date": "2014-08-22", "event": "Birth", "location": "Liverpool Women's Hospital"}
        # Additional key dates can be added here
    ],
    # Additional identifiers will be populated from documents
    "identifiers": {}
}

# List of family members who should not be classified as medical personnel
NON_MEDICAL_PERSONNEL = [
    "Adam Vials Moore",
    "Adam Vials",
    "Adam Moore",
    "Dr. Adam Vials Moore",
    "Dr. Adam Vials",
    "Dr. Adam Moore",
    "Cora Vials Moore",
    "Cora Vials",
    "Cora Moore",
    "Isaac Vials Moore",
    "Isaac Vials",
    "Isaac Moore"
]

def get_age(current_date=None):
    """
    Calculate Gwen's age based on her DOB and the current date.
    
    Parameters:
        current_date (str): Date in format 'YYYY-MM-DD'. If None, uses the current date.
        
    Returns:
        dict: Age in years, months, and days.
    """
    from datetime import datetime, date
    
    if current_date:
        if isinstance(current_date, str):
            current = datetime.strptime(current_date, '%Y-%m-%d').date()
        else:
            current = current_date
    else:
        current = date.today()
    
    dob = datetime.strptime(PATIENT_INFO["dob"], '%Y-%m-%d').date()
    
    years = current.year - dob.year
    months = current.month - dob.month
    days = current.day - dob.day
    
    if days < 0:
        months -= 1
        # Get the number of days in the previous month
        if current.month == 1:
            prev_month = date(current.year - 1, 12, 1)
        else:
            prev_month = date(current.year, current.month - 1, 1)
        
        import calendar
        days_in_prev_month = calendar.monthrange(prev_month.year, prev_month.month)[1]
        days += days_in_prev_month
    
    if months < 0:
        years -= 1
        months += 12
    
    return {
        "years": years,
        "months": months,
        "days": days
    }

def get_age_at_date(event_date):
    """
    Calculate Gwen's age at a specific date.
    
    Parameters:
        event_date (str): Date in format 'YYYY-MM-DD'.
        
    Returns:
        dict: Age in years, months, and days.
    """
    return get_age(event_date)

def format_age(age_dict):
    """
    Format age dictionary into a readable string.
    
    Parameters:
        age_dict (dict): Age dictionary with years, months, and days.
        
    Returns:
        str: Formatted age string.
    """
    years = age_dict["years"]
    months = age_dict["months"]
    days = age_dict["days"]
    
    if years == 0:
        if months == 0:
            return f"{days} days old"
        else:
            return f"{months} months, {days} days old"
    else:
        return f"{years} years, {months} months old"

def update_patient_info(new_info):
    """
    Update the patient information with new data.
    
    Parameters:
        new_info (dict): New patient information to add.
    """
    global PATIENT_INFO
    
    # Update identifiers
    if "identifiers" in new_info:
        if "identifiers" not in PATIENT_INFO:
            PATIENT_INFO["identifiers"] = {}
        
        for key, value in new_info["identifiers"].items():
            PATIENT_INFO["identifiers"][key] = value
    
    # Update other fields as needed
    for key, value in new_info.items():
        if key != "identifiers" and key not in PATIENT_INFO:
            PATIENT_INFO[key] = value

def is_family_member(name):
    """
    Check if a name belongs to a family member.
    
    Parameters:
        name (str): Name to check.
        
    Returns:
        bool: True if the name belongs to a family member, False otherwise.
    """
    for family_name in NON_MEDICAL_PERSONNEL:
        if family_name.lower() in name.lower():
            return True
    
    return False
