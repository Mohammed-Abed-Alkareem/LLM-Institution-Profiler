# Institution Profiler Quality Score System

## Overview

The Institution Profiler uses a sophisticated quality scoring system to evaluate the completeness and richness of extracted institutional data. The system is designed to provide meaningful quality assessments that account for different types of institutions and their relevant data fields.

## How Quality Scoring Works

### 1. Field Categories and Weights

The quality score system categorizes all extracted fields into weighted categories:

#### Critical Fields (40% of total score)
Essential identification information that every institution should have:
- `name`, `official_name`, `type`, `website`, `description`
- `location_city`, `location_country`, `entity_type`

These fields carry the highest weight because they represent fundamental institutional identity.

#### Important Fields (25% of total score)
Key operational details that provide substantial information:
- `founded`, `address`, `state`, `postal_code`, `phone`, `email`
- `industry_sector`, `size`, `number_of_employees`, `headquarters_location`

#### Valuable Fields (20% of total score)
Detailed organizational information:
- `leadership`, `ceo`, `president`, `chairman`, `key_people`
- `annual_revenue`, `legal_status`, `fields_of_focus`
- `services_offered`, `products`, `operating_countries`

#### Specialized Fields (10% of total score)
Institution-type specific details:
- **Universities**: `student_population`, `faculty_count`, `programs_offered`, `research_areas`
- **Hospitals**: `medical_specialties`, `patient_capacity`, `bed_count`
- **Companies**: Domain-specific business information

#### Enhanced Fields (5% of total score)
Rich content and relationships:
- `notable_achievements`, `rankings`, `awards`, `certifications`
- `affiliations`, `partnerships`, `publications`, `patents`
- `financial_data`, `endowment`, `budget`, `campus_size`

### 2. Institution-Type Awareness

The system includes logic to handle institution-specific fields intelligently:

#### General Fields
- Apply to ALL institution types
- Always count toward quality score
- Include basic identification, contact, and operational information

#### Institution-Specific Fields
- Only count for relevant institution types
- University fields (like `student_population`) don't penalize hospitals
- Hospital fields (like `bed_count`) don't penalize universities
- Business fields (like `stock_symbol`) don't penalize non-profits

#### Unknown Institution Types
- Score calculated using only general fields
- Institution-specific fields are ignored in scoring
- Prevents unfair penalization when institution type is unclear

### 3. Bonus Scoring System

Additional points (up to 25 total) are awarded for content richness:

#### Visual Content Bonus (up to 8 points)
- Institution logos found: +3 points
- General images found: +2 points
- Facility/campus images: +2 points
- Campus-specific images: +1 point

#### Content Richness Bonus (up to 7 points)
- Social media links: +2 points
- Documents found: +2 points
- Multiple crawling sources (>3): +3 points

#### Data Source Quality Bonus (up to 10 points)
- High crawling success rate (≥80%): +3 points
- Substantial content size (>1MB): +2 points
- Fresh data (low cache hit rate): +2 points

#### Processing Success Bonus (up to 5 points)
- All pipeline phases successful: +3 points
- Two phases successful: +2 points
- Multi-source verification: +2 points

### 4. Quality Rating Scale

Final scores are translated to descriptive ratings:

- **90-100**: Exceptional - Comprehensive, high-quality data
- **80-89**: Excellent - Very complete with rich details
- **70-79**: Very Good - Good coverage with some gaps
- **60-69**: Good - Adequate information for most uses
- **50-59**: Fair - Basic information present
- **35-49**: Poor - Significant gaps in critical data
- **20-34**: Very Poor - Minimal information available
- **0-19**: Minimal - Severely limited data

### 5. New University-Specific Fields

Enhanced fields for educational institutions:

#### Academic Structure
- `undergraduate_programs`, `graduate_programs`, `doctoral_programs`
- `professional_programs`, `online_programs`, `continuing_education`
- `course_catalog`, `academic_calendar`, `semester_system`

#### Faculty and Staff
- `professors`, `notable_faculty`, `academic_staff`, `administrative_staff`
- `student_faculty_ratio`

#### Student Life
- `campus_housing`, `dormitories`, `student_organizations`
- `fraternities_sororities`, `athletics_programs`

#### Facilities
- `libraries`, `laboratory_facilities`, `sports_facilities`
- `research_centers`, `institutes`

#### Financial and Performance
- `tuition_costs`, `scholarship_programs`, `graduation_rate`
- `academic_rankings`, `distinguished_alumni`

### 6. Implementation Benefits

#### Fair Comparison
- Institutions are scored against relevant benchmarks
- University quality isn't penalized for lacking hospital-specific data
- Companies aren't penalized for lacking academic programs

#### Information Gain Focus
- Scores reflect actual useful information extracted
- Bonus points reward comprehensive data collection
- Multiple validation sources increase confidence

#### Transparent Scoring
- Detailed breakdown shows which categories contribute to score
- Category-specific completion rates provided
- Source quality metrics included in assessment

## Usage in Application

The quality score is calculated in `quality_score_calculator.py` and integrates with:

1. **Web Interface**: Displays score and rating in results
2. **Benchmarking**: Tracks quality metrics across institutions
3. **Pipeline Validation**: Identifies extraction success/failure
4. **User Feedback**: Provides transparency about data completeness

## Future Enhancements

- Dynamic field weighting based on institution type detection
- Machine learning-based relevance scoring
- User feedback integration for field importance
- Temporal scoring for data freshness tracking
