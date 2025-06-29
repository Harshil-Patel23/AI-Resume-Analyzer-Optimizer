import streamlit as st
import os
import fitz  # PyMuPDF for PDF reading
from utils import (
    enhanced_pdf_extraction, 
    advanced_text_cleaning,
    extract_skills_by_category, 
    calculate_match_score,
    semantic_skill_matching,
    calculate_weighted_score,
    generate_optimization_suggestions,
    check_ats_compatibility,
    extract_experience_info
)
from skills_data import skills_data

# Set page configuration
st.set_page_config(
    page_title="AI Resume Analyzer & Optimizer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .score-card h3 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
    }
    
    .score-card p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    .skill-tag {
        display: inline-block;
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .skill-tag.matched {
        background: #e8f5e8;
        color: #2e7d32;
    }
    
    .skill-tag.missing {
        background: #ffebee;
        color: #c62828;
    }
    
    .semantic-match {
        background: #f3e5f5;
        border-left: 4px solid #9c27b0;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    
    .suggestion-card {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    
    .critical-suggestion {
        background: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    
    .ats-score {
        text-align: center;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: bold;
        font-size: 1.5rem;
    }
    
    .experience-badge {
        background: linear-gradient(135deg, #4caf50, #45a049);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        display: inline-block;
        margin: 0.5rem 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def display_semantic_matches(semantic_matches):
    """Display semantic similarity matches"""
    if semantic_matches:
        st.markdown("### 🧠 AI Semantic Matches")
        st.markdown("*Skills matched using AI understanding (not just exact words)*")
        
        for category, matches in semantic_matches.items():
            if matches:
                st.markdown(f"**{category.title()}:**")
                for match in matches:
                    similarity_percent = int(match['similarity'] * 100)
                    st.markdown(f"""
                    <div class="semantic-match">
                        "{match['jd_skill']}" ↔ "{match['resume_skill']}"
                        <br><strong>{similarity_percent}% similar</strong>
                    </div>
                    """, unsafe_allow_html=True)

def display_suggestions(suggestions):
    """Display optimization suggestions"""
    if suggestions:
        st.markdown("### 💡 Optimization Suggestions")
        
        for suggestion in suggestions:
            card_class = "critical-suggestion" if suggestion['type'] == 'critical' else "suggestion-card"
            icon = "🚨" if suggestion['type'] == 'critical' else "💡"
            
            st.markdown(f"""
            <div class="{card_class}">
                <strong>{icon} {suggestion['message']}</strong>
                <br>Action: {suggestion['action']}
            </div>
            """, unsafe_allow_html=True)

def display_ats_results(ats_results):
    """Display ATS compatibility results"""
    st.markdown("### 🤖 ATS Compatibility Check")
    
    # ATS Score
    ats_score = ats_results['ats_score']
    score_color = "#4caf50" if ats_score >= 80 else "#ff9800" if ats_score >= 60 else "#f44336"
    
    st.markdown(f"""
    <div class="ats-score" style="background-color: {score_color}; color: white;">
        <div>
            <h3 style="margin: 0;">ATS Score: {ats_score}%</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Issues and Recommendations
    if ats_results['issues']:
        st.markdown("**⚠️ Issues Found:**")
        for issue in ats_results['issues']:
            st.markdown(f"• {issue}")
    
    if ats_results['recommendations']:
        st.markdown("**✅ Recommendations:**")
        for rec in ats_results['recommendations']:
            st.markdown(f"• {rec}")

def main():
    # Main header
    st.markdown('<h1 class="main-header">🤖 AI-Powered Resume Analyzer & Optimizer</h1>', unsafe_allow_html=True)
    
    # Sidebar for settings
    with st.sidebar:
        st.markdown("## ⚙️ Analysis Settings")
        
        # Job title input for weighted scoring
        job_title = st.text_input(
            "Job Title (Optional)", 
            placeholder="e.g., Senior Data Scientist",
            help="Helps optimize scoring weights for specific roles"
        )
        
        # Semantic similarity threshold
        semantic_threshold = st.slider(
            "AI Similarity Threshold", 
            min_value=0.5, 
            max_value=0.9, 
            value=0.7, 
            step=0.05,
            help="How similar skills need to be for AI matching (higher = stricter)"
        )
        
        # Analysis options
        st.markdown("## 🔍 Analysis Options")
        enable_semantic = st.checkbox("Enable AI Semantic Matching", value=True)
        enable_weighted = st.checkbox("Enable Smart Scoring", value=True)
        enable_suggestions = st.checkbox("Enable Optimization Tips", value=True)
        enable_ats = st.checkbox("Enable ATS Check", value=True)
        
        st.markdown("## 📋 How to Use")
        st.markdown("""
        1. **Upload Resume**: PDF format preferred
        2. **Job Description**: Paste full job posting
        3. **Configure Settings**: Adjust options above
        4. **Analyze**: Get comprehensive insights
        """)
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Upload Your Resume")
        uploaded_file = st.file_uploader(
            "Choose a PDF file", 
            type=['pdf'],
            help="Upload your resume in PDF format (Max 10MB)"
        )
        
        st.subheader("📋 Job Description")
        job_description = st.text_area(
            "Paste the job description here:",
            height=200,
            placeholder="Enter the complete job description including requirements, responsibilities, and qualifications..."
        )
        
        # Submit button
        submit_button = st.button("🚀 ANALYZE RESUME", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("📊 Analysis Results")
        results_placeholder = st.empty()
    
    # Process when submit button is clicked
    if submit_button:
        if uploaded_file is not None and job_description.strip():
            with st.spinner("🔍 Analyzing your resume with AI..."):
                try:
                    # Create uploads directory if it doesn't exist
                    os.makedirs("uploads", exist_ok=True)
                    
                    # Save uploaded file
                    file_path = os.path.join("uploads", uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Extract text from PDF using enhanced method
                    resume_text = enhanced_pdf_extraction(file_path)
                    
                    # Advanced text cleaning
                    resume_text_cleaned = advanced_text_cleaning(resume_text)
                    jd_text_cleaned = advanced_text_cleaning(job_description)
                    
                    # Extract skills
                    resume_skills = extract_skills_by_category(resume_text_cleaned, skills_data)
                    jd_skills = extract_skills_by_category(jd_text_cleaned, skills_data)
                    
                    # Calculate basic match score
                    basic_score, details = calculate_match_score(resume_skills, jd_skills)
                    
                    # Initialize variables for optional features
                    semantic_matches = {}
                    weighted_score = basic_score
                    suggestions = []
                    ats_results = {}
                    experience_info = {}
                    
                    # Semantic matching (if enabled)
                    if enable_semantic and resume_skills and jd_skills:
                        semantic_matches = semantic_skill_matching(
                            resume_skills, jd_skills, threshold=semantic_threshold
                        )
                    
                    # Weighted scoring (if enabled)
                    if enable_weighted:
                        weighted_score = calculate_weighted_score(details, job_title)
                    
                    # Generate suggestions (if enabled)
                    if enable_suggestions:
                        suggestions = generate_optimization_suggestions(
                            details, weighted_score, resume_text
                        )
                    
                    # ATS compatibility check (if enabled)
                    if enable_ats:
                        ats_results = check_ats_compatibility(resume_text, file_path)
                    
                    # Extract experience information
                    experience_info = extract_experience_info(resume_text)
                    
                    # Display results in the right column
                    with results_placeholder.container():
                        # Display match scores
                        col_score1, col_score2 = st.columns(2)
                        
                        with col_score1:
                            st.markdown(f"""
                            <div class="score-card">
                                <div>
                                    <h3>{basic_score}%</h3>
                                    <p>Basic Score</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_score2:
                            if enable_weighted:
                                st.markdown(f"""
                                <div class="score-card">
                                    <div>
                                        <h3>{weighted_score}%</h3>
                                        <p>Smart Score</p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Experience information
                        if experience_info.get('total_years', 0) > 0:
                            st.markdown(f"""
                            <div class="experience-badge">
                                📅 Experience: {experience_info['total_years']} years
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # ATS Score (if enabled)
                        if enable_ats and ats_results:
                            display_ats_results(ats_results)
                        
                        # Semantic matches (if enabled and found)
                        if enable_semantic and semantic_matches:
                            display_semantic_matches(semantic_matches)
                        
                        # Display detailed analysis
                        st.markdown("### 📈 Skill Analysis")
                        
                        # Traditional skill matching
                        st.markdown("**⭐ Required Skills:**")
                        all_required_skills = ""
                        for category, data in details.items():
                            if data['required']:
                                all_required_skills += "".join([
                                    f'<span class="skill-tag">{skill}</span>' 
                                    for skill in data['required']
                                ])
                        st.markdown(all_required_skills, unsafe_allow_html=True)
                        
                        st.markdown("**✅ Matching Skills:**")
                        all_matching_skills = ""
                        for category, data in details.items():
                            if data['matched']:
                                all_matching_skills += "".join([
                                    f'<span class="skill-tag matched">{skill}</span>' 
                                    for skill in data['matched']
                                ])
                        st.markdown(all_matching_skills, unsafe_allow_html=True)
                        
                        st.markdown("**❌ Missing Skills:**")
                        all_missing_skills = ""
                        for category, data in details.items():
                            if data['missing']:
                                all_missing_skills += "".join([
                                    f'<span class="skill-tag missing">{skill}</span>' 
                                    for skill in data['missing']
                                ])
                        st.markdown(all_missing_skills, unsafe_allow_html=True)
                        
                        # Optimization suggestions (if enabled)
                        if enable_suggestions and suggestions:
                            display_suggestions(suggestions)
                    
                    # Clean up uploaded file
                    os.remove(file_path)
                    
                    # Success message with summary
                    improvement_percentage = weighted_score - basic_score if enable_weighted else 0
                    semantic_matches_count = sum(len(matches) for matches in semantic_matches.values()) if semantic_matches else 0
                    
                    success_message = f"✅ Analysis completed! "
                    if semantic_matches_count > 0:
                        success_message += f"Found {semantic_matches_count} AI matches. "
                    if improvement_percentage > 0:
                        success_message += f"Smart scoring improved by {improvement_percentage:.1f}%"
                    
                    st.success(success_message)
                
                except Exception as e:
                    st.error(f"❌ Error processing your resume: {str(e)}")
                    st.error("Please make sure your PDF is valid and try again.")
                    # Optional: Show more detailed error for debugging
                    if st.checkbox("Show detailed error (for debugging)"):
                        st.exception(e)
        
        elif uploaded_file is None:
            st.warning("⚠️ Please upload a PDF file.")
        elif not job_description.strip():
            st.warning("⚠️ Please enter a job description.")
    
    # Footer with features
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 🧠 AI Features")
        st.markdown("• Semantic matching\n• Smart scoring\n• Experience extraction")
    
    with col2:
        st.markdown("### 📊 Analysis")
        st.markdown("• Skill categorization\n• Gap identification\n• Match percentage")
    
    with col3:
        st.markdown("### 🤖 ATS Check")
        st.markdown("• Format validation\n• Content analysis\n• Compatibility score")
    
    with col4:
        st.markdown("### 💡 Optimization")
        st.markdown("• Actionable tips\n• Missing skills\n• Content suggestions")

if __name__ == "__main__":
    main()