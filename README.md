# AI-Powered Resume Analyzer & Optimizer

An intelligent tool that analyzes your resume against job descriptions to help you optimize your application and increase your chances of getting hired.

## 🚀 Live Demo

👉 [Try the Live App](https://ai-resume-analyzer-optimizer.streamlit.app/)

## 🚀 Features

- **Resume Analysis**: Upload your resume in PDF format for instant analysis
- **Job Description Matching**: Compare your resume against any job description
- **Skill Gap Analysis**: Identify missing skills required for the position
- **Match Score**: Get a percentage score of how well your resume matches the job requirements
- **Detailed Breakdown**: View matching and missing skills by category
- **AI Semantic Matching**: Uses advanced AI to find related skills, not just exact keywords
- **ATS Compatibility Check**: Analyze your resume for Applicant Tracking System friendliness
- **Optimization Suggestions**: Get actionable tips to improve your resume
- **Modern UI**: Clean and intuitive user interface built with Streamlit and Flask

## 🛠️ Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/AI-Powered-Resume-Analyzer-Optimizer.git
    cd AI-Powered-Resume-Analyzer-Optimizer
    ```

2. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

## 💻 Usage

### Streamlit App (Recommended)

1. Run the Streamlit app:

    ```sh
    streamlit run streamlitApp.py
    ```

2. Open your web browser and navigate to the provided local URL (typically http://localhost:8501)

3. Upload your resume in PDF format

4. Paste the job description you want to match against

5. Click "ANALYZE RESUME" to get your results

### Flask Web App

1. Run the Flask app:

    ```sh
    python app.py
    ```

2. Open your browser and go to http://localhost:5000

## 📊 Analysis Results

The tool provides:

- Overall match score (basic and smart/weighted)
- Required skills for the position
- Skills you already have
- Missing skills you should consider adding
- AI semantic skill matches
- ATS compatibility score and recommendations
- Detailed breakdown by skill categories
- Actionable optimization suggestions

## 🛠️ Technical Stack

- Python
- Streamlit
- Flask
- PyMuPDF (for PDF processing)
- pdfplumber
- scikit-learn
- sentence-transformers
- spaCy
- Tailwind CSS (for Flask UI)
- Custom skill matching algorithms

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⭐ Support

If you find this tool helpful, please give it a star on GitHub!