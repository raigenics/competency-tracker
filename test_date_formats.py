"""
Quick test to verify MMM-yy date format parsing.
"""
from datetime import datetime

# Test the new date formats
test_dates = [
    "Sep-25",           # MMM-yy
    "December-24",      # Full month-yy
    "1-Sep-25",         # dd-MMM-yy
    "01-Sep-2025",      # dd-MMM-yyyy
    "2025-09-01",       # ISO format
]

date_formats = [
    '%Y-%m-%d',      # 2011-02-02
    '%d-%m-%Y',      # 02-02-2011
    '%m/%d/%Y',      # 02/02/2011
    '%d/%m/%Y',      # 02/02/2011
    '%Y/%m/%d',      # 2011/02/02
    '%d-%b-%y',      # 1-Sep-25
    '%d-%B-%y',      # 1-September-25
    '%d-%b-%Y',      # 1-Sep-2025
    '%d-%B-%Y',      # 1-September-2025
    '%b-%y',         # Sep-25 (NEW)
    '%B-%y',         # September-25 (NEW)
]

def test_date_parsing():
    """Test all date formats."""
    print("Testing MMM-yy Date Format Parsing")
    print("=" * 60)
    
    for date_str in test_dates:
        print(f"\nTesting: '{date_str}'")
        parsed = False
        
        for fmt in date_formats:
            try:
                result = datetime.strptime(date_str, fmt).date()
                print(f"  ✓ Matched format '{fmt}' → {result}")
                parsed = True
                break
            except ValueError:
                continue
        
        if not parsed:
            print(f"  ✗ No format matched!")
    
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    test_date_parsing()
