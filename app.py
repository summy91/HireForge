from flask import Flask, request, render_template, session
from parse_resume import parse_pdf_resume
from langgraph.graph import StateGraph
from typing import TypedDict, List
from typing_extensions import Annotated
from claude_parser import extract_resume_info_with_claude
from match_resume import rank_resumes_by_job_description, get_embedding, score_resumes_by_job_description
from sendemail import send_candidate_interview_email, send_candidate_ranking_email
import  json
import os
from werkzeug.utils import secure_filename
from flask_session import Session

UPLOAD_FOLDER = "sample_data"

# Load SMTP configuration from config file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Extract configuration values
sender_email = config['sender_email']
smtp_server = config['smtp_server']
smtp_port = config['smtp_port']
username = config['username']
password = config['password']
hireforgeHR_email= config['hireforgeHR_email']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = '87f1fd8c-3388-4d0d-a6eb-5048d9368081'
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)


# LangGraph State
class State(TypedDict):
    uploaded_files: Annotated[List[str], "multiple"]
    parsed_resumes: List[dict]
    ranked_resumes: List[dict]

# LangGraph Nodes
def upload_handler(state):
    # Just pass through in this version
    return state

def parse_resumes(state):
    results = []
    for file_path in state.get("uploaded_files", []):
        try:
            raw = parse_pdf_resume(file_path)
            resume_text = raw.get("text", "")
            extracted = extract_resume_info_with_claude(resume_text)
            extracted["filename"] = os.path.basename(file_path)
            extracted["text"] = resume_text
            results.append(extracted)
        except Exception as e:
            results.append({"filename": file_path, "error": str(e)})
    state["parsed_resumes"] = results
    return state

def embed_and_score_resumes(state):
    try:
        parsed_resumes = state.get("parsed_resumes", [])

        # Embeddings
        texts = [r["text"] for r in parsed_resumes if r.get("text")]
        embeddings = get_embedding(texts)
        for i, r in enumerate(parsed_resumes):
            r["embedding"] = embeddings[i]

        # Job description
        job_description = "Senior .NET/Azure Engineer with 10+ years experience"
        job_embedding = get_embedding([job_description])[0]

        # Cosine similarity ranking
        ranked_resumes = rank_resumes_by_job_description(parsed_resumes, job_description, job_embedding)
        # print("ranked_resumes:", json.dumps(ranked_resumes, indent=2))

        # GPT-4o deep scoring
        wrapped_ranked = [{"resume": r} for r in ranked_resumes]
        deep_scored = score_resumes_by_job_description(ranked_resumes, job_description)
        print("deep_scored:", json.dumps(deep_scored, indent=2))

        state["ranked_resumes"] = deep_scored
        return state

    except Exception as e:
        state["error"] = str(e)
        return state



def end(state):
    return state

# LangGraph Flow
workflow_upload = StateGraph(State)
workflow_upload.add_node("UploadHandler", upload_handler)
workflow_upload.add_node("ResumeParser", parse_resumes)
workflow_upload.add_node("OutputParsedResumes", end)

workflow_upload.set_entry_point("UploadHandler")
workflow_upload.add_edge("UploadHandler", "ResumeParser")
workflow_upload.add_edge("ResumeParser", "OutputParsedResumes")
graph_upload = workflow_upload.compile()

workflow_score = StateGraph(State)
workflow_score.add_node("EmbedAndRankResumes", embed_and_score_resumes)
workflow_score.add_node("OutputScoredResumes", end)

workflow_score.set_entry_point("EmbedAndRankResumes")
workflow_score.add_edge("EmbedAndRankResumes", "OutputScoredResumes")
graph_score = workflow_score.compile()

# Flask Route
@app.route('/', methods=['GET'])
def home():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        files = request.files.getlist('resumes')
        file_paths = []

        for file in files:
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            file_paths.append(save_path)

        # ✅ This is where we pass the uploaded file paths into LangGraph
        state_input = {"uploaded_files": file_paths}
        final_state = graph_upload.invoke(state_input)
        parsed = final_state.get("parsed_resumes", [])
        session["parsed_resumes"] = parsed
        session.modified = True

        print("Final parsed resumes going into session:", parsed)
        return render_template('ranking.html', results=parsed)


    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/score', methods=['POST'])
def score():
    print("Session inside /score:", dict(session))

    try:
        parsed_resumes = session.get("parsed_resumes", [])
        state_input = {"parsed_resumes": parsed_resumes}

        final_state = graph_score.invoke(state_input)
        ranked = final_state.get("ranked_resumes", [])
        send_candidate_ranking_email(ranked,sender_email=sender_email,
                                     hireforgeHR_email=hireforgeHR_email,
                                     smtp_server=smtp_server,
                                     smtp_port=smtp_port, 
                                     username=username,
                                     password=password)
        print("ranked:", json.dumps(ranked, indent=2))

        session["ranked_resumes"] = ranked
        # Optional: save to session
        # session["ranked_resumes"] = ranked

        return render_template("scoring.html", results=ranked, scored=True)

    except Exception as e:
        return f"Error: {str(e)}", 500
    
@app.route('/send_email', methods=['POST'])
def sendMail():
    print("Session inside /send_email:", dict(session))
    try:
        name = request.form['name']
        candidate_email = request.form['email']
        send_candidate_interview_email(name=name,candidate_email=candidate_email,sender_email=sender_email,
               smtp_server=smtp_server,
               smtp_port=smtp_port, 
               username=username,
               password=password)
        
        print("Email Sent Successfully")
        # Return the same page with a flag
        
        results = session.get("ranked_resumes", [])
        for item in results:
          if item['email'] == candidate_email:
             item['scheduled'] = True  # Add a flag to indicate scheduling

        # Save updated results back to session (outside the loop)
        session["ranked_resumes"] = results
        session.modified = True

        # Print for debugging
        print("ranked resumes:", json.dumps(results, indent=2))
        return render_template('scoring.html', results=results, scored=True)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, use_reloader=False)

