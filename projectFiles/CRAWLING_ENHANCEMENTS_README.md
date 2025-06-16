# Enhanced Institution Crawling System

## Overview

The crawling system has been enhanced with priority-based configurations, smart keyword detection, and configurable benchmarking strategies. This allows for more intelligent resource allocation and better benchmarking of different crawling approaches.

## Key Features

### 1. Priority-Based Crawling
- **High Priority Sites**: Higher depth (3 levels) and more pages (25) for official domains
- **Medium Priority Sites**: Standard depth (2 levels) and pages (15) for relevant sites
- **Low Priority Sites**: Limited depth (1 level) and pages (8) for less relevant sites

### 2. Smart Keyword Detection
Enhanced keyword matching for different institution types:
- **Educational**: University-specific terms, academic indicators, .edu domains
- **Medical**: Healthcare terminology, medical specialties, hospital indicators
- **Financial**: Banking terms, financial services, regulatory keywords
- **Corporate**: Business terminology, company indicators, general domains

### 3. Configurable Strategies
Four different crawling strategies for benchmarking:
- **Equal Distribution**: Same depth and pages for all sites
- **Priority-Based**: Resource allocation based on site priority scores
- **High Links**: More pages for high-priority sites, standard depth
- **High Depth**: Deeper crawling for high-priority sites, standard pages

## Usage Examples

### Basic Enhanced Crawling
```python
from crawling_prep import InstitutionLinkManager, CrawlPriorityConfig, BenchmarkConfig

# Create manager with custom configurations
priority_config = CrawlPriorityConfig(
    high_priority_max_depth=4,
    high_priority_max_pages=30
)

benchmark_config = BenchmarkConfig(strategy="priority_based")

manager = InstitutionLinkManager(
    priority_config=priority_config,
    benchmark_config=benchmark_config
)

# Get crawling links with priority-based allocation
result = manager.get_crawling_links("Harvard University", "university")
```

### Strategy Comparison
```python
from crawling_prep import compare_crawling_strategies

# Compare all strategies for an institution
comparison = compare_crawling_strategies(
    "Mayo Clinic", 
    "medical",
    max_links=15
)

# View strategy metrics
for strategy, metrics in comparison['summary']['strategy_metrics'].items():
    print(f"{strategy}: {metrics['total_potential_pages']} total pages")
```

### Quick Strategy Selection
```python
from crawling_prep import get_institution_links_with_strategy

# Get links with specific strategy
equal_result = get_institution_links_with_strategy(
    "Goldman Sachs", "financial", strategy="equal"
)

priority_result = get_institution_links_with_strategy(
    "Goldman Sachs", "financial", strategy="priority_based"
)
```

## Configuration Classes

### CrawlPriorityConfig
```python
@dataclass
class CrawlPriorityConfig:
    high_priority_max_depth: int = 3        # Depth for high-priority sites
    high_priority_max_pages: int = 25       # Pages for high-priority sites
    medium_priority_max_depth: int = 2      # Depth for medium-priority sites
    medium_priority_max_pages: int = 15     # Pages for medium-priority sites
    low_priority_max_depth: int = 1         # Depth for low-priority sites
    low_priority_max_pages: int = 8         # Pages for low-priority sites
    priority_threshold_high: int = 100      # Score threshold for high priority
    priority_threshold_medium: int = 50     # Score threshold for medium priority
```

### BenchmarkConfig
```python
@dataclass
class BenchmarkConfig:
    strategy: str = "priority_based"        # Strategy type
    equal_depth: int = 2                    # Depth for equal strategy
    equal_max_pages: int = 15               # Pages for equal strategy
    high_links_multiplier: float = 1.5      # Link multiplier for high_links
    high_depth_multiplier: float = 1.5      # Depth multiplier for high_depth
```

## Priority Scoring

Sites are scored based on multiple factors:

### Domain Authority (+100 points)
- `.edu`, `.org`, `.gov` domains get highest priority

### Institution Type Matching (+50 points)
- URLs/titles matching institution type (university, hospital, bank)

### Official Page Indicators (+15-20 points)
- Homepage paths (`/`, `/home`, `/about`)
- Official titles ("official", "homepage")

### Penalty Factors (-20 points)
- Social media sites (Facebook, Twitter, LinkedIn)
- Wikipedia entries

## Smart Keyword Patterns

Each institution category has specialized keyword detection:

### Educational Institutions
- **Primary**: university, college, student, faculty, degree, campus
- **Secondary**: tuition, research, accreditation, ranking
- **Domains**: `.edu`, `university.`, `college.`

### Medical Institutions
- **Primary**: hospital, clinic, medical, doctor, patient, treatment
- **Secondary**: specialist, laboratory, accredited, certified
- **Domains**: `health.`, `medical.`, `hospital.`

### Financial Institutions
- **Primary**: bank, banking, loan, investment, branch
- **Secondary**: FDIC, regulation, compliance, corporate
- **Domains**: `bank.`, `financial.`

## Benchmarking Integration

The system supports four benchmarking strategies:

1. **Equal Distribution**: All sites get same resources
2. **Priority-Based**: Resources allocated by priority score
3. **High Links**: More pages for priority sites, same depth
4. **High Depth**: Deeper crawling for priority sites, same pages

These strategies can be compared to determine optimal resource allocation for different institution types and use cases.

## Output Structure

Enhanced crawling results include:

```python
{
    'institution_name': 'Harvard University',
    'institution_type': 'university',
    'search_successful': True,
    'links': [
        {
            'url': 'https://harvard.edu',
            'title': 'Harvard University',
            'priority': 150,
            'priority_tier': 'high',
            'crawl_depth': 3,
            'max_pages': 25,
            'smart_keywords_matched': ['university', 'harvard', 'education']
        }
    ],
    'priority_summary': {
        'high_priority_count': 5,
        'medium_priority_count': 3,
        'low_priority_count': 2,
        'total_potential_pages': 185
    }
}
```

## Integration with Pipeline

The enhanced crawling system integrates seamlessly with the existing pipeline. The pipeline can use the priority-based configurations to optimize resource usage and improve data quality while maintaining compatibility with existing benchmarking systems.
