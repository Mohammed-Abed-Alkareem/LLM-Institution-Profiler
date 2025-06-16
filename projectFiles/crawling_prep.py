"""
Link extraction and crawling preparation for institution data.
Enhanced with priority-based crawling configurations and smart keyword detection.
"""
import os
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
from search.search_service import SearchService


@dataclass
class CrawlPriorityConfig:
	"""Configuration for priority-based crawling."""
	high_priority_max_depth: int = 3
	high_priority_max_pages: int = 25
	medium_priority_max_depth: int = 2
	medium_priority_max_pages: int = 15
	low_priority_max_depth: int = 1
	low_priority_max_pages: int = 8
	priority_threshold_high: int = 100
	priority_threshold_medium: int = 50


@dataclass
class BenchmarkConfig:
	"""Configuration for benchmarking different crawling strategies."""
	strategy: str = "priority_based"  # "equal", "priority_based", "high_links", "high_depth"
	equal_depth: int = 2
	equal_max_pages: int = 15
	high_links_multiplier: float = 1.5
	high_depth_multiplier: float = 1.5


class InstitutionLinkManager:
	"""Manages links for institution crawling and data extraction with priority-based configurations."""
	def __init__(self, base_dir: str = None, search_service=None, 
				 priority_config: CrawlPriorityConfig = None,
				 benchmark_config: BenchmarkConfig = None):
		self.base_dir = base_dir or os.getcwd()
		self.search_service = search_service if search_service else SearchService(base_dir)
		self.priority_config = priority_config or CrawlPriorityConfig()
		self.benchmark_config = benchmark_config or BenchmarkConfig()
		self.keyword_patterns = self._initialize_keyword_patterns()
	
	def get_crawling_links(self, institution_name: str, institution_type: str = None, 
						  max_links: int = 10, include_search_metadata: bool = True, search_params: dict = None) -> Dict:
		"""
		Get links for institution crawling with metadata.
		
		Args:
			institution_name: Name of the institution
			institution_type: Type of institution (if known)
			max_links: Maximum number of links to return
			include_search_metadata: Whether to include search metadata
			search_params: Enhanced search parameters (location, keywords, domain_hint, exclude_terms)
			
		Returns:
			Dictionary with links and metadata for crawling
		"""
		# Get search results with links using enhanced search params
		search_result = self.search_service.search_institution(institution_name, institution_type, search_params=search_params)
		
		crawling_data = {
			'institution_name': institution_name,
			'institution_type': institution_type,
			'search_successful': search_result.get('success', False),
			'links': [],
			'metadata': {}
		}
		
		if not search_result.get('success'):
			crawling_data['error'] = search_result.get('error', 'Search failed')
			return crawling_data
				# Extract links from search results
		links = []
		for item in search_result.get('results', []):
			link = item.get('link')
			if link and link not in links:
				priority_score = self._calculate_link_priority(link, item, institution_type)
				priority_tier = self._calculate_priority_tier(priority_score)
				
				links.append({
					'url': link,
					'title': item.get('title', ''),
					'snippet': item.get('snippet', ''),
					'display_link': item.get('displayLink', ''),
					'priority': priority_score,
					'priority_tier': priority_tier
				})
				
				if len(links) >= max_links:
					break
		
		# Sort by priority (higher is better)
		links.sort(key=lambda x: x['priority'], reverse=True)
		
		# Apply benchmark strategy for configurable crawling parameters
		links = self._apply_benchmark_strategy(links)
		
		crawling_data['links'] = links
		
		if include_search_metadata:
			crawling_data['metadata'] = {
				'total_search_results': search_result.get('total_results', '0'),
				'search_time': search_result.get('search_time', 0),
				'cache_hit': search_result.get('cache_hit', False),
				'source': search_result.get('source', 'unknown'),
				'response_time': search_result.get('response_time', 0)
			}
		
		return crawling_data	
	def _calculate_link_priority(self, url: str, search_item: Dict, institution_type: str = None) -> int:
		"""Calculate priority score for a link (higher = better)."""
		priority = 0
		url_lower = url.lower()
		title_lower = search_item.get('title', '').lower()
		snippet_lower = search_item.get('snippet', '').lower()
		
		# Get institution category for smart keyword matching
		category = self._get_institution_category(institution_type, url, title_lower)
		keyword_patterns = self.keyword_patterns.get(category, {})
		
		# Official domain indicators (highest priority)
		if any(domain in url_lower for domain in ['.edu', '.org', '.gov']):
			priority += 100
		
		# Domain pattern matching based on category
		domain_patterns = keyword_patterns.get('domain_patterns', [])
		for pattern in domain_patterns:
			if re.search(pattern, url_lower):
				priority += 80
				break
		
		# Title indicator matching
		title_indicators = keyword_patterns.get('title_indicators', [])
		for indicator in title_indicators:
			if indicator in title_lower:
				priority += 60
				break
		
		# Smart keyword detection in content
		primary_keywords = keyword_patterns.get('primary_keywords', [])
		for pattern in primary_keywords:
			if re.search(pattern, title_lower, re.IGNORECASE):
				priority += 40
			if re.search(pattern, snippet_lower, re.IGNORECASE):
				priority += 30
		
		# Secondary keyword detection
		secondary_keywords = keyword_patterns.get('secondary_keywords', [])
		for pattern in secondary_keywords:
			if re.search(pattern, title_lower, re.IGNORECASE):
				priority += 20
			if re.search(pattern, snippet_lower, re.IGNORECASE):
				priority += 15
		
		# Institution type specific priorities (legacy support)
		if institution_type:
			if institution_type.lower() in ['university', 'college', 'school', 'edu']:
				if any(edu_indicator in url_lower for edu_indicator in ['.edu', 'university', 'college']):
					priority += 50
				if any(edu_word in title_lower for edu_word in ['university', 'college', 'school']):
					priority += 30
			
			elif institution_type.lower() in ['hospital', 'clinic', 'medical', 'med']:
				if any(med_indicator in url_lower for med_indicator in ['hospital', 'medical', 'health']):
					priority += 50
				if any(med_word in title_lower for med_word in ['hospital', 'medical', 'health', 'clinic']):
					priority += 30
			
			elif institution_type.lower() in ['bank', 'financial', 'fin']:
				if any(fin_indicator in url_lower for fin_indicator in ['bank', 'financial']):
					priority += 50
				if any(fin_word in title_lower for fin_word in ['bank', 'financial']):
					priority += 30
		
		# Homepage indicators
		if any(homepage in url_lower for homepage in ['/', '/home', '/index', '/about']):
			priority += 20
		
		# Official pages
		if any(official in title_lower for official in ['official', 'homepage', 'home']):
			priority += 15
		
		# Contact and information pages
		if any(info_page in url_lower for info_page in ['/contact', '/about', '/info']):
			priority += 10
		
		# Avoid less useful pages
		if any(avoid in url_lower for avoid in ['facebook', 'twitter', 'linkedin', 'wikipedia']):
			priority -= 20
		
		# Avoid non-informative pages
		if any(avoid in url_lower for avoid in ['/search?', '/login', '/register', '/cart', '/shop']):
			priority -= 30
		
		return priority
	def prepare_crawling_config(self, institution_data: Dict, crawl_depth: int = 2) -> Dict:
		"""
		Prepare configuration for web crawling based on institution data with priority-based settings.
		
		Args:
			institution_data: Data from get_crawling_links()
			crawl_depth: How deep to crawl (1 = just provided links, 2+ = follow links) - deprecated, now uses priority-based depths
			
		Returns:
			Crawling configuration dictionary with priority-based settings
		"""
		# Build priority-based URL configurations
		url_configs = []
		for link in institution_data.get('links', []):
			url_config = {
				'url': link['url'],
				'priority': link.get('priority', 0),
				'priority_tier': link.get('priority_tier', 'medium'),
				'crawl_depth': link.get('crawl_depth', crawl_depth),
				'max_pages': link.get('max_pages', 15),
				'title': link.get('title', ''),
				'snippet': link.get('snippet', '')
			}
			url_configs.append(url_config)
		
		config = {
			'institution_name': institution_data['institution_name'],
			'institution_type': institution_data['institution_type'],
			'seed_urls': [link['url'] for link in institution_data['links']],
			'url_configs': url_configs,
			'benchmark_strategy': self.benchmark_config.strategy,
			'crawl_settings': {
				'respect_robots_txt': True,
				'delay_between_requests': 1.0,
				'timeout': 30,
				'max_file_size': 5 * 1024 * 1024,  # 5MB
				'allowed_content_types': ['text/html', 'text/plain'],
				'exclude_patterns': [
					r'\.pdf$', r'\.doc$', r'\.docx$', r'\.ppt$', r'\.pptx$',
					r'/search\?', r'/login', r'/register', r'/cart',
					r'facebook\.com', r'twitter\.com', r'linkedin\.com'
				]
			},
			'extraction_targets': self._get_extraction_targets(institution_data['institution_type']),
			'metadata': institution_data.get('metadata', {}),
			'priority_summary': self._generate_priority_summary(url_configs)
		}
		
		return config
	
	def _get_extraction_targets(self, institution_type: str = None) -> List[str]:
		"""Get target information types for extraction based on institution type."""
		common_targets = [
			'institution_name', 'official_name', 'address', 'city', 'state', 'country',
			'phone', 'email', 'website', 'description', 'established_date'
		]
		
		if not institution_type:
			return common_targets
		
		type_lower = institution_type.lower()
		
		if type_lower in ['university', 'college', 'school', 'edu']:
			return common_targets + [
				'student_population', 'faculty_count', 'programs_offered',
				'accreditation', 'ranking', 'tuition_fees', 'campus_size',
				'academic_divisions', 'research_areas'
			]
		
		elif type_lower in ['hospital', 'clinic', 'medical', 'med']:
			return common_targets + [
				'bed_count', 'medical_specialties', 'services_offered',
				'accreditation', 'certifications', 'emergency_services',
				'staff_count', 'patient_capacity'
			]
		
		elif type_lower in ['bank', 'financial', 'fin']:
			return common_targets + [
				'institution_type', 'regulatory_body', 'license_number',
				'services_offered', 'branches_count', 'assets_size',
				'founding_date', 'headquarters', 'subsidiaries'
			]
		
		return common_targets
	
	def _initialize_keyword_patterns(self) -> Dict[str, Dict]:
		"""Initialize smart keyword patterns for different institution types."""
		return {
			'educational': {
				'primary_keywords': [
					r'\b(university|college|school|academy|institute)\b',
					r'\b(student|faculty|professor|dean|academic)\b',
					r'\b(degree|bachelor|master|phd|graduate|undergraduate)\b',
					r'\b(campus|classroom|library|dormitor(y|ies))\b'
				],
				'secondary_keywords': [
					r'\b(tuition|enrollment|admission|registrar)\b',
					r'\b(research|publication|journal|conference)\b',
					r'\b(accreditation|ranking|curriculum)\b'
				],
				'domain_patterns': [r'\.edu$', r'university\.|college\.', r'school\.'],
				'title_indicators': ['university', 'college', 'school', 'institute', 'academy']
			},
			'medical': {
				'primary_keywords': [
					r'\b(hospital|clinic|medical|health|healthcare)\b',
					r'\b(doctor|physician|nurse|patient|treatment)\b',
					r'\b(emergency|surgery|department|ward)\b',
					r'\b(medicine|therapy|diagnostic|care)\b'
				],
				'secondary_keywords': [
					r'\b(specialist|consultation|appointment|admission)\b',
					r'\b(laboratory|pharmacy|radiology|cardiology)\b',
					r'\b(accredited|certified|licensed)\b'
				],
				'domain_patterns': [r'health\.|medical\.|hospital\.', r'\.org$'],
				'title_indicators': ['hospital', 'medical', 'health', 'clinic', 'healthcare']
			},
			'financial': {
				'primary_keywords': [
					r'\b(bank|banking|financial|finance|credit)\b',
					r'\b(loan|mortgage|investment|account|deposit)\b',
					r'\b(branch|atm|customer|service)\b',
					r'\b(insurance|wealth|advisory|trust)\b'
				],
				'secondary_keywords': [
					r'\b(fdic|federal|reserve|regulation|compliance)\b',
					r'\b(corporate|commercial|personal|business)\b',
					r'\b(interest|rate|fee|statement)\b'
				],
				'domain_patterns': [r'bank\.|financial\.|\.com$'],
				'title_indicators': ['bank', 'financial', 'credit', 'insurance']
			},
			'corporate': {
				'primary_keywords': [
					r'\b(company|corporation|business|enterprise)\b',
					r'\b(headquarters|office|location|facility)\b',
					r'\b(employee|staff|team|department)\b',
					r'\b(product|service|solution|technology)\b'
				],
				'secondary_keywords': [
					r'\b(founded|established|ceo|president|executive)\b',
					r'\b(revenue|profit|growth|market)\b',
					r'\b(industry|sector|global|international)\b'
				],
				'domain_patterns': [r'\.com$', r'\.org$', r'\.net$'],
				'title_indicators': ['company', 'corporation', 'inc', 'ltd', 'llc']
			}
		}

	def _get_institution_category(self, institution_type: str = None, url: str = "", title: str = "") -> str:
		"""Determine institution category for smart keyword matching."""
		if not institution_type:
			# Try to infer from URL and title
			url_lower = url.lower()
			title_lower = title.lower()
			
			if any(edu in url_lower for edu in ['.edu', 'university', 'college', 'school']):
				return 'educational'
			elif any(med in url_lower for med in ['hospital', 'medical', 'health']):
				return 'medical'
			elif any(fin in url_lower for fin in ['bank', 'financial']):
				return 'financial'
			else:
				return 'corporate'
		
		type_lower = institution_type.lower()
		if type_lower in ['university', 'college', 'school', 'edu', 'educational']:
			return 'educational'
		elif type_lower in ['hospital', 'clinic', 'medical', 'med', 'healthcare']:
			return 'medical'
		elif type_lower in ['bank', 'financial', 'fin', 'credit']:
			return 'financial'
		else:
			return 'corporate'

	def _calculate_priority_tier(self, priority_score: int) -> str:
		"""Calculate priority tier based on score."""
		if priority_score >= self.priority_config.priority_threshold_high:
			return 'high'
		elif priority_score >= self.priority_config.priority_threshold_medium:
			return 'medium'
		else:
			return 'low'

	def _apply_benchmark_strategy(self, links: List[Dict]) -> List[Dict]:
		"""Apply benchmarking strategy to modify crawling parameters."""
		strategy = self.benchmark_config.strategy
		
		for link in links:
			base_depth = 2
			base_pages = 15
			
			if strategy == "equal":
				link['crawl_depth'] = self.benchmark_config.equal_depth
				link['max_pages'] = self.benchmark_config.equal_max_pages
			
			elif strategy == "high_links":
				tier = link.get('priority_tier', 'medium')
				multiplier = self.benchmark_config.high_links_multiplier if tier == 'high' else 1.0
				link['crawl_depth'] = base_depth
				link['max_pages'] = int(base_pages * multiplier)
			
			elif strategy == "high_depth":
				tier = link.get('priority_tier', 'medium')
				multiplier = self.benchmark_config.high_depth_multiplier if tier == 'high' else 1.0
				link['crawl_depth'] = int(base_depth * multiplier)
				link['max_pages'] = base_pages
			
			else:  # priority_based (default)
				tier = link.get('priority_tier', 'medium')
				if tier == 'high':
					link['crawl_depth'] = self.priority_config.high_priority_max_depth
					link['max_pages'] = self.priority_config.high_priority_max_pages
				elif tier == 'medium':
					link['crawl_depth'] = self.priority_config.medium_priority_max_depth
					link['max_pages'] = self.priority_config.medium_priority_max_pages
				else:
					link['crawl_depth'] = self.priority_config.low_priority_max_depth
					link['max_pages'] = self.priority_config.low_priority_max_pages
		
		return links
	
	def _generate_priority_summary(self, url_configs: List[Dict]) -> Dict:
		"""Generate a summary of priority distribution for benchmarking."""
		summary = {
			'total_urls': len(url_configs),
			'high_priority': 0,
			'medium_priority': 0,
			'low_priority': 0,
			'avg_crawl_depth': 0,
			'total_max_pages': 0
		}
		
		for config in url_configs:
			tier = config.get('priority_tier', 'medium')
			if tier == 'high':
				summary['high_priority'] += 1
			elif tier == 'medium':
				summary['medium_priority'] += 1
			else:
				summary['low_priority'] += 1
			
			summary['avg_crawl_depth'] += config.get('crawl_depth', 2)
			summary['total_max_pages'] += config.get('max_pages', 15)
		
		if summary['total_urls'] > 0:
			summary['avg_crawl_depth'] = summary['avg_crawl_depth'] / summary['total_urls']
		
		return summary
