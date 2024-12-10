import PyPDF2


def read_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

with open("/Users/jakobildstad/Documents/VSC_general/estimate_grade_webapp/testfolder/text.txt", "w") as f:
    f.write(read_pdf("/Users/jakobildstad/Documents/VSC_general/estimate_grade_webapp/uploads/1342515_247425194_263397058_3.pdf"))

import os
import PyPDF2
from pdfrw import PdfReader
import tempfile
import pytesseract
from pdf2image import convert_from_path
import re


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


def read_file_content(file_path):
    if file_path is None:
        return ""
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == '.pdf':
        text = read_pdf(file_path)
        form_fields = extract_form_fields(file_path)

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
