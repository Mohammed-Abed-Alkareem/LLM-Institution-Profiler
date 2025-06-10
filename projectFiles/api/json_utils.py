# -*- coding: utf-8 -*-
"""
JSON utilities for the Institution Profiler API.
Provides custom JSON encoding to handle enum objects and other non-serializable types.
"""
import json
from enum import Enum
from flask import jsonify as flask_jsonify


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle enum objects and other non-serializable types."""
    
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def safe_jsonify(data, **kwargs):
    """
    Safe JSON serialization that handles enum objects.
    
    Args:
        data: Data to serialize
        **kwargs: Additional arguments passed to jsonify
        
    Returns:
        Flask JSON response with proper enum handling
    """
    # Convert any enum objects to their values before jsonifying
    def convert_enums(obj):
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {key: convert_enums(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_enums(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(convert_enums(item) for item in obj)
        else:
            return obj
    
    converted_data = convert_enums(data)
    return flask_jsonify(converted_data, **kwargs)


def safe_json_dumps(data, **kwargs):
    """
    Safe JSON dumps that handles enum objects.
    
    Args:
        data: Data to serialize
        **kwargs: Additional arguments passed to json.dumps
        
    Returns:
        JSON string with proper enum handling
    """
    return json.dumps(data, cls=CustomJSONEncoder, **kwargs)
