from flask import Flask, render_template, request, redirect, url_for
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from pdfrw import PdfReader
from openai import OpenAI
from applib import API_KEY, infodict
import markdown
import tempfile
import pytesseract
from pdf2image import convert_from_path
import re

# Sett sti til tesseract om nødvendig:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

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

        subject_info = fetch_subject_info(subject_code)
        exam_content = read_file_content(exam_path)
        solution_content = read_file_content(solution_path) if solution_path else None

        grade, short_reason, full_reason, reasoning = get_feedback_from_chatgpt(subject_code, subject_info, exam_content, solution_content)

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


def extract_form_fields(pdf_path):
    pdf = PdfReader(pdf_path)
    fields = []
    if '/AcroForm' in pdf:
        acroform = pdf['/AcroForm']
        if acroform and '/Fields' in acroform:
            for f in acroform['/Fields']:
                field = f.resolve()
                name = field.get('/T')
                field_type = field.get('/FT')
                value = field.get('/V')
                options = field.get('/Opt')
                
                field_info = {
                    'name': name,
                    'type': field_type,
                    'value': value,
                }
                if options:
                    field_info['options'] = options
                
                fields.append(field_info)
    return fields

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
    if file_path is None:
        return ""
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == '.pdf':
        text = read_pdf(file_path)
        form_fields = extract_form_fields(file_path)

        if form_fields and len(form_fields) > 0:
            # Form fields funnet
            form_info = "\n\n[Form Fields (kandidatens valgte svar på flervalg og felt):]\n"
            for fld in form_fields:
                name = fld.get('name', 'Ukjent felt')
                ftype = fld.get('type', 'Ukjent type')
                val = fld.get('value', 'Ingen verdi')
                
                form_info += f"Felt: {name}\n"
                form_info += f" - Type: {ftype}\n"
                form_info += f" - Verdi: {val}\n"
                if 'options' in fld:
                    form_info += f" - Mulige alternativer:\n"
                    for opt in fld['options']:
                        opt_val = opt if isinstance(opt, str) else opt.to_unicode()
                        form_info += f"   * {opt_val}\n"
                
                form_info += "\n"
            text += form_info
        else:
            # Ingen formfelter - bruk OCR
            text += detect_selected_answers_ocr(file_path)

        return text

    elif file_extension.lower() in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return ""


def read_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text


def detect_selected_answers_ocr(file_path):
    """
    Bruk OCR for å identifisere valgte svar.
    Juster koden nedenfor etter hvordan valgte alternativer vises i OCR-tekst.
    Anta for eksempel at valgte svar gjenkjennes av OCR som "(X)" eller "■".
    """
    info_str = "\n\n[Forsøk på å identifisere valgte svar via OCR:]\n"
    with tempfile.TemporaryDirectory() as temp_dir:
        images = convert_from_path(file_path, output_folder=temp_dir, fmt='png', dpi=300)
        for i, img in enumerate(images):
            ocr_text = pytesseract.image_to_string(img, lang='nor')  # ev. 'eng' hvis engelsk
            # Eksempel: Søk etter linjer med '(X)' eller '■' foran alternativet
            # Juster regex basert på virkelige resultater fra OCR
            # Eksempel regex: søk etter linjer som starter med '[x]' eller '(x)'
            pattern = r'^[\(\[]x[\)\]]\s+(.*)$'  # juster om nødvendig
            matches = re.findall(pattern, ocr_text, re.MULTILINE|re.IGNORECASE)
            for match in matches:
                info_str += f"Valgt svar funnet på side {i+1}: {match}\n"
    return info_str


def get_feedback_from_chatgpt(subject_code, subject_info, exam_content, solution_content):
    print(exam_content)
    prompt = f"""
Du er en sensor i faget {subject_code}. Her er informasjon om emnet:
{subject_info}
{infodict[subject_code] if subject_code in infodict else "OBS: dette emnet er ikke støttet, så estimatet er ikke veldig nøyaktig."}

Nedenfor er kandidatens eksamensbesvarelse, inkludert alle fritekstsvar, kode, figurer beskrevet i tekst, samt flervalgs- og skjemaopplysninger (form fields) og/eller OCR-identifiserte svar. Du må anta at dette er en nøyaktig gjengivelse av kandidatens svar. Ikke gjett utover det som står her.

--- Kandidatens eksamensbesvarelse START ---
{exam_content}
--- Kandidatens eksamensbesvarelse SLUTT ---

--- Løsningsforslag START ---
{f"{solution_content}" if solution_content else "Ingen løsningsforslag ble oppgitt."}
--- Løsningsforslag SLUTT ---

Vurder besvarelsen basert på informasjonen om emnet. Først skal du resonnere stegvis og grundig om besvarelsen (chain-of-thought). 
På aller siste linje skal du oppgi Karakter||Kort begrunnelse||Full begrunnelse, og ikke nevn karakteren før siste linje. 
Eksempel på aller siste linje:
B||Kandidaten oppnådde 73%, som tilsvarer karakteren C.||Kandidaten leverte sterke løsninger på programmeringsoppgavene i fritekstdelen, men manglet flere svar i flervalgsdelen, noe som trakk ned den totale poengsummen.

Karakterskala:
A: 89-100%
B: 77-88%
C: 65-76%
D: 53-64%
E: 40-52%
F: <40 %
Karakteren skal gis basert på poengsum og karakterskalaen. Sett en grønn check-emoji bak oppgavene med full uttelling i den stegvise vurderingen.
"""

    try:
        response = client.chat.completions.create(
            model="chatgpt-4o-latest", 
            messages=[
                {"role": "system", "content": "Du er en streng, men rettferdig sensor med full kjennskap til faget."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.3
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