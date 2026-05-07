import streamlit as st
from google import genai
import PyPDF2
import tempfile
import os

#Gemini Client
client=genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)

# page Config
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📝",
    layout="wide"
)

#title
st.title("🚀 AI Resume Analyzer")

# Subtitle
st.write("Upload your resume and compare it with a job description using Gemini AI.")


#Session State

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result=""

if "resume_text" not in st.session_state:
        st.session_state.resume_text=""

if "chat_history" not in st.session_state:
    st.session_state.chat_history=[]

if "improved_resume" not in st.session_state:
    st.session_state.improved_resume = ""    

# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    text=""

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(pdf_file.read())
        temp_path=temp_file.name

    with open(temp_path, "rb") as file:
        reader=PyPDF2.PdfReader(file)
        for page in reader.pages:
            text+=page.extract_text()
    os.remove(temp_path)
    return text            


#Analyze Resume
def analyze_resume(resume_text,job_title,job_description):
    prompt=f"""
    You are an expert resume analyzer.
    Analyze this resume for the given job role.

    JOB TITLE:
    {job_title}

    JOB DESCRIPTION:
    {job_description}    

    RESUME:
    {resume_text}


    Give response in this format:

    ATS Score: number only

    Missing Skills:
    - skill 1
    - skill 2

    Strengths:
    - point 1
    - point 2

    Weaknesses:
    - point 1
    - point 2

    Improvement Suggestions:
    - suggestion 1
    - suggestion 2
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"Error: {e}"


# Improve Resume Function
def improve_resume(resume_text, job_title, job_description):

    prompt = f"""
    You are an expert resume writer.
    Improve this resume for the given job role.
    
    JOB TITLE:
    {job_title}

    JOB DESCRIPTION:
    {job_description}

    ORIGINAL RESUME:
    {resume_text}

    Create:
    1. Professional Summary
    2. Improved Skills Section
    3. Better Experience Descriptions
    4. ATS Optimized Resume

    Keep it professional and ATS friendly.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        return response.text

    except Exception as e:
        return f"Error: {e}"

# Extract ATS score from Gemini response
def extract_ats_score(text):
    lines = text.split("\n")
    for line in lines:
        if "ATS Score" in line:
            numbers = ''.join(filter(str.isdigit, line))
            if numbers:
                return int(numbers)

    return 0
#create two columns
col1,col2=st.columns(2)

#left side->Resume Upload
with col1:
    st.header("📄 Upload Resume")
    uploaded_file=st.file_uploader(
        "Uplaod PDF Resume",
        type="pdf"
    )
    if uploaded_file:
        st.success("✅ Resume Uploaded Successfully")
        resume_text=extract_text_from_pdf(uploaded_file)
        st.session_state.resume_text=resume_text
        st.subheader("📑 Extracted Resume Text")

        st.text_area(
            "Resume Content",
            resume_text,
            height=300

        )
#Right side-> Job Details
with col2:
    st.header("💼 Job Details")
    job_title=st.text_input(
        "Job Title",
        value=st.session_state.get("job_title", "")

    )
    job_description=st.text_area(
        "JOb Description",
        height=250,
        value=st.session_state.get("job_description", "")

    )
    st.session_state.job_title=job_title
    st.session_state.job_description=job_description

# Analyze Button
if st.button("🔍 Analyze Resume"):
    if uploaded_file and job_description and job_title:
        with st.spinner("Analyzing Resume"):
            result=analyze_resume(
                resume_text,
                job_title,
                job_description
            )   

            st.session_state.analysis_result=result
    else:
        st.warning("Please upload resume and fill all fields")        


#Show Analysis Result
if st.session_state.analysis_result:
    st.subheader("📊 Analysis Result")
    ats_score=extract_ats_score(
        st.session_state.analysis_result
    )
    st.subheader("🎯 ATS Match Score")
    st.progress(ats_score)
    st.success(f"{ats_score}% Match")
    st.write(st.session_state.analysis_result)

    # Improve Resume Button
    if st.button("✨ Improve Resume"):
        with st.spinner("Improving Resume..."):
            improved = improve_resume(
                st.session_state.resume_text,
                st.session_state.job_title,
                st.session_state.job_description
            )

            st.session_state.improved_resume = improved

# Show Improved Resume
if st.session_state.improved_resume:

    st.subheader("🚀 ATS Optimized Resume")

    st.write(st.session_state.improved_resume)
    st.download_button(
        label="📥 Download Improved Resume",
        data=st.session_state.improved_resume,
        file_name="improved_resume.txt",
        mime="text/plain"
    )    

#Chat Section
st.divider() 
st.header("💬 Ask Questions About Resume")  
question=st.text_input(
    'Ask something about your resume',
    key="question_input"
) 

if st.button('Ask AI'):
    if question and st.session_state.analysis_result:
        prompt=f"""
        Resume:
        {st.session_state.resume_text}

        Analysis:
        {st.session_state.analysis_result}
        User Question:
        {question}
        """

        try:
            response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
            )
            answer= response.text

        except Exception as e:
            answer= f"Error: {e}"
        
        #save chat history
        st.session_state.chat_history.append({
            "question": question,
            "answer":answer
            
        })

        # refresh app
        st.rerun()

    else:
        st.warning("Please analyze resume first.")

#show Chat History
for chat in st.session_state.chat_history:
    st.subheader("🧑 You")
    st.write(chat["question"])

    st.subheader("🤖 AI")
    st.write(chat["answer"])

    st.divider()
