"""
Validators for complaint data.
"""
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
import imghdr


class ComplaintValidator:
    """Validator class for complaint data."""
    
    @staticmethod
    def validate_description(description):
        """
        Validate complaint description length (10-500 characters).
        
        Args:
            description (str): Complaint description
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if not description:
            return False, "Description is required"
        
        description = description.strip()
        length = len(description)
        
        if length < 10:
            return False, f"Description must be at least 10 characters (currently {length})"
        
        if length > 500:
            return False, f"Description must not exceed 500 characters (currently {length})"
        
        return True, None
    
    @staticmethod
    def validate_coordinates(latitude, longitude):
        """
        Validate coordinate ranges.
        Latitude: -90 to 90
        Longitude: -180 to 180
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (TypeError, ValueError):
            return False, "Invalid coordinate format"
        
        if lat < -90 or lat > 90:
            return False, f"Latitude must be between -90 and 90 (got {lat})"
        
        if lon < -180 or lon > 180:
            return False, f"Longitude must be between -180 and 180 (got {lon})"
        
        return True, None
    
    @staticmethod
    def validate_photo_format(photo_file):
        """
        Validate photo file format using file headers (magic numbers).
        Allowed formats: JPEG, PNG, WebP
        
        Args:
            photo_file: Uploaded file object
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if not photo_file:
            return False, "Photo file is required"
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        file_name = photo_file.name.lower()
        
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            return False, f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
        
        # Check file header (magic numbers)
        try:
            # Read first few bytes to check file type
            photo_file.seek(0)
            header = photo_file.read(12)
            photo_file.seek(0)
            
            # Check for JPEG
            if header[:2] == b'\xff\xd8':
                return True, None
            
            # Check for PNG
            if header[:8] == b'\x89PNG\r\n\x1a\n':
                return True, None
            
            # Check for WebP
            if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
                return True, None
            
            return False, "Invalid image format. File header does not match JPEG, PNG, or WebP"
            
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    @staticmethod
    def validate_photo_size(photo_file, max_size_mb=5):
        """
        Validate photo file size (max 5MB).
        
        Args:
            photo_file: Uploaded file object
            max_size_mb (int): Maximum file size in MB
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if not photo_file:
            return False, "Photo file is required"
        
        max_size_bytes = max_size_mb * 1024 * 1024
        file_size = photo_file.size
        
        if file_size > max_size_bytes:
            size_mb = file_size / (1024 * 1024)
            return False, f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
        
        return True, None
    
    @staticmethod
    def validate_photo_count(photo_count, max_count=3):
        """
        Validate number of photos (max 3).
        
        Args:
            photo_count (int): Number of photos
            max_count (int): Maximum allowed photos
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if photo_count > max_count:
            return False, f"Maximum {max_count} photos allowed (got {photo_count})"
        
        return True, None
    
    @staticmethod
    def validate_photo(photo_file):
        """
        Validate photo file (format and size).
        
        Args:
            photo_file: Uploaded file object
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        # Validate format
        is_valid, error = ComplaintValidator.validate_photo_format(photo_file)
        if not is_valid:
            return False, error
        
        # Validate size
        is_valid, error = ComplaintValidator.validate_photo_size(photo_file)
        if not is_valid:
            return False, error
        
        return True, None
    
    @staticmethod
    def validate_complaint_data(description, latitude, longitude, photos=None):
        """
        Validate all complaint data.
        
        Args:
            description (str): Complaint description
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            photos (list): List of photo files (optional)
            
        Returns:
            tuple: (is_valid: bool, errors: dict)
        """
        errors = {}
        
        # Validate description
        is_valid, error = ComplaintValidator.validate_description(description)
        if not is_valid:
            errors['description'] = error
        
        # Validate coordinates
        is_valid, error = ComplaintValidator.validate_coordinates(latitude, longitude)
        if not is_valid:
            errors['location'] = error
        
        # Validate photos if provided
        if photos:
            # Validate photo count
            is_valid, error = ComplaintValidator.validate_photo_count(len(photos))
            if not is_valid:
                errors['photos'] = error
            else:
                # Validate each photo
                photo_errors = []
                for i, photo in enumerate(photos):
                    is_valid, error = ComplaintValidator.validate_photo(photo)
                    if not is_valid:
                        photo_errors.append(f"Photo {i+1}: {error}")
                
                if photo_errors:
                    errors['photos'] = '; '.join(photo_errors)
        
        return len(errors) == 0, errors


def validate_complaint_description(value):
    """Django validator for complaint description."""
    is_valid, error = ComplaintValidator.validate_description(value)
    if not is_valid:
        raise ValidationError(error)


def validate_latitude(value):
    """Django validator for latitude."""
    is_valid, error = ComplaintValidator.validate_coordinates(value, 0)
    if not is_valid:
        raise ValidationError(error)


def validate_longitude(value):
    """Django validator for longitude."""
    is_valid, error = ComplaintValidator.validate_coordinates(0, value)
    if not is_valid:
        raise ValidationError(error)
