"""
Improved Institution Profiler Web Crawler Test

Based on working crawl4ai examples, this test properly crawls websites
and saves all results to files for inspection.
"""

import asyncio
import os
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, CrawlResult, BrowserConfig
from crawl4ai import JsonCssExtractionStrategy


async def test_basic_institution_crawl():
    """Test basic crawling with proper file output"""
    print("🚀 Testing Institution Profiler Web Crawler")
    print("=" * 60)
    
    # Create output directory
    output_dir = "crawler_test_results"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Test cases with reliable URLs
    test_cases = [
        {
            "name": "Example Website",
            "url": "https://example.com",
            "type": "general"
        },
        {
            "name": "HTTPBin HTML",
            "url": "https://httpbin.org/html",
            "type": "general"
        },
        {
            "name": "Harvard University",
            "url": "https://www.harvard.edu",
            "type": "university"
        }
    ]
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    # Configure browser for better success rate
    browser_config = BrowserConfig(
        headless=True,
        viewport_height=800,
        viewport_width=1200,
        verbose=True
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}/{total_tests}: Crawling {test_case['name']}")
            print("-" * 50)
            
            try:
                start_time = datetime.now()
                
                # Basic crawl configuration
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    word_count_threshold=10,
                    screenshot=True,  # Take screenshots
                    verbose=True
                )
                
                # Perform the crawl
                results: List[CrawlResult] = await crawler.arun(
                    url=test_case["url"],
                    config=config
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Process results
                for j, result in enumerate(results):
                    result_data = {
                        'test_info': {
                            'name': test_case['name'],
                            'url': test_case['url'],
                            'type': test_case['type'],
                            'crawl_duration_seconds': duration,
                            'timestamp': start_time.isoformat(),
                            'test_number': i,
                            'result_number': j + 1
                        },
                        'crawl_result': {
                            'success': result.success,
                            'status_code': result.status_code,
                            'url': result.url,
                            'metadata': result.metadata
                        }
                    }
                    
                    if result.success:
                        print(f"✅ Successfully crawled {test_case['url']}")
                        print(f"   Duration: {duration:.2f} seconds")
                        print(f"   Status: {result.status_code}")
                        
                        # Add content information
                        result_data['content'] = {
                            'has_html': bool(result.html),
                            'has_cleaned_html': bool(result.cleaned_html),
                            'has_markdown': bool(result.markdown),
                            'html_length': len(result.html) if result.html else 0,
                            'cleaned_html_length': len(result.cleaned_html) if result.cleaned_html else 0,
                            'markdown_length': len(result.markdown.raw_markdown) if result.markdown else 0,
                            'has_links': bool(result.links),
                            'has_images': bool(result.media and result.media.get('images')),
                            'internal_links_count': len(result.links.get('internal', [])) if result.links else 0,
                            'external_links_count': len(result.links.get('external', [])) if result.links else 0,
                            'images_count': len(result.media.get('images', [])) if result.media else 0
                        }
                        
                        # Save detailed JSON result
                        json_file = os.path.join(output_dir, f"result_{i}_{test_case['name'].replace(' ', '_')}.json")
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
                        
                        # Save raw HTML
                        if result.html:
                            html_file = os.path.join(output_dir, f"raw_html_{i}_{test_case['name'].replace(' ', '_')}.html")
                            with open(html_file, 'w', encoding='utf-8') as f:
                                f.write(result.html)
                            print(f"   Raw HTML saved: {html_file}")
                        
                        # Save cleaned HTML
                        if result.cleaned_html:
                            clean_html_file = os.path.join(output_dir, f"cleaned_html_{i}_{test_case['name'].replace(' ', '_')}.html")
                            with open(clean_html_file, 'w', encoding='utf-8') as f:
                                f.write(result.cleaned_html)
                            print(f"   Cleaned HTML saved: {clean_html_file}")
                        
                        # Save markdown
                        if result.markdown and result.markdown.raw_markdown:
                            md_file = os.path.join(output_dir, f"markdown_{i}_{test_case['name'].replace(' ', '_')}.md")
                            with open(md_file, 'w', encoding='utf-8') as f:
                                f.write(result.markdown.raw_markdown)
                            print(f"   Markdown saved: {md_file}")
                        
                        # Save links
                        if result.links:
                            links_file = os.path.join(output_dir, f"links_{i}_{test_case['name'].replace(' ', '_')}.json")
                            with open(links_file, 'w', encoding='utf-8') as f:
                                json.dump(result.links, f, indent=2, ensure_ascii=False)
                            print(f"   Links saved: {links_file}")
                        
                        # Save images info
                        if result.media and result.media.get('images'):
                            images_file = os.path.join(output_dir, f"images_{i}_{test_case['name'].replace(' ', '_')}.json")
                            with open(images_file, 'w', encoding='utf-8') as f:
                                json.dump(result.media['images'], f, indent=2, ensure_ascii=False)
                            print(f"   Images info saved: {images_file}")
                        
                        # Save screenshot if available
                        if result.screenshot:
                            screenshot_file = os.path.join(output_dir, f"screenshot_{i}_{test_case['name'].replace(' ', '_')}.png")
                            with open(screenshot_file, 'wb') as f:
                                if isinstance(result.screenshot, str):
                                    # Base64 encoded
                                    f.write(base64.b64decode(result.screenshot))
                                else:
                                    # Raw bytes
                                    f.write(result.screenshot)
                            print(f"   Screenshot saved: {screenshot_file}")
                        
                        # Create summary text file
                        summary_file = os.path.join(output_dir, f"summary_{i}_{test_case['name'].replace(' ', '_')}.txt")
                        with open(summary_file, 'w', encoding='utf-8') as f:
                            f.write(f"CRAWL SUMMARY: {test_case['name']}\n")
                            f.write("=" * 50 + "\n\n")
                            f.write(f"URL: {test_case['url']}\n")
                            f.write(f"Type: {test_case['type']}\n")
                            f.write(f"Success: {result.success}\n")
                            f.write(f"Status Code: {result.status_code}\n")
                            f.write(f"Crawl Duration: {duration:.2f} seconds\n")
                            f.write(f"Timestamp: {start_time.isoformat()}\n\n")
                            
                            if result.metadata:
                                f.write("METADATA:\n")
                                for key, value in result.metadata.items():
                                    f.write(f"  {key}: {value}\n")
                                f.write("\n")
                            
                            f.write("CONTENT SUMMARY:\n")
                            f.write(f"  HTML Length: {len(result.html) if result.html else 0:,} characters\n")
                            f.write(f"  Cleaned HTML Length: {len(result.cleaned_html) if result.cleaned_html else 0:,} characters\n")
                            f.write(f"  Markdown Length: {len(result.markdown.raw_markdown) if result.markdown else 0:,} characters\n")
                            f.write(f"  Internal Links: {len(result.links.get('internal', [])) if result.links else 0}\n")
                            f.write(f"  External Links: {len(result.links.get('external', [])) if result.links else 0}\n")
                            f.write(f"  Images Found: {len(result.media.get('images', [])) if result.media else 0}\n")
                            
                            if result.markdown and result.markdown.raw_markdown:
                                f.write(f"\nFIRST 500 CHARACTERS OF MARKDOWN:\n")
                                f.write("-" * 40 + "\n")
                                f.write(result.markdown.raw_markdown[:500])
                                if len(result.markdown.raw_markdown) > 500:
                                    f.write("\n... (truncated)")
                        
                        print(f"   Summary saved: {summary_file}")
                        successful_tests += 1
                        
                    else:
                        print(f"❌ Failed to crawl {test_case['url']}")
                        print(f"   Error: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
                        
                        # Save error information
                        error_file = os.path.join(output_dir, f"error_{i}_{test_case['name'].replace(' ', '_')}.json")
                        with open(error_file, 'w', encoding='utf-8') as f:
                            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
            
            except Exception as e:
                print(f"❌ Exception crawling {test_case['name']}: {str(e)}")
                
                # Save exception information
                error_data = {
                    'test_info': test_case,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'timestamp': datetime.now().isoformat()
                }
                error_file = os.path.join(output_dir, f"exception_{i}_{test_case['name'].replace(' ', '_')}.json")
                with open(error_file, 'w', encoding='utf-8') as f:
                    json.dump(error_data, f, indent=2, ensure_ascii=False)
    
    # Create final summary
    final_summary = {
        'test_run_summary': {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'success_rate_percent': (successful_tests / total_tests * 100) if total_tests > 0 else 0
        },
        'test_cases': test_cases,
        'output_directory': output_dir
    }
    
    summary_file = os.path.join(output_dir, "final_test_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(final_summary, f, indent=2, ensure_ascii=False)
    
    # Create human-readable summary
    readable_summary_file = os.path.join(output_dir, "RESULTS_SUMMARY.txt")
    with open(readable_summary_file, 'w', encoding='utf-8') as f:
        f.write("INSTITUTION PROFILER CRAWLER TEST RESULTS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Tests: {total_tests}\n")
        f.write(f"Successful: {successful_tests}\n")
        f.write(f"Failed: {total_tests - successful_tests}\n")
        f.write(f"Success Rate: {(successful_tests / total_tests * 100):.1f}%\n\n")
        
        f.write("TEST DETAILS:\n")
        f.write("-" * 30 + "\n")
        for i, test_case in enumerate(test_cases, 1):
            f.write(f"{i}. {test_case['name']} ({test_case['url']})\n")
        
        f.write(f"\nAll results saved to: {output_dir}/\n")
        f.write("Check individual files for detailed content and analysis.\n")
    
    print(f"\n📊 FINAL RESULTS")
    print("=" * 50)
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    print(f"📈 Success rate: {(successful_tests / total_tests * 100):.1f}%")
    print(f"📁 All results saved to: {output_dir}/")
    print(f"📋 Summary file: {readable_summary_file}")
    
    if successful_tests > 0:
        print("🎉 Crawler is working! Check the files for crawled content.")
    else:
        print("❌ No successful crawls. Check error files for details.")


async def main():
    """Run the improved crawler test"""
    print("🏁 Starting Improved Institution Profiler Crawler Test")
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        await test_basic_institution_crawl()
        print(f"\n🏆 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✅ Crawler test finished successfully!")
    except Exception as e:
        print(f"\n💥 Critical error: {str(e)}")
        print("❌ Crawler test failed")


if __name__ == "__main__":
    asyncio.run(main())
