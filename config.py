"""
Configuration Settings
Prarthi ERP System
"""

# Company info
COMPANY_NAME = "Prarthi Bhambere Limited"
COMPANY_SHORT = "PBL"

# Vendor categories
VENDOR_CATEGORIES = [
    "Steel Suppliers",
    "Cement Suppliers", 
    "Aggregate Suppliers",
    "Ready Mix Concrete",
    "Electrical Suppliers",
    "Plumbing Suppliers",
    "Hardware Suppliers",
    "Paint Suppliers",
    "Timber Suppliers",
    "Glass Suppliers",
    "Tile Suppliers",
    "Sanitary Suppliers",
    "HVAC Suppliers",
    "Fire Safety Suppliers",
    "Elevator Suppliers",
    "Fuel Supplier",
    "Labour Contractor",
    "Transport Contractor",
    "Equipment Rental",
    "Professional Services",
    "General Supplier",
    "Other"
]

# Indian states
INDIAN_STATES = [
    "Andaman and Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli",
    "Daman and Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal"
]

# Payment terms
PAYMENT_TERMS = [
    "Advance",
    "30 Days",
    "45 Days",
    "60 Days",
    "90 Days",
    "Against Delivery",
    "Against Invoice"
]

# Currency
CURRENCY = "INR"
CURRENCY_SYMBOL = "₹"

# Date format
DATE_FORMAT = "%d-%m-%Y"
DATETIME_FORMAT = "%d-%m-%Y %H:%M"

# Financial year
def get_financial_year():
    from datetime import datetime
    today = datetime.now()
    if today.month >= 4:
        return f"{today.year}-{today.year + 1}"
    else:
        return f"{today.year - 1}-{today.year}"
