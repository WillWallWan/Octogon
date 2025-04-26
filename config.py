"""
Configuration file for the tennis court reservation system.
"""

# User credentials
USERS = {
    "alex": {
        "email": "nyuclubtennis+alexm@gmail.com",
        "password": "Tennis2025"
    },
    "jamie": {
        "email": "nyuclubtennis+jamies@gmail.com",
        "password": "Tennis2025"
    },
    "arthur": {
        "email": "nyuclubtennis+arthurw@gmail.com",
        "password": "Tennis2025"
    },
    "morgan": {
        "email": "nyuclubtennis+morganb@gmail.com",
        "password": "Tennis2025"
    },
    "jordan": {
        "email": "nyuclubtennis+jordanr@gmail.com",
        "password": "Tennis2025"
    },
    "brian": {
        "email": "nyuclubtennis+brians@gmail.com",
        "password": "Tennis2025"
    },
    "yiting": {
        "email": "nyuclubtennis+yitings@gmail.com",
        "password": "Tennis2025"
    },
    "ben": {
        "email": "nyuclubtennis+benk@gmail.com",
        "password": "Tennis2025"
    }
    
}

# Court booking priorities (highest priority first)
COURT_PRIORITIES = [
    {"court": 6, "time": "18:00"},  # Highest priority 
    {"court": 3, "time": "17:00"},
    {"court": 5, "time": "18:00"},
    {"court": 6, "time": "17:00"},
    {"court": 3, "time": "18:00"},
    {"court": 5, "time": "17:00"},
    {"court": 6, "time": "19:00"},
    {"court": 3, "time": "19:00"},
    {"court": 5, "time": "19:00"}
]

# Secondary court priorities (for manual booker)
SECONDARY_COURT_PRIORITIES = [
    {"court": 1, "time": "17:00"},
    {"court": 2, "time": "18:00"},
    {"court": 4, "time": "17:00"},
    {"court": 1, "time": "18:00"},
    {"court": 2, "time": "17:00"},
    {"court": 4, "time": "18:00"},
    {"court": 1, "time": "19:00"},
    {"court": 2, "time": "19:00"},
    {"court": 4, "time": "19:00"}
]

# Time constraints
BOOKING_WINDOW_START = "08:00"  # Earliest time to submit booking requests
BOOKING_WINDOW_END = "16:00"    # Latest time to submit booking requests
SAME_DAY_CUTOFF = "15:00"      # Cutoff for same-day bookings

# Court availability
COURT_OPEN_TIME = "07:00"      # First available booking time
COURT_CLOSE_TIME = "21:00"     # Last available booking time (for 1-hour slots)

# Days ahead to book based on current weekday (0=Monday, 6=Sunday)
BOOKING_RULES = {
    0: [1, 2],      # Monday: book Wednesday
    1: [2],      # Tuesday: book Thursday
    2: [2],      # Wednesday: book Friday
    3: [2],      # Thursday: book Saturday
    4: [3, 4] # Friday: book Monday, Tuesday
}

# Court IDs (don't change unless the website changes these values)
COURT_IDS = {
    1: "036dfea4-c487-47b0-b7fe-c9cbe52b7c98",
    2: "175bdff8-016e-46ab-a9df-829fe40c0754",
    3: "9bdef00b-afa0-4b6b-bf9a-75899f7f97c7",
    4: "d311851d-ce53-49fc-9662-42adcda26109",
    5: "8a5ca8e8-3be0-4145-a4ef-91a69671295b",
    6: "77c7f42c-8891-4818-a610-d5c1027c62fe"
} 