def get_institution_links_for_crawling(institution_name: str, institution_type: str = None, 
									 max_links: int = 10, base_dir: str = None, search_params: dict = None) -> Dict:
	"""
	Convenience function to get institution links for crawling.
	
	Args:
		institution_name: Name of the institution
		institution_type: Type of institution
		max_links: Maximum number of links to return
		base_dir: Base directory for search service
		search_params: Enhanced search parameters (location, keywords, domain_hint, exclude_terms)
		
	Returns:
		Dictionary with links and metadata for crawling
	"""
	link_manager = InstitutionLinkManager(base_dir)
	return link_manager.get_crawling_links(institution_name, institution_type, max_links, search_params=search_params)

# Convenience functions for different crawling strategies

def create_equal_distribution_config() -> BenchmarkConfig:
	"""Create benchmark config for equal distribution strategy."""
	return BenchmarkConfig(
		strategy="equal",
		equal_depth=2,
		equal_max_pages=15
	)


def create_priority_based_config(high_threshold: int = 100, medium_threshold: int = 50) -> Tuple[CrawlPriorityConfig, BenchmarkConfig]:
	"""Create priority-based crawling configuration."""
	priority_config = CrawlPriorityConfig(
		high_priority_max_depth=3,
		high_priority_max_pages=25,
		medium_priority_max_depth=2,
		medium_priority_max_pages=15,
		low_priority_max_depth=1,
		low_priority_max_pages=8,
		priority_threshold_high=high_threshold,
		priority_threshold_medium=medium_threshold
	)
	
	benchmark_config = BenchmarkConfig(strategy="priority_based")
	
	return priority_config, benchmark_config


def create_high_links_config(multiplier: float = 1.5) -> BenchmarkConfig:
	"""Create benchmark config for high links strategy."""
	return BenchmarkConfig(
		strategy="high_links",
		high_links_multiplier=multiplier
	)


def create_high_depth_config(multiplier: float = 1.5) -> BenchmarkConfig:
	"""Create benchmark config for high depth strategy."""
	return BenchmarkConfig(
		strategy="high_depth",
		high_depth_multiplier=multiplier
	)


def get_institution_links_with_strategy(institution_name: str, institution_type: str = None,
										max_links: int = 10, strategy: str = "priority_based",
										base_dir: str = None, search_params: dict = None) -> Dict:
	"""
	Get institution links with specific crawling strategy applied.
	
	Args:
		institution_name: Name of the institution
		institution_type: Type of institution
		max_links: Maximum number of links to return
		strategy: Crawling strategy ("equal", "priority_based", "high_links", "high_depth")
		base_dir: Base directory for search service
		search_params: Enhanced search parameters
		
	Returns:
		Dictionary with links, metadata, and strategy-specific crawling configurations
	"""
	if strategy == "equal":
		benchmark_config = create_equal_distribution_config()
		priority_config = CrawlPriorityConfig()
	elif strategy == "high_links":
		benchmark_config = create_high_links_config()
		priority_config = CrawlPriorityConfig()
	elif strategy == "high_depth":
		benchmark_config = create_high_depth_config()
		priority_config = CrawlPriorityConfig()
	else:  # priority_based
		priority_config, benchmark_config = create_priority_based_config()
	
	link_manager = InstitutionLinkManager(
		base_dir=base_dir,
		priority_config=priority_config,
		benchmark_config=benchmark_config
	)
	
	return link_manager.get_crawling_links(
		institution_name, institution_type, max_links, 
		search_params=search_params
	)


