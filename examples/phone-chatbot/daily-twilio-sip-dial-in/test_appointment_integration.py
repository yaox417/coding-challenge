#!/usr/bin/env python3
"""Test integration of date converter with appointment scheduling."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.date_converter import DateConverter
from datetime import datetime


def test_appointment_integration():
    """Test how the date converter would work with appointment scheduling."""
    converter = DateConverter()
    
    print("=== APPOINTMENT SCHEDULING WITH DATE CONVERTER ===")
    print(f"Current date/time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    print(f"Today is: {datetime.now().strftime('%A')}")
    print()
    
    # Simulate the appointment options offered by the bot
    appointment_options = [
        "tomorrow at 3pm",
        "next Monday at 10am", 
        "next Wednesday at 11am"
    ]
    
    print("1. AVAILABLE APPOINTMENT SLOTS:")
    print("-" * 40)
    for i, option in enumerate(appointment_options, 1):
        converted = converter.convert_relative_date(option)
        print(f"{i}. {option} → {converted}")
    
    print("\n2. PATIENT RESPONSE SCENARIOS:")
    print("-" * 40)
    
    # Test various patient responses
    patient_responses = [
        ("tomorrow works for me", "tomorrow at 3pm"),
        ("Monday is good", "next Monday at 10am"),
        ("Wednesday please", "next Wednesday at 11am"),
        ("tomorrow or Monday", "tomorrow at 3pm"),  # First option
        ("Monday or Wednesday", "next Monday at 10am"),  # First option
        ("anything works", "tomorrow at 3pm"),  # Default to first
        ("none of those work", "Custom time needed"),
        ("I'm free Friday at 2pm", "Friday at 2pm"),
        ("How about Thursday morning?", "Thursday at 9am"),
    ]
    
    for response, selected_time in patient_responses:
        print(f"Patient says: '{response}'")
        print(f"  Selected: {selected_time}")
        
        if selected_time != "Custom time needed":
            converted = converter.convert_relative_date(selected_time)
            print(f"  Converted: {converted}")
        else:
            print(f"  Action: Ask patient for their preferred time")
        print()
    
    print("3. CUSTOM TIME HANDLING:")
    print("-" * 40)
    
    custom_times = [
        "Friday at 2pm",
        "next Thursday at 9am",
        "Monday morning",
        "tomorrow afternoon",
        "next week sometime",
        "two weeks from now at 1pm"
    ]
    
    for custom_time in custom_times:
        converted = converter.convert_relative_date(custom_time)
        detailed = converter.get_formatted_date_time(custom_time)
        
        print(f"Custom request: '{custom_time}'")
        print(f"  Converted: {converted}")
        if detailed['time_info']:
            print(f"  Time info: {detailed['time_info']}")
        print()
    
    print("4. EMAIL CONFIRMATION EXAMPLE:")
    print("-" * 40)
    
    # Simulate what would go in the email
    selected_appointment = "next Monday at 10am"
    converted_appointment = converter.convert_relative_date(selected_appointment)
    
    print(f"Selected appointment: {selected_appointment}")
    print(f"Email will show: {converted_appointment}")
    print()
    print("Sample email content:")
    print(f"Dear Patient,")
    print(f"Your appointment with Dr. Smith has been scheduled for:")
    print(f"{converted_appointment}")
    print(f"Please arrive 15 minutes early.")


if __name__ == "__main__":
    test_appointment_integration()
