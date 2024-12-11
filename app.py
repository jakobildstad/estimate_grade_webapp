from flask import Flask, render_template, request, redirect, url_for
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from openai import OpenAI
import markdown
from libraries.applib import API_KEY, infodict #egen
from libraries.answerdetection import fetch_multiple_choice_answers #egen

client = OpenAI(api_key=API_KEY)
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        subject_code = request.form['subjectCode']
        return redirect(url_for('upload', subject_code=subject_code))

    supported_subjects = list(infodict.keys())
    return render_template('index.html', supported_subjects=supported_subjects)


@app.route('/upload/<subject_code>', methods=['GET', 'POST'])
def upload(subject_code):
    if request.method == 'POST':
        exam_file = request.files.get('examFile')
        solution_file = request.files.get('solutionFile')

        if not exam_file:
            return render_template('upload.html', subject_code=subject_code, error="Eksamensbesvarelse er påkrevd")

        exam_path = os.path.join(app.config['UPLOAD_FOLDER'], exam_file.filename)
        exam_file.save(exam_path)
        
        solution_path = None
        if solution_file:
            solution_path = os.path.join(app.config['UPLOAD_FOLDER'], solution_file.filename)
            solution_file.save(solution_path)

        # Hent data fra PDF
        subject_info = fetch_subject_info(subject_code)
        exam_content = read_file_content(exam_path)
        solution_content = read_file_content(solution_path) if solution_path else None
        multiple_choice_answers = fetch_multiple_choice_answers(exam_path)


        grade, short_reason, full_reason, reasoning = get_feedback_from_chatgpt(
            subject_code, subject_info, exam_content, solution_content, multiple__choice_answers=multiple_choice_answers
        )

        # Fjern '**' fra karakter og begrunnelser
        grade = grade.replace('**', '')
        short_reason = short_reason.replace('**', '')
        full_reason = full_reason.replace('**', '')

        # Konverter full_reason og reasoning til HTML via markdown
        full_reason_html = markdown.markdown(full_reason)
        reasoning_html = markdown.markdown(reasoning)

        return render_template(
            'result.html',
            subject_code=subject_code,
            grade=grade,
            short_reason=short_reason,
            full_reason=full_reason_html,
            reasoning=reasoning_html
        )

    return render_template('upload.html', subject_code=subject_code)


def fetch_subject_info(subject_code):
    possible_urls = [
        f"https://wiki.math.ntnu.no/{subject_code}",
        f"https://www.ntnu.no/studier/emner/{subject_code}"
    ]
    for url in possible_urls:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.get_text(separator="\n").strip()
            return content
    return "Fant ikke spesifikk informasjon om emnet."


def read_file_content(file_path):
    if not file_path:
        return ""

    _, file_extension = os.path.splitext(file_path)
    content = ""

    if file_extension.lower() == '.pdf':
        # Les tekst fra PDF
        pdf_text = read_pdf(file_path)
        content += f"\n\n[PDF Tekstuttrekk:]\n{pdf_text}"
    else:
        content += f"Ukjent filformat: {file_extension}"

    return content


def read_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text


def get_feedback_from_chatgpt(subject_code, subject_info, exam_content, solution_content, multiple__choice_answers):
    print(multiple__choice_answers)
    prompt = f"""
Du er en sensor i faget {subject_code}. Her er informasjon om emnet:
{subject_info}
{infodict[subject_code] if subject_code in infodict else ""}

Nedenfor er kandidatens eksamensbesvarelse. Du må anta at dette er en nøyaktig gjengivelse av kandidatens svar.

Vurder besvarelsen basert på informasjonen om emnet. Først skal du resonnere stegvis og grundig om besvarelsen (chain-of-thought). 
På aller siste linje skal du oppgi Karakter||Kort begrunnelse||Full begrunnelse, og ikke nevn karakteren før siste linje. 
Eksempel på aller siste linje:
B||Kandidaten oppnådde 73%, som tilsvarer karakteren C.||Kandidaten leverte sterke løsninger på programmeringsoppgavene i fritekstdelen, men manglet flere svar i flervalgsdelen, noe som trakk ned den totale poengsummen.
Du må følge karakterskalaen når du setter karakter. I den fulle begrunnelsen skal du sette grønn check-emoji bak oppgaver med full uttelling.

Det er svært sjeldent at en kandidat ikke har svart på en oppgave, så hvis du tolker at det ikke er svart, prøv å se etter et svar etter følgende mønster:
I flervalgsoppgaver er formatet omtrentlig slik 'B (A, B, C, D)' løpende i teksten. Da er det det elementet som kommer to ganger som er svaret (B i DETTE tilfellet). På starten av slike oppgaver står det ofte noe slik som "velg riktig alternativ".
Drag-and-drop-oppgaver er slik at hvis koden på slutten av oppgaven er rett, er oppgaven rett besvart. Du skal gi noe uttelling hvis noe er rett.

Karakterskala:
A: 89-100%
B: 77-88%
C: 65-76%
D: 53-64%
E: 40-52%
F: <40 %

--- Kandidatens eksamensbesvarelse START ---
{exam_content}
--- Kandidatens eksamensbesvarelse SLUTT ---

--- Svar på flervalgsoppgaver START ---
{multiple__choice_answers}
--- Svar på flervalgsoppgaver SLUTT ---

--- Løsningsforslag START ---
{f"{solution_content}" if solution_content else "Ingen løsningsforslag ble oppgitt."}
--- Løsningsforslag SLUTT ---


"""

    try:
        response = client.chat.completions.create(
            model="chatgpt-4o-latest", 
            messages=[
                {"role": "system", "content": "Du er rettferdig sensor med full kjennskap til faget. Dersom det er feil svar, skal du likevel gi litt poeng dersom det vises forståelse"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.4
        )
        raw_content = response.choices[0].message.content.strip()

        lines = raw_content.split('\n')
        last_line = lines[-1].strip()
        parts = last_line.split("||")
        grade = parts[0].strip() if len(parts) > 0 else "Ukjent"
        short_reason = parts[1].strip() if len(parts) > 1 else ""
        full_reason = parts[2].strip() if len(parts) > 2 else last_line

        reasoning = "\n".join(lines[:-1]).strip()

        return grade, short_reason, full_reason, reasoning

    except Exception as e:
        return "Ukjent", "", f"En feil oppsto ved kontakt med ChatGPT: {e}", ""


if __name__ == '__main__':
    app.run(debug=True)