from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
from werkzeug.utils import secure_filename
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

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/analyze', methods=['POST'])
def analyze_resume():
    try:
        # Get form data
        job_description = request.form.get('job_description', '').strip()
        job_title = request.form.get('job_title', '')
        semantic_threshold = float(request.form.get('semantic_threshold', 0.7))
        
        
        # Get analysis options
        enable_semantic = request.form.get('enable_semantic') == 'on'
        enable_weighted = request.form.get('enable_weighted') == 'on'
        enable_suggestions = request.form.get('enable_suggestions') == 'on'
        enable_ats = request.form.get('enable_ats') == 'on'
        
        # Check if file was uploaded
        if 'resume_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('index'))
        
        file = request.files['resume_file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        if not job_description:
            flash('Please enter a job description', 'error')
            return redirect(url_for('index'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
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
            
            # Clean up uploaded file
            os.remove(file_path)
            
            # Prepare results for template
            results = {
                'basic_score': basic_score,
                'weighted_score': weighted_score if enable_weighted else None,
                'details': details,
                'semantic_matches': semantic_matches if enable_semantic else {},
                'suggestions': suggestions if enable_suggestions else [],
                'ats_results': ats_results if enable_ats else {},
                'experience_info': experience_info,
                'job_title': job_title,
                'semantic_threshold': semantic_threshold,
                'options': {
                    'semantic': enable_semantic,
                    'weighted': enable_weighted,
                    'suggestions': enable_suggestions,
                    'ats': enable_ats
                }
            }
            
            return render_template('results.html', results=results)
        
        else:
            flash('Invalid file format. Please upload a PDF file.', 'error')
            return redirect(url_for('index'))
    
    except Exception as e:
        flash(f'Error processing your resume: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Please upload a file smaller than 10MB.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)