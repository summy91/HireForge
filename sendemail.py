import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_candidate_interview_email(name,candidate_email,sender_email, smtp_server, smtp_port, username, password):
    interviewDate = '2025-12-08'
    time= '10:00 AM'
    job_title = 'Senior .NET/Azure Engineer'
    # Load HTML template
    with open("templates/email_template.html", "r", encoding="utf-8") as file:
        html_template = file.read()

    
    html_content = html_template.format(
        name=name,
        interviewDate=interviewDate,
        time=time,
        Job_Title=job_title
    )
    
    # Compose email
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = candidate_email
    msg["Subject"] = f"Interview Invitation for {job_title}"
    msg.attach(MIMEText(html_content, "html"))

    # Send email once
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(username, password)
        server.sendmail(sender_email, candidate_email, msg.as_string())
     
        
def send_candidate_ranking_email(ranked, sender_email,hireforgeHR_email, smtp_server, smtp_port, username, password):
    # Load Excel data
    df = pd.DataFrame(ranked)
    # Build HTML table rows
    table_rows = ""
    for _, row in df.iterrows():
        score = int(row['score'])
        if score>50:
            status_class = "Suitable"
            status_color = "green"
        else:
            status_class = "Rejected"
            status_color = "red"
        table_rows += f"""
        <tr>
            <td>{row['name']}</td>
            <td>{row['score']}</td>
            <td>{row['email']}</td>
            <td>{row['skills']}</td>
            <td style='color:{status_color}; font-weight:bold;'>{status_class}</td>
        </tr>
        """

    # Load HTML template
    with open("templates/candidate_score.html", "r", encoding="utf-8") as file:
        html_template = file.read()

    html_content = html_template.format(table_rows=table_rows)

    # Compose email
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = hireforgeHR_email
    msg["Subject"] = "Candidate Score Report for Senior .NET/Azure Engineer"
    msg.attach(MIMEText(html_content, "html"))

    # Send email once
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(username, password)
        server.sendmail(sender_email, hireforgeHR_email, msg.as_string())
        print("✅ Email sent successfully!")