def compare_crawling_strategies(institution_name: str, institution_type: str = None,
								max_links: int = 10, base_dir: str = None,
								search_params: dict = None) -> Dict:
	"""
	Compare different crawling strategies for the same institution.
	
	Args:
		institution_name: Name of the institution
		institution_type: Type of institution
		max_links: Maximum number of links to return
		base_dir: Base directory for search service
		search_params: Enhanced search parameters
		
	Returns:
		Dictionary with results from all strategies for comparison
	"""
	strategies = ["equal", "priority_based", "high_links", "high_depth"]
	comparison_results = {
		'institution_name': institution_name,
		'institution_type': institution_type,
		'strategies': {}
	}
	
	for strategy in strategies:
		try:
			result = get_institution_links_with_strategy(
				institution_name, institution_type, max_links, 
				strategy, base_dir, search_params
			)
			comparison_results['strategies'][strategy] = result
		except Exception as e:
			comparison_results['strategies'][strategy] = {
				'error': str(e),
				'success': False
			}
	
	# Add summary comparison
	comparison_results['summary'] = _generate_strategy_comparison_summary(comparison_results['strategies'])
	
	return comparison_results


def _generate_strategy_comparison_summary(strategy_results: Dict) -> Dict:
	"""Generate summary comparison of different strategies."""
	summary = {
		'total_strategies': len(strategy_results),
		'successful_strategies': 0,
		'strategy_metrics': {}
	}
	
	for strategy, result in strategy_results.items():
		if result.get('success', False):
			summary['successful_strategies'] += 1
			
			links = result.get('links', [])
			summary['strategy_metrics'][strategy] = {
				'total_links': len(links),
				'high_priority_links': len([l for l in links if l.get('priority_tier') == 'high']),
				'medium_priority_links': len([l for l in links if l.get('priority_tier') == 'medium']),
				'low_priority_links': len([l for l in links if l.get('priority_tier') == 'low']),
				'avg_crawl_depth': sum(l.get('crawl_depth', 0) for l in links) / len(links) if links else 0,
				'avg_max_pages': sum(l.get('max_pages', 0) for l in links) / len(links) if links else 0,
				'total_potential_pages': sum(l.get('max_pages', 0) for l in links)
			}
	
	return summary
