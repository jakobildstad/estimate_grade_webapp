import cv2
import pytesseract
import numpy as np
import pdfplumber
from pdf2image import convert_from_path
import logging

PDF_PATH = "/Users/jakobildstad/Documents/VSC_general/estimate_grade_webapp/testfolder/jakob_exam.pdf"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    pages_with_text = extract_pages_with_text(PDF_PATH)
    print(pages_with_text)
    convert_pages_to_images(PDF_PATH, pages_with_text)
    """
    process_pdf(PDF_PATH)

def extract_pages_with_text(pdf_path, target_text="Velg ett alternativ"):
    """
    Funksjon for å identifisere sider som inneholder target_text.
    Returnerer en liste med sidetall (0-indeksert).
    """
    pages_with_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and target_text.lower() in text.lower():
                pages_with_text.append(i) #OBS
                logging.info(f"Fant '{target_text}' på side {i + 1}.")
    return pages_with_text

def convert_pages_to_images(pdf_path, pages, dpi=300):
    """
    Konverterer spesifikke sider i en PDF til bilder.
    Returnerer en liste med OpenCV-bilder.
    """
    images = []
    # Konverter bare de spesifikke sidene (pdf2image bruker 1-indeksert sider)
    pil_images = convert_from_path(pdf_path, dpi=dpi, first_page=min(pages)+1, last_page=max(pages)+1)
    for page_number, pil_image in zip(pages, pil_images):
        # Konverter PIL-bilde til OpenCV-format
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        images.append((page_number, image))
        logging.info(f"Konverterte side {page_number + 1} til bilde.")
    return images

def find_text_location(image, target_text="Velg ett alternativ"):
    """
    Bruker OCR til å finne posisjonen til target_text i et bilde.
    Returnerer (x, y, w, h) hvis funnet, ellers None.
    """
    data = pytesseract.image_to_data(image, lang='nor', output_type=pytesseract.Output.DICT)
    n_boxes = len(data['level'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        if text.lower() == target_text.lower():
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            logging.info(f"Fant '{target_text}' på posisjon: ({x}, {y}, {w}, {h})")
            return (x, y, w, h)
    return None

def crop_answer_region(image, text_box, offset_y=30, offset_h=100, offset_x=0, offset_w=300):
    """
    Cropper området hvor det markerte svaret sannsynligvis er, basert på posisjonen til målteksten.
    Juster offset-verdiene etter behov basert på PDF-layouten.
    """
    x, y, w, h = text_box
    # Definer området under målteksten hvor svaret befinner seg
    cropped = image[y + h + offset_y : y + h + offset_y + offset_h, x + offset_x : x + offset_x + offset_w]
    logging.info(f"Cropped området for svar: {cropped.shape}")
    return cropped

def preprocess_image_for_ocr(image):
    """
    Forhåndsbehandler bildet for bedre OCR-resultater.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Anvend binær terskling
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    return thresh

def detect_highlighted_answer(image, resize_ratio=0.8):
    """
    Funksjon for å oppdage markert svar i et bilde.
    """
    # Reduser oppløsningen
    img = cv2.resize(image, None, fx=resize_ratio, fy=resize_ratio, interpolation=cv2.INTER_AREA)

    # Konverter til HSV for å detektere blå region
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Definer rekkevidden for å detektere blå (juster etter behov)
    lower_blue = np.array([70, 40, 230])
    upper_blue = np.array([120, 50, 255])

    # Lag en maske for den blå regionen
    mask = cv2.inRange(hsv_img, lower_blue, upper_blue)

    # Finn konturer av den blå regionen
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Sorter konturer etter areal for å fokusere på den største (sannsynligvis høydepunktert)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for contour in contours:
        # Få bounding box av det markerte området
        x, y, w, h = cv2.boundingRect(contour)

        # Crop det markerte området
        cropped = img[y:y+h, x:x+w]

        # Bruk OCR på det croppede bildet
        custom_config = r'--oem 3 --psm 6'
        answer_text = pytesseract.image_to_string(cropped, lang='nor', config=custom_config)

        # Returner det oppdagede svaret
        if answer_text.strip():
            logging.info(f"Oppdaget markert svar: {answer_text.strip()}")
            return answer_text.strip()

    return "Ingen markert svar oppdaget"

def process_pdf(pdf_path):
    """
    Hovedfunksjon for å prosessere PDF og finne markerte svar.
    Returnerer en liste med resultater.
    """
    # Trinn 1: Identifiser sider med "Velg ett alternativ"
    pages = extract_pages_with_text(pdf_path, "Velg ett alternativ")
    if not pages:
        logging.warning("Ingen sider med 'Velg ett alternativ' funnet.")
        return []

    # Trinn 2: Konverter identifiserte sider til bilder
    images = convert_pages_to_images(pdf_path, pages, dpi=300)

    results = []
    for page_number, image in images:
        # Trinn 3: Finn posisjonen til "Velg ett alternativ"
        text_box = find_text_location(image, "Velg ett alternativ")
        if text_box:
            # Trinn 4: Crop området hvor det markerte svaret er
            answer_region = crop_answer_region(image, text_box)
            
            # Trinn 5: Forhåndsbehandle bildet for OCR
            preprocessed = preprocess_image_for_ocr(answer_region)
            
            # Trinn 6: Oppdag det markerte svaret
            answer = detect_highlighted_answer(preprocessed)
            results.append({
                "page": page_number + 1,  # Gjør det 1-indeksert for lesbarhet
                "answer": answer
            })
        else:
            logging.warning(f"'Velg ett alternativ' ikke funnet på side {page_number + 1}.")
    
    return results

main()