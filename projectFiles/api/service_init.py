# -*- coding: utf-8 -*-
"""
Service initialization and configuration for the Institution Profiler application.
Centralizes all service setup and dependency injection.
"""
import os
from service_factory import initialize_autocomplete_with_all_institutions, get_autocomplete_service
from spell_check import SpellCorrectionService
from search.search_service import SearchService
from crawler.crawler_service import CrawlerService
from benchmarking.integration import initialize_benchmarking


def initialize_services(base_dir):
    """
    Initialize all application services and return a services dictionary.
    
    Args:
        base_dir: Base directory of the application
        
    Returns:
        dict: Dictionary containing all initialized services
    """
    services = {}
      # Initialize benchmarking system
    try:
        benchmarking_manager = initialize_benchmarking(base_dir)
        services['benchmarking'] = benchmarking_manager
        print("✅ Benchmarking system initialized")
    except Exception as e:
        print(f"⚠️ Warning: Benchmarking initialization failed: {e}")
        services['benchmarking'] = None

    # Initialize spell checking service
    dictionary_path = os.path.join(base_dir, 'spell_check', 'symspell_dict.txt')
    spell_service = SpellCorrectionService(dictionary_path=dictionary_path)
    services['spell_check'] = spell_service

    # Check if spell correction is available
    if not spell_service.is_initialized:
        print("Warning: Spell checking service is not initialized.")
        print("Spell checking will be disabled, but autocomplete will still work.")

    # Initialize autocomplete service with all institution types
    initialize_autocomplete_with_all_institutions(base_dir)
    autocomplete_service = get_autocomplete_service()
    services['autocomplete'] = autocomplete_service

    # Initialize search service
    search_service = SearchService(base_dir)
    services['search'] = search_service

    # Initialize crawler service
    crawler_service = CrawlerService(base_dir)
    services['crawler'] = crawler_service
    
    return services


def validate_services(services):
    """
    Validate that all critical services are properly initialized.
    
    Args:
        services: Dictionary of services to validate
        
    Returns:
        dict: Validation results
    """
    validation_results = {
        'all_services_ok': True,
        'service_status': {},
        'warnings': [],
        'errors': []
    }
    
    # Check autocomplete service
    if services.get('autocomplete') and services['autocomplete'].is_initialized:
        validation_results['service_status']['autocomplete'] = 'OK'
    else:
        validation_results['service_status']['autocomplete'] = 'FAILED'
        validation_results['errors'].append('Autocomplete service not initialized')
        validation_results['all_services_ok'] = False
    
    # Check search service
    if services.get('search'):
        validation_results['service_status']['search'] = 'OK'
    else:
        validation_results['service_status']['search'] = 'FAILED'
        validation_results['errors'].append('Search service not initialized')
        validation_results['all_services_ok'] = False
    
    # Check crawler service
    if services.get('crawler'):
        validation_results['service_status']['crawler'] = 'OK'
    else:
        validation_results['service_status']['crawler'] = 'FAILED'
        validation_results['errors'].append('Crawler service not initialized')
        validation_results['all_services_ok'] = False
    
    # Check spell check service
    if services.get('spell_check') and services['spell_check'].is_initialized:
        validation_results['service_status']['spell_check'] = 'OK'
    else:
        validation_results['service_status']['spell_check'] = 'WARNING'
        validation_results['warnings'].append('Spell check service not fully initialized')
    
    # Check benchmarking service
    if services.get('benchmarking'):
        validation_results['service_status']['benchmarking'] = 'OK'
    else:
        validation_results['service_status']['benchmarking'] = 'WARNING'
        validation_results['warnings'].append('Benchmarking service not initialized')
    
    return validation_results
