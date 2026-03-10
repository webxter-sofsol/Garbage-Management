from datetime import datetime, timedelta
from django.utils import timezone


class PickupRequestValidator:
    """Validator for pickup request data."""
    
    VALID_WASTE_TYPES = ['general', 'recyclable', 'organic']
    
    @staticmethod
    def validate_pickup_request_data(waste_type, preferred_date, latitude, longitude, address, notes=None):
        """
        Validate pickup request data.
        
        Returns:
            tuple: (is_valid, errors_dict)
        """
        errors = {}
        
        # Validate waste type
        if not waste_type:
            errors['waste_type'] = 'Waste type is required'
        elif waste_type not in PickupRequestValidator.VALID_WASTE_TYPES:
            errors['waste_type'] = f'Invalid waste type. Must be one of: {", ".join(PickupRequestValidator.VALID_WASTE_TYPES)}'
        
        # Validate preferred date
        if not preferred_date:
            errors['preferred_date'] = 'Preferred date is required'
        else:
            try:
                # Parse date if it's a string
                if isinstance(preferred_date, str):
                    date_obj = datetime.strptime(preferred_date, '%Y-%m-%d').date()
                else:
                    date_obj = preferred_date
                
                # Check if date is at least 24 hours in future
                tomorrow = (timezone.now() + timedelta(days=1)).date()
                if date_obj < tomorrow:
                    errors['preferred_date'] = 'Preferred date must be at least 24 hours in the future'
            except ValueError:
                errors['preferred_date'] = 'Invalid date format. Use YYYY-MM-DD'
        
        # Validate coordinates
        if not latitude:
            errors['latitude'] = 'Latitude is required'
        else:
            try:
                lat = float(latitude)
                if lat < -90 or lat > 90:
                    errors['latitude'] = 'Latitude must be between -90 and 90'
            except (ValueError, TypeError):
                errors['latitude'] = 'Invalid latitude value'
        
        if not longitude:
            errors['longitude'] = 'Longitude is required'
        else:
            try:
                lon = float(longitude)
                if lon < -180 or lon > 180:
                    errors['longitude'] = 'Longitude must be between -180 and 180'
            except (ValueError, TypeError):
                errors['longitude'] = 'Invalid longitude value'
        
        # Validate address
        if not address or not address.strip():
            errors['address'] = 'Address is required'
        elif len(address.strip()) < 10:
            errors['address'] = 'Address must be at least 10 characters'
        
        # Validate notes (optional)
        if notes and notes.strip():
            if len(notes.strip()) < 10:
                errors['notes'] = 'Notes must be at least 10 characters if provided'
            elif len(notes.strip()) > 500:
                errors['notes'] = 'Notes must not exceed 500 characters'
        
        is_valid = len(errors) == 0
        return is_valid, errors
