# parse_resume.py
import pdfplumber

def parse_pdf_resume(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    return {"text": text.strip()}
    # Simple dummy extraction
    # lines = text.splitlines()
    # return lines
    # return {
    #     "raw_text": text,
    #     "name": lines[0].strip() if lines else "Unknown",
    #     "email": next((l for l in lines if "@" in l), "Not found"),
    #     "years_experience": "10+",  # placeholder
    #     "skills": [kw for kw in ["Azure", ".NET", "C#", "Cloud"] if kw.lower() in text.lower()]
    # }

