# This file makes the api directory a Python package
from flask import Blueprint

# Create a Blueprint for the API
api_bp = Blueprint('api', __name__)

# Import routes after creating the blueprint to avoid circular imports
from . import routes
