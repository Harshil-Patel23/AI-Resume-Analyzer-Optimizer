import re
import fitz
import pdfplumber
import PyPDF2
import nltk
import spacy
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import dateparser
from datetime import datetime

#================================================================================= step 0 load the models

# Load pre-trained sentence transformer model for semantic similarity calculations
# This is expensive to load, so we do it once at module level
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

# Load spaCy English language model for NLP tasks (uncomment if needed)
# nltk.download('stopwords')
nlp = spacy.load("en_core_web_sm")

#================================================================================= step 1 extract text from the resume pdf

def enhanced_pdf_extraction(pdf_path):
    """
    Extract text from PDF using multiple methods for better accuracy.
    Uses both pdfplumber (good for tables/layouts) and PyMuPDF (general purpose).
    Returns the longest extracted text as it's usually the most complete.
    """
    text_methods = []
    
    # Method 1: pdfplumber - excellent for preserving table structure and complex layouts
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text1 = ""
            for page in pdf.pages:
                text1 += page.extract_text() or ""
        text_methods.append(text1)
    except:
        pass
    
    # Method 2: PyMuPDF (fitz) - good general-purpose PDF text extraction
    try:
        doc = fitz.open(pdf_path)
        text2 = ""
        for page_num in range(len(doc)):
            text2 += doc.load_page(page_num).get_text()
        text_methods.append(text2)
    except:
        pass
    
    # Return the longest extracted text (usually most complete)
    return max(text_methods, key=len) if text_methods else ""

#================================================================================= step 2 clean the text

def advanced_text_cleaning(text):
    """
    Advanced text cleaning that preserves important punctuation for technical skills.
    Removes personal information and normalizes whitespace.
    """
    # Convert to lowercase first
    text = text.lower()
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Remove email addresses and phone numbers for privacy
    text = re.sub(r'\S+@\S+', '[EMAIL]', text)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)

    # Preserve important punctuation for technical skills like C++, .NET, C#
    # Keep: word characters, spaces, +, #, ., -
    text = re.sub(r'[^\w\s\+\#\.\-]', ' ', text)

    return text

#================================================================================= step 3 define the skill dataset
# defined in the skills_data.py file

#================================================================================= step 4 extract skills by category

def extract_skills_by_category(text, skills_data):
    """
    Extract skills from text by matching against predefined skill categories.
    Uses word boundary matching to avoid partial matches.
    
    Args:
        text: The text to search in
        skills_data: Dictionary with categories as keys and skill lists as values
    
    Returns:
        Dictionary with categories and found skills
    """
    matched_skills = {}
    for category, skills in skills_data.items():
        found = []
        for skill in skills:
            skill_lower = skill.lower()
            # Use word boundaries to match complete words only
            if re.search(r'\b' + re.escape(skill_lower) + r'\b', text):
                found.append(skill)
        if found:
            matched_skills[category] = found
    return matched_skills

#================================================================================= step 5 calculate match score

def calculate_match_score(resume_skills, jd_skills):
    """
    Calculate percentage match between resume skills and job description skills.
    Provides detailed breakdown by category.
    
    Args:
        resume_skills: Skills found in resume (by category)
        jd_skills: Skills required in job description (by category)
    
    Returns:
        Tuple of (match_percentage, detailed_results)
    """
    total_required = 0
    total_matched = 0
    detailed_result = {}

    for category in jd_skills:
        # Convert to sets for efficient intersection operations
        jd_category_skills = set(jd_skills[category])
        resume_category_skills = set(resume_skills.get(category, []))
        matched = jd_category_skills & resume_category_skills  # Set intersection
        total_required += len(jd_category_skills)
        total_matched += len(matched)
        detailed_result[category] = {
            "required": list(jd_category_skills),
            "matched": list(matched),
            "missing": list(jd_category_skills - resume_category_skills)  # Set difference
        }

    # Calculate percentage match, avoiding division by zero
    match_score = round((total_matched / total_required) * 100, 2) if total_required > 0 else 0
    return match_score, detailed_result




#================================================================================= step 6 calcuate semantic match

def semantic_skill_matching(resume_skills, jd_skills, threshold=0.7):
    """
    Find semantically similar skills between resume and job description.
    Uses sentence transformers to calculate semantic similarity.
    
    Args:
        resume_skills: Skills from resume (by category)
        jd_skills: Skills from job description (by category)
        threshold: Minimum similarity score (0-1) to consider a match
    
    Returns:
        Dictionary of semantic matches with similarity scores
    """
    semantic_matches = {}

    for category in jd_skills:
        jd_category_skills = jd_skills[category]
        resume_category_skills = resume_skills.get(category, [])

        semantic_matched = []

        for jd_skill in jd_category_skills:
            best_match = None
            best_score = 0

            for resume_skill in resume_category_skills:
                # Calculate semantic similarity using sentence transformers
                embeddings = semantic_model.encode([jd_skill, resume_skill])
                similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

                if similarity > threshold and similarity > best_score:
                    best_match = resume_skill
                    best_score = similarity
            
            if best_match:
                semantic_matched.append({
                    'jd_skill': jd_skill,
                    'resume_skill': best_match,
                    'similarity': round(best_score, 2)
                })
            
        if semantic_matched:
            semantic_matches[category] = semantic_matched
    
    return semantic_matches

#================================================================================= step 7 calculate weighted score based on the job title

def get_skill_weights(job_title=""):
    """
    Get category weights for scoring based on job title.
    Different job types prioritize different skill categories.
    
    Args:
        job_title: Job title to customize weights
    
    Returns:
        Dictionary of category weights (sums to 1.0)
    """
    # Default weights for general software development roles
    base_weights = {
        'programming': 0.35,    # Core programming languages
        'technical': 0.30,      # Technical concepts and methodologies
        'frameworks': 0.20,     # Libraries and frameworks
        'soft_skills': 0.10,    # Communication, leadership, etc.
        'tools': 0.05           # Development tools and platforms
    }
    
    # Adjust weights based on job title keywords
    job_title_lower = job_title.lower()
    
    # Senior/Lead roles emphasize soft skills more
    if 'senior' in job_title_lower or 'lead' in job_title_lower:
        base_weights['soft_skills'] = 0.20
        base_weights['technical'] = 0.25
    
    # Data roles emphasize technical skills and tools
    if 'data' in job_title_lower:
        base_weights['technical'] = 0.40
        base_weights['tools'] = 0.15
    
    return base_weights

def calculate_weighted_score(detailed_result, job_title=""):
    """
    Calculate weighted match score based on job-specific category importance.
    
    Args:
        detailed_result: Detailed matching results from calculate_match_score
        job_title: Job title for weight customization
    
    Returns:
        Weighted percentage score
    """
    weights = get_skill_weights(job_title)
    
    total_weighted_score = 0
    total_weight = 0
    
    for category, results in detailed_result.items():
        if category in weights:
            required_count = len(results['required'])
            matched_count = len(results['matched'])
            
            if required_count > 0:
                category_score = matched_count / required_count
                weighted_contribution = category_score * weights[category]
                total_weighted_score += weighted_contribution
                total_weight += weights[category]
    
    # Calculate final weighted score
    final_score = (total_weighted_score / total_weight * 100) if total_weight > 0 else 0
    return round(final_score, 2)

#================================================================================= step 8 generate suggestions for resume improvement

def generate_optimization_suggestions(detailed_result, match_score, resume_text):
    """
    Generate actionable suggestions to improve resume based on analysis results.
    
    Args:
        detailed_result: Detailed matching results
        match_score: Overall match percentage
        resume_text: Raw resume text for content analysis
    
    Returns:
        List of suggestion dictionaries with type, message, and action
    """
    suggestions = []
    priority_suggestions = []
    
    # Overall score suggestions - prioritize critical issues
    # if match_score < 70:
    #     priority_suggestions.append({
    #         'type': 'critical',
    #         'message': 'Your resume has low relevance to this job. Consider significant revisions.',
    #         'action': 'Review job description and add relevant skills/experience'
    #     })
    if match_score < 70:
        suggestions.append({
            'type': 'important',
            'message': 'Your resume could be more competitive.',
            'action': 'Add missing key skills and relevant experience'
        })
    
    # Skill-specific suggestions
    for category, results in detailed_result.items():
        missing_skills = results['missing']
        if len(missing_skills) > 0:
            # Prioritize most common/important missing skills
            top_missing = missing_skills[:3]
            suggestions.append({
                'type': 'skill_gap',
                'category': category,
                'message': f'Missing important {category} skills',
                'action': f'Consider adding: {", ".join(top_missing)}',
                'skills': top_missing
            })
    
    # Content suggestions
    if len(resume_text.split()) < 200:
        suggestions.append({
            'type': 'content',
            'message': 'Resume appears too brief',
            'action': 'Add more detailed descriptions of your experience and achievements'
        })
    
    return priority_suggestions + suggestions

#================================================================================= step 9 check ATS compatibility


def check_ats_compatibility(resume_text, pdf_path):
    issues = []
    recommendations = []
    
    # Check for contact information
    if not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text):
        issues.append("Missing email address")
        recommendations.append("Add a professional email address")
    
    # Check for phone number
    if not re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', resume_text):
        issues.append("Missing phone number")
        recommendations.append("Add your phone number")
    
    # Check for standard sections
    standard_sections = ['experience', 'education', 'skills']
    for section in standard_sections:
        if not re.search(f'\\b{section}\\b', resume_text.lower()):
            issues.append(f"Missing {section} section")
            recommendations.append(f"Add a clear {section} section")
    
    # Check for excessive special characters
    special_char_ratio = len(re.findall(r'[^\w\s]', resume_text)) / len(resume_text)
    if special_char_ratio > 0.1:
        issues.append("Too many special characters")
        recommendations.append("Simplify formatting and reduce special characters")
    
    # Check word count
    word_count = len(resume_text.split())
    if word_count < 150:
        issues.append("Resume too short")
        recommendations.append("Add more detailed content (aim for 200-400 words)")
    elif word_count > 800:
        issues.append("Resume too long")
        recommendations.append("Condense content to essential information")
    
    ats_score = max(0, 100 - len(issues) * 15)
    
    return {
        'ats_score': ats_score,
        'issues': issues,
        'recommendations': recommendations
    }

#================================================================================= step 10 extract the experience (optional)

def extract_experience_info(resume_text):
    experience_data = {
        'total_years': 0,
        'experience_entries': [],
        'current_role': None
    }
    
    # Pattern for experience mentions
    experience_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
        r'(\d+)\+?\s*yrs?\s*(?:of\s*)?(?:experience|exp)',
        r'(\d{4})\s*[-–]\s*(?:present|current|\d{4})',
        r'(\d{1,2}/\d{4})\s*[-–]\s*(?:present|current|\d{1,2}/\d{4})'
    ]
    
    years_mentioned = []
    for pattern in experience_patterns:
        matches = re.findall(pattern, resume_text.lower())
        years_mentioned.extend(matches)
    
    if years_mentioned:
        # Extract numeric years
        numeric_years = []
        for year in years_mentioned:
            try:
                numeric_years.append(int(year))
            except:
                continue
        
        if numeric_years:
            experience_data['total_years'] = max(numeric_years)
    
    return experience_data