"""
Setup script for initializing the search service and testing configuration.
"""
import os
import sys
from search.search_service import SearchService


def check_environment():
    """Check if required environment variables are set."""
    print("Checking environment configuration...")
    
    api_key = os.getenv('GOOGLE_API_KEY')
    cse_id = os.getenv('GOOGLE_CSE_ID')
    
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not set")
        return False
    else:
        print(f"✅ GOOGLE_API_KEY found (starts with: {api_key[:10]}...)")
    
    if not cse_id:
        print("❌ GOOGLE_CSE_ID environment variable not set")
        return False
    else:
        print(f"✅ GOOGLE_CSE_ID found: {cse_id}")
    
    return True


def test_search_service():
    """Test the search service with a sample query."""
    print("\nTesting search service...")
    
    try:
        search_service = SearchService()
        
        if not search_service.is_ready():
            print("❌ Search service not ready")
            return False
        
        print("✅ Search service initialized successfully")
        
        # Test with a well-known institution
        print("\nTesting with 'MIT university'...")
        result = search_service.search_institution("MIT", "university")
        
        if result.get('success'):
            print(f"✅ Search successful!")
            print(f"   - Found {len(result.get('results', []))} results")
            print(f"   - Total results: {result.get('total_results', '0')}")
            print(f"   - Response time: {result.get('response_time', 0):.3f}s")
            print(f"   - Source: {result.get('source', 'unknown')}")
            print(f"   - Cache hit: {result.get('cache_hit', False)}")
            
            # Show first result
            results = result.get('results', [])
            if results:
                first_result = results[0]
                print(f"   - First result: {first_result.get('title', 'No title')}")
                print(f"   - Link: {first_result.get('link', 'No link')}")
        else:
            print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing search service: {e}")
        return False


def show_stats():
    """Show current search service statistics."""
    print("\nSearch service statistics:")
    
    try:
        search_service = SearchService()
        stats = search_service.get_stats()
        
        print(f"Service configured: {stats.get('service_configured', False)}")
        
        cache_stats = stats.get('cache_stats', {})
        if cache_stats:
            print(f"Cache statistics:")
            print(f"  - Total cached queries: {cache_stats.get('total_cached_queries', 0)}")
            print(f"  - Cache hits: {cache_stats.get('cache_hits', 0)}")
            print(f"  - Cache misses: {cache_stats.get('cache_misses', 0)}")
            print(f"  - Hit rate: {cache_stats.get('hit_rate_percent', 0)}%")
        
        session_stats = stats.get('session_stats', {})
        if session_stats:
            print(f"Session statistics:")
            print(f"  - Total searches: {session_stats.get('total_searches', 0)}")
            print(f"  - Success rate: {session_stats.get('success_rate_percent', 0)}%")
            print(f"  - API calls: {session_stats.get('api_calls', 0)}")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")


def main():
    """Main setup function."""
    print("🔍 Search Service Setup")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment not properly configured!")
        print("\nPlease set the required environment variables:")
        print("1. Copy .env.example to .env")
        print("2. Fill in your Google API credentials")
        print("3. Set environment variables or load .env file")
        print("\nFor PowerShell:")
        print("   $env:GOOGLE_API_KEY='your_key_here'")
        print("   $env:GOOGLE_CSE_ID='your_cse_id_here'")
        return 1
    
    # Test search service
    if not test_search_service():
        print("\n❌ Search service test failed!")
        return 1
    
    # Show statistics
    show_stats()
    
    print("\n✅ Search service setup complete!")
    print("\nYou can now use the search endpoints:")
    print("- GET /search?name=institution_name&type=university")
    print("- GET /search/links?name=institution_name&max_links=10")
    print("- GET /search/stats")
    print("- GET /search/cache")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
