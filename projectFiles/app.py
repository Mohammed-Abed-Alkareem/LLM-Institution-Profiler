# -*- coding: utf-8 -*-
"""
Main Flask application for the Institution Profiler.
Refactored for better organization and maintainability.
"""
import os
from flask import Flask

# Import route modules
from api.core_routes import register_core_routes
from api.search_routes import register_search_routes
from api.crawler_routes import register_crawler_routes
from api.benchmark_routes import register_benchmark_routes
from api.utility_routes import register_utility_routes
from api.service_init import initialize_services, validate_services


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Get base directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize all services
    print("🚀 Initializing Institution Profiler services...")
    services = initialize_services(BASE_DIR)
    
    # Validate services
    validation = validate_services(services)
    if not validation['all_services_ok']:
        print("⚠️ Some services failed to initialize:")
        for error in validation['errors']:
            print(f"   ❌ {error}")
    
    if validation['warnings']:
        for warning in validation['warnings']:
            print(f"   ⚠️ {warning}")
    
    if validation['all_services_ok']:
        print("✅ All critical services initialized successfully")
    
    # Register all route modules
    register_core_routes(app, services)
    register_search_routes(app, services)
    register_crawler_routes(app, services)
    register_benchmark_routes(app, services)
    register_utility_routes(app, services)
    
    # Add a health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for monitoring."""
        return {
            'status': 'healthy',
            'services': validation['service_status'],
            'all_services_ok': validation['all_services_ok']
        }
    
    # Add service status endpoint
    @app.route('/services/status', methods=['GET'])
    def services_status():
        """Detailed service status endpoint."""
        return {
            'validation_results': validation,
            'service_details': {
                'autocomplete_stats': services['autocomplete'].get_stats() if services.get('autocomplete') else None,
                'search_stats': services['search'].get_stats() if services.get('search') else None,
                'benchmarking_summary': services['benchmarking'].get_session_summary() if services.get('benchmarking') else None
            }
        }
    
    return app


# Create the Flask app instance
app = create_app()


if __name__ == '__main__':
    print("🌟 Starting Institution Profiler Flask Application")
    print("📊 Access the application at: http://localhost:5000")
    print("🔍 API documentation available at various endpoints")
    app.run(debug=True, host='0.0.0.0', port=5000)
