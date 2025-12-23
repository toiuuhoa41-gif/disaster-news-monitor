from datetime import datetime
import json
import os

def get_current_time():
    """Return the current time in ISO format."""
    return datetime.now().isoformat()

def load_json_file(file_path):
    """Load a JSON file and return its content."""
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json_file(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def format_response(success, data=None, message=None):
    """Format a standard API response."""
    response = {
        "success": success,
        "timestamp": get_current_time()
    }
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return response

def validate_query_params(params, required_params):
    """Validate query parameters against required parameters."""
    missing_params = [param for param in required_params if param not in params]
    if missing_params:
        return False, missing_params
    return True, None

def extract_query_params(request):
    """Extract query parameters from a request."""
    return request.query_params

def log_error(message):
    """Log an error message."""
    # Placeholder for logging functionality
    print(f"ERROR: {message}")