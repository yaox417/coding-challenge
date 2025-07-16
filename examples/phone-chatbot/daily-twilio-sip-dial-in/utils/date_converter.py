"""Date conversion utility for converting relative dates to actual dates."""

from datetime import datetime, timedelta
import re
from typing import Optional


class DateConverter:
    """Converts relative date expressions to actual calendar dates."""
    
    def __init__(self):
        """Initialize the date converter."""
        self.today = datetime.now()
    
    def convert_relative_date(self, relative_date: str) -> str:
        """
        Convert relative date expressions to actual calendar dates.
        
        Args:
            relative_date: String like "tomorrow at 3pm", "next Monday at 10am"
            
        Returns:
            String with actual date like "January 17, 2025 at 3:00 PM"
        """
        try:
            # Clean up the input
            relative_date = relative_date.lower().strip()
            
            # Extract time if present
            time_match = re.search(r'(\d{1,2})\s*(am|pm)', relative_date)
            time_str = ""
            if time_match:
                hour = int(time_match.group(1))
                period = time_match.group(2)
                
                # Convert to 12-hour format display
                if period == "pm" and hour != 12:
                    display_hour = hour
                elif period == "am" and hour == 12:
                    display_hour = 12
                else:
                    display_hour = hour
                
                time_str = f" at {display_hour}:00 {period.upper()}"
            
            # Calculate the target date
            target_date = None
            
            if "tomorrow" in relative_date:
                target_date = self.today + timedelta(days=1)
            
            elif "next monday" in relative_date or "monday" in relative_date:
                target_date = self._get_next_weekday(0)  # Monday is 0
            
            elif "next tuesday" in relative_date or "tuesday" in relative_date:
                target_date = self._get_next_weekday(1)  # Tuesday is 1
            
            elif "next wednesday" in relative_date or "wednesday" in relative_date:
                target_date = self._get_next_weekday(2)  # Wednesday is 2
            
            elif "next thursday" in relative_date or "thursday" in relative_date:
                target_date = self._get_next_weekday(3)  # Thursday is 3
            
            elif "next friday" in relative_date or "friday" in relative_date:
                target_date = self._get_next_weekday(4)  # Friday is 4
            
            elif "next week" in relative_date:
                target_date = self.today + timedelta(days=7)
            
            elif "two weeks" in relative_date or "2 weeks" in relative_date:
                target_date = self.today + timedelta(days=14)
            
            else:
                # there's more we need to do here
                return relative_date
            
            if target_date:
                # Format the date nicely
                formatted_date = target_date.strftime("%B %d, %Y")
                return f"{formatted_date}{time_str}"
            
            return relative_date
            
        except Exception as e:
            # If anything goes wrong, return the original
            return relative_date
    
    def _get_next_weekday(self, weekday: int) -> datetime:
        """
        Get the next occurrence of a specific weekday.
        
        Args:
            weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
            
        Returns:
            datetime object for the next occurrence of that weekday
        """
        days_ahead = weekday - self.today.weekday()
        
        # If the day is today or has passed this week, get next week's occurrence
        if days_ahead <= 0:
            days_ahead += 7
            
        return self.today + timedelta(days=days_ahead)
    
    def get_formatted_date_time(self, relative_date: str) -> dict:
        """
        Get both formatted date and structured date/time info.
        
        Args:
            relative_date: String like "tomorrow at 3pm"
            
        Returns:
            Dictionary with formatted_date, date_object, and time_info
        """
        formatted = self.convert_relative_date(relative_date)
        
        # Try to extract structured info
        result = {
            'formatted_date': formatted,
            'original': relative_date,
            'date_object': None,
            'time_info': None
        }
        
        try:
            # Extract time info
            time_match = re.search(r'(\d{1,2})\s*(am|pm)', relative_date.lower())
            if time_match:
                result['time_info'] = {
                    'hour': int(time_match.group(1)),
                    'period': time_match.group(2).upper()
                }
            
            # Get date object for further processing if needed
            if "tomorrow" in relative_date.lower():
                result['date_object'] = self.today + timedelta(days=1)
            elif "monday" in relative_date.lower():
                result['date_object'] = self._get_next_weekday(0)
            elif "tuesday" in relative_date.lower():
                result['date_object'] = self._get_next_weekday(1)
            elif "wednesday" in relative_date.lower():
                result['date_object'] = self._get_next_weekday(2)
            elif "thursday" in relative_date.lower():
                result['date_object'] = self._get_next_weekday(3)
            elif "friday" in relative_date.lower():
                result['date_object'] = self._get_next_weekday(4)
                
        except Exception:
            pass
            
        return result


# Example usage and testing
if __name__ == "__main__":
    converter = DateConverter()
    
    test_dates = [
        "tomorrow at 3pm",
        "next Monday at 10am",
        "next Wednesday at 11am",
        "Monday at 2pm",
        "tomorrow at 9am",
        "next Friday at 4pm"
    ]
    
    print("Date Conversion Examples:")
    print("=" * 50)
    
    for date in test_dates:
        converted = converter.convert_relative_date(date)
        print(f"'{date}' → '{converted}'")
    
    print("\nDetailed Info Example:")
    print("=" * 30)
    
    detailed = converter.get_formatted_date_time("tomorrow at 3pm")
    print(f"Formatted: {detailed['formatted_date']}")
    print(f"Original: {detailed['original']}")
    print(f"Time Info: {detailed['time_info']}")
