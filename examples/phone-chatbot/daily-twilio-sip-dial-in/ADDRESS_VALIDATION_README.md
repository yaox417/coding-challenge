# Google Maps Address Validation Integration

This document describes the Google Maps API integration for address validation in the phone chatbot system.

## Overview

The system now includes real-time address validation using Google's Geocoding API to ensure that patient addresses are accurate and complete before storing them in the system.

## Features

- **Real-time validation**: Addresses are validated as soon as they're provided by the patient
- **Formatted addresses**: Valid addresses are automatically formatted to Google's standard format
- **Error handling**: Invalid or incomplete addresses trigger retry prompts with specific error messages
- **Graceful fallback**: If the validation service is unavailable, addresses are accepted as-is to prevent blocking the conversation flow

## Setup

### 1. Google Maps API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Geocoding API
   - Places API (optional, for future address suggestions)
4. Create an API key with appropriate restrictions
5. Add the API key to your `.env` file:

```bash
GOOGLE_MAPS_API_KEY=your_api_key_here
```

### 2. Dependencies

The required dependency is already added to `requirements.txt`:

```
googlemaps
```

Install it with:
```bash
# If using a virtual environment (recommended)
source .venv/bin/activate
pip install googlemaps

# Or globally
pip3 install googlemaps
```

## How It Works

### Address Validation Flow

1. **Patient provides address**: During the conversation flow, when the patient provides their address
2. **API validation**: The system calls Google's Geocoding API to validate the address
3. **Result processing**:
   - **Valid address**: Formatted address is stored and conversation continues
   - **Invalid address**: Patient is asked to provide a complete address again
   - **Service error**: Address is accepted as-is to prevent blocking

### Validation Criteria

An address is considered valid if it has:
- Basic components (street/route and locality/city)
- Good location accuracy (ROOFTOP or RANGE_INTERPOLATED)
- Street number (for complete addresses)

### Error Messages

The system provides specific error messages for different validation failures:
- "Address not found. Please provide a more specific address."
- "Please provide a complete address with street, city, and state."
- "The address seems incomplete. Please provide the full street address including house number."

## Code Structure

### Files Modified/Added

1. **`utils/address_validator.py`**: Core address validation logic
2. **`bot.py`**: Integration with the conversation flow
3. **`requirements.txt`**: Added googlemaps dependency
4. **`.env`**: Added GOOGLE_MAPS_API_KEY

### Key Components

#### AddressValidator Class

```python
class AddressValidator:
    def validate_address(self, address: str) -> Tuple[bool, Optional[Dict], Optional[str]]
    def get_address_suggestions(self, partial_address: str) -> list
    def format_address_for_speech(self, address_data: Dict) -> str
```

#### Modified Functions

- `collect_address()`: Now includes validation logic
- `create_address_retry_node()`: New node for handling validation failures

## Testing

Run the test script to verify the integration:

```bash
python3 test_address_validation.py
```

This will test various address formats and show validation results.

## API Usage and Costs

- **Geocoding API**: Used for address validation
- **Pricing**: Check [Google Maps Platform Pricing](https://developers.google.com/maps/billing-and-pricing/pricing)
- **Rate limits**: 50 requests per second by default
- **Optimization**: Consider implementing caching for frequently validated addresses

## Error Handling

The system includes comprehensive error handling:

1. **API errors**: Gracefully handled with fallback to accepting address as-is
2. **Network issues**: Timeout and retry logic
3. **Invalid API key**: Clear error messages for configuration issues
4. **Rate limiting**: Proper handling of API quota limits

## Security Considerations

1. **API key restrictions**: Restrict the API key to specific APIs and domains/IPs
2. **Environment variables**: Never commit API keys to version control
3. **Input validation**: Addresses are sanitized before API calls
4. **Logging**: Sensitive information is not logged

## Future Enhancements

1. **Address suggestions**: Implement autocomplete for partial addresses
2. **Caching**: Cache validated addresses to reduce API calls
3. **Batch validation**: For processing multiple addresses
4. **International support**: Enhanced validation for international addresses
5. **Address confidence scoring**: Provide confidence levels for validated addresses

## Troubleshooting

### Common Issues

1. **"GOOGLE_MAPS_API_KEY environment variable is required"**
   - Ensure the API key is set in your `.env` file

2. **"Google Maps API error"**
   - Check API key permissions and quotas
   - Verify the Geocoding API is enabled

3. **"Address validation service error"**
   - Check network connectivity
   - Verify API key is valid and has sufficient quota

### Debug Mode

Enable debug logging to see detailed validation information:

```python
logger.add(sys.stderr, level="DEBUG")
```

## Support

For issues related to:
- Google Maps API: [Google Maps Platform Support](https://developers.google.com/maps/support)
- Integration issues: Check the logs and test script output
