#!/usr/bin/env python3
"""Comprehensive test for the date converter functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.date_converter import DateConverter
from datetime import datetime, timedelta


def test_date_converter():
    """Test the date converter with various inputs."""
    converter = DateConverter()
    
    print("=== COMPREHENSIVE DATE CONVERTER TEST ===")
    print(f"Current date/time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    print(f"Today is: {datetime.now().strftime('%A')}")
    print()
    
    # Test cases with expected behavior
    test_cases = [
        # Basic relative dates
        "tomorrow at 3pm",
        "tomorrow at 9am",
        "tomorrow at 12pm",
        
        # Weekdays
        "Monday at 2pm",
        "Tuesday at 10am",
        "Wednesday at 11am",
        "Thursday at 1pm",
        "Friday at 4pm",
        
        # Next weekdays
        "next Monday at 10am",
        "next Tuesday at 2pm",
        "next Wednesday at 11am",
        "next Thursday at 3pm",
        "next Friday at 4pm",
        
        # Time variations
        "Monday at 1am",
        "Tuesday at 12am",
        "Wednesday at 11pm",
        
        # Week-based
        "next week",
        "two weeks",
        "2 weeks",
        
        # Edge cases
        "invalid date string",
        "Monday",  # No time specified
        "3pm",     # No date specified
        "",        # Empty string
    ]
    
    print("1. BASIC CONVERSION TESTS:")
    print("-" * 50)
    
    for i, test_input in enumerate(test_cases, 1):
        try:
            result = converter.convert_relative_date(test_input)
            print(f"{i:2d}. '{test_input}' → '{result}'")
        except Exception as e:
            print(f"{i:2d}. '{test_input}' → ERROR: {e}")
    
    print("\n2. DETAILED INFO TESTS:")
    print("-" * 50)
    
    detailed_tests = [
        "tomorrow at 3pm",
        "next Monday at 10am",
        "Friday at 2pm"
    ]
    
    for test_input in detailed_tests:
        try:
            result = converter.get_formatted_date_time(test_input)
            print(f"Input: '{test_input}'")
            print(f"  Formatted: {result['formatted_date']}")
            print(f"  Original: {result['original']}")
            print(f"  Time Info: {result['time_info']}")
            if result['date_object']:
                print(f"  Date Object: {result['date_object'].strftime('%Y-%m-%d %A')}")
            print()
        except Exception as e:
            print(f"ERROR with '{test_input}': {e}")
    
    print("3. WEEKDAY CALCULATION VERIFICATION:")
    print("-" * 50)
    
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for day in weekdays:
        try:
            result = converter.convert_relative_date(f"{day} at 2pm")
            # Get the actual date object to verify the weekday
            if day.lower() == 'monday':
                date_obj = converter._get_next_weekday(0)
            elif day.lower() == 'tuesday':
                date_obj = converter._get_next_weekday(1)
            elif day.lower() == 'wednesday':
                date_obj = converter._get_next_weekday(2)
            elif day.lower() == 'thursday':
                date_obj = converter._get_next_weekday(3)
            elif day.lower() == 'friday':
                date_obj = converter._get_next_weekday(4)
            
            actual_weekday = date_obj.strftime('%A')
            print(f"{day} → {result} (Actual weekday: {actual_weekday})")
            
            # Verify it's actually the correct weekday
            if actual_weekday == day:
                print("  ✓ Weekday calculation is correct")
            else:
                print("  ✗ Weekday calculation is INCORRECT")
                
        except Exception as e:
            print(f"ERROR with {day}: {e}")
        print()


if __name__ == "__main__":
    test_date_converter()
