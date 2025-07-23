import streamlit as st
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import google.generativeai as genai

# Load API Key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY not found in .env file.")
    st.stop()

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Prompt Template
def generate_prompt(resume_text, jd_text):
    return f"""
You are an exceptionally precise and objective Applicant Tracking System (ATS) expert, highly specialized in evaluating resumes for technical roles like AI/ML Engineer, Data Scientist, and Big Data Engineer. Your goal is to provide consistent and accurate evaluations.

Your task is to:
1.  **Analyze the resume thoroughly.**
2.  **Compare the resume against the provided job description.**
3.  **Calculate a precise percentage match.** This match score should be based on the explicit alignment of skills, experience, and keywords found in the resume with those explicitly mentioned in the job description. Give higher weight to direct matches of technical skills and required experience years (if specified). For example, if 10 core requirements are listed in the JD and 7 are clearly present in the resume, the base score should reflect this proportion.
4.  **Identify and list all critical keywords from the job description that are explicitly missing** from the resume. If no critical keywords are missing, state 'None'.
5.  **Summarize the company's expectations from the candidate** based *only* on the job description. Provide this as a concise list of 3-5 bullet points.
6.  **Provide specific, actionable, and tailored suggestions** for improving the resume to maximize its alignment with the job description. These suggestions should be concise, 3-5 bullet points, and directly actionable.

Respond ONLY in this strict format, without any introductory or concluding remarks, just the structured text below:

Match Score: <percentage>%
Missing Keywords: <comma-separated list of critical missing keywords, or 'None'>
Company Expectations:
- <Point 1: Key expectation derived directly from JD>
- <Point 2: Key expectation derived directly from JD>
- <Point 3: Key expectation derived directly from JD>
Resume Improvement Suggestions:
- <Suggestion 1: Actionable step to align resume with JD, e.g., "Add 'PyTorch' if experienced">
- <Suggestion 2: Actionable step to align resume with JD, e.g., "Quantify project 'X' impact with metrics">
- <Suggestion 3: Actionable step to align resume with JD, e.g., "Include experience with 'Snowflake'">

Resume:
{resume_text}

Job Description:
{jd_text}
"""

# Extract Text from PDF 
def extract_text_from_pdf(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text
    return full_text

# Gemini API Call
def get_gemini_ats_evaluation(resume_text, jd_text):
    try:
        prompt = generate_prompt(resume_text, jd_text)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini Error: {str(e)}"

# Streamlit UI
st.set_page_config(
    page_title="AI Resume ATS Evaluator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.header("About This App")
    st.markdown("""
    This **Smart ATS Resume Evaluator** leverages **Google's Gemini AI** to help you
    optimize your resume for specific job descriptions.
    
    Upload your resume (PDF) and paste the job description, then let the AI analyze:
    - Your match score.
    - Missing keywords.
    - Company expectations.
    - Tailored suggestions for improvement.
    """)
    st.markdown("---")
    st.markdown("[GitHub Repository](https://github.com/Kalyanchittaluri/ATS_System)") 

# Main Content Area
st.title("Smart ATS Resume Evaluator")
st.markdown("### Land your dream job by optimizing your resume for Applicant Tracking Systems")

st.info("Instructions: Upload your resume (PDF) and paste the job description below. Click 'Analyze' to get instant feedback and improvement suggestions.")

st.divider()

# Input Section
input_col, _ = st.columns([1.5, 1])
with input_col:
    st.subheader("Your Application Materials")

    uploaded_resume = st.file_uploader("1. Upload Your Resume (PDF)", type="pdf", help="Please upload your most recent resume.")
    
    st.markdown("---") 
    
    job_description = st.text_area(
        "2. Paste the Job Description Here", 
        height=350, 
        placeholder="Paste the full job description (JD) including requirements, responsibilities, and qualifications here...",
        help="Copy and paste the entire job description from the job posting."
    )

st.divider()

# Analyze Button
if st.button("Analyze My Resume", use_container_width=True):
    if not uploaded_resume or not job_description.strip():
        st.error("Please upload your resume AND paste the job description to proceed.")
    else:
        with st.spinner("Analyzing your resume... This might take a few moments."):
            resume_text = extract_text_from_pdf(uploaded_resume)
            result = get_gemini_ats_evaluation(resume_text, job_description)

            if result.startswith("Gemini Error"):
                st.exception(result)
            else:
                lines = result.splitlines()
                match_score = "N/A"
                missing_keywords = "N/A"
                company_expectations = "N/A"
                improvement_suggestions = "N/A"

                def get_section_content(title, lines, start_idx, next_title_keys):
                    # Find the content related to the current title
                    content_start_line = lines[start_idx]
                    colon_split = content_start_line.split(":", 1)
                    
                    # If there's content directly after the colon on the title line
                    inline_content = colon_split[1].strip() if len(colon_split) > 1 else ""
                    
                    content_lines = []
                    if inline_content and not inline_content.startswith('-'): # Only add if it's not the start of a bullet list
                        content_lines.append(inline_content)

                    end_idx = len(lines)
                    for key in next_title_keys:
                        if key in section_starts:
                            next_idx = section_starts[key]
                            if next_idx > start_idx: # Ensure it's a subsequent section
                                end_idx = next_idx
                                break
                    
                    # Collect all lines from after the title line up to the next section
                    for i in range(start_idx + 1, end_idx):
                        current_line = lines[i].strip()
                        if current_line: # Keep non-empty lines
                            content_lines.append(current_line)
                    
                    return "\n".join(content_lines).strip()


                section_starts = {}
                for i, line in enumerate(lines):
                    if line.startswith("Match Score:"):
                        section_starts["Match Score"] = i
                    elif line.startswith("Missing Keywords:"):
                        section_starts["Missing Keywords"] = i
                    elif line.startswith("Company Expectations:"):
                        section_starts["Company Expectations"] = i
                    elif line.startswith("Resume Improvement Suggestions:"):
                        section_starts["Resume Improvement Suggestions"] = i

                # Extract content based on detected sections
                if "Match Score" in section_starts:
                    match_score = get_section_content("Match Score", lines, section_starts["Match Score"], ["Missing Keywords", "Company Expectations", "Resume Improvement Suggestions"])

                if "Missing Keywords" in section_starts:
                    missing_keywords = get_section_content("Missing Keywords", lines, section_starts["Missing Keywords"], ["Company Expectations", "Resume Improvement Suggestions"])

                if "Company Expectations" in section_starts:
                    company_expectations = get_section_content("Company Expectations", lines, section_starts["Company Expectations"], ["Resume Improvement Suggestions"])

                if "Resume Improvement Suggestions" in section_starts:
                    improvement_suggestions = get_section_content("Resume Improvement Suggestions", lines, section_starts["Resume Improvement Suggestions"], [])

                # Display Results
                st.divider()
                st.subheader("1. Match Score and Missing Keywords")
                st.markdown(f"**Match Score:** {match_score}")
                st.markdown(f"**Missing Keywords:** {missing_keywords if missing_keywords != 'None' else 'None identified'}")

                st.markdown("---")

                st.subheader("2. Company Expectations")
                if company_expectations:
                    # Split by newlines and render each line as a markdown bullet
                    for point in company_expectations.split('\n'):
                        st.markdown(point)
                else:
                    st.markdown("No expectations extracted.")

                st.markdown("---")

                st.subheader("3. Resume Improvement Suggestions")
                if improvement_suggestions:
                    # Split by newlines and render each line as a markdown bullet
                    for suggestion in improvement_suggestions.split('\n'):
                        st.markdown(suggestion)
                else:
                    st.markdown("No suggestions provided.")