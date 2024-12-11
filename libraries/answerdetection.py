import cv2
import pytesseract
import numpy as np
import pdfplumber
from pdf2image import convert_from_path
import logging
from fuzzywuzzy import fuzz


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
                pages_with_text.append(i)
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

def find_text_location(image, target_text="Velg ett alternativ", threshold=80):
    """
    Bruker OCR til å finne posisjonen til target_text i et bilde.
    Returnerer (x, y, w, h) hvis funnet, ellers None.
    """
    data = pytesseract.image_to_data(image, lang='nor', output_type=pytesseract.Output.DICT)
    n_boxes = len(data['level'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        similarity = fuzz.partial_ratio(text.lower(), target_text.lower())
        if similarity >= threshold:
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            logging.info(f"Fant '{target_text}' på posisjon: ({x}, {y}, {w}, {h}) med likhet: {similarity}")
            return (x, y, w, h)
    return None

def crop_answer_region(image, text_box, page_height, page_width, padding=10):
    """
    Cropper 1/3 av siden under posisjonen til målteksten "Velg ett alternativ".
    
    Parameters:
    - image: OpenCV-bilde av siden.
    - text_box: Tuple (x, y, w, h) for posisjonen til "Velg ett alternativ".
    - page_height: Total høyde på siden i piksler.
    - page_width: Total bredde på siden i piksler.
    - padding: Antall piksler mellom slutten av teksten og startpunktet for cropping.
    
    Returns:
    - Cropped bilde som dekker 1/3 av siden under målteksten.
    """
    x, y, w, h = text_box
    # Startpunkt for cropping: slutten av teksten + padding
    crop_start_y = y + h + padding
    # Høyde på det croppede området: 1/3 av siden
    crop_height = page_height // 2
    # Sørg for at vi ikke går utenfor bildet
    crop_end_y = min(crop_start_y + crop_height, page_height)
    
    # Hvis du ønsker å dekke hele bredden:
    crop_start_x = 0
    crop_width = page_width
    
    # Alternativt, hvis du vil beholde bredden rundt teksten:
    # crop_start_x = max(x - 50, 0)  # Juster 50 piksler til venstre
    # crop_width = min(w + 100, page_width - crop_start_x)  # Juster 50 piksler til høyre
    
    cropped = image[crop_start_y:crop_end_y, crop_start_x:crop_start_x + crop_width]
    logging.info(f"Cropped området for svar: {cropped.shape} (start_y: {crop_start_y}, end_y: {crop_end_y})")
    return cropped

def preprocess_image_for_ocr(image):
    """
    Forhåndsbehandler bildet for bedre OCR-resultater.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    # Anvend binær terskling
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    return thresh

def detect_highlighted_answer(img, resize_ratio=0.8, max_contours=5): #lavere resize er raskere men for lav risikerer unøyaktighet i tolkning av tesseract
    #Preprocess
    img = cv2.resize(img, None, fx=resize_ratio, fy=resize_ratio, interpolation=cv2.INTER_AREA)

    # Convert to HSV to detect blue region
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Define the range for detecting blue (adjust as needed)
    lower_blue = np.array([94, 46, 230])
    upper_blue = np.array([104, 66, 250])

    # Create a mask for the blue region
    mask = cv2.inRange(hsv_img, lower_blue, upper_blue)

    # Find contours of the blue area
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) #[:max_contours]

    # Sort contours by area to focus on the largest (likely the highlight)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for contour in contours:
        # Get bounding box of the highlighted region
        x, y, w, h = cv2.boundingRect(contour)

        # Crop the highlighted region
        cropped = img[y:y+h, x:x+w]

        # Use OCR on the cropped image
        answer_text = pytesseract.image_to_string(cropped, lang='nor')

        # Return the detected answer
        if answer_text.strip():
            return f"Highlighted Answer: {answer_text.strip()}"
    
    return "No highlighted answer detected"

def fetch_multiple_choice_answers(pdf_path):
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
        # Hent dimensjonene til siden
        page_height, page_width = image.shape[:2]
        
        # Trinn 3: Finn posisjonen til "Velg ett alternativ"
        text_box = find_text_location(image, "Velg ett alternativ")
        if text_box:
            # Trinn 4: Crop området hvor det markerte svaret er (1/3 av siden under teksten)
            answer_region = crop_answer_region(image, text_box, page_height, page_width)

            #Lagrer bildet for inspeksjon
            """
            cropped_path = f"/Users/jakobildstad/Documents/VSC_general/estimate_grade_webapp/testfolder/imgfolder/cropped_page_{page_number + 1}.png"
            cv2.imwrite(cropped_path, answer_region)
            logging.info(f"Lagrer croppede bilde som {cropped_path}")
            """
            
            # Trinn 5: Oppdag det markerte svaret uten forhåndsbehandling
            answer = detect_highlighted_answer(answer_region)
            
            # Optional: Forhåndsbehandle det detekterte svaret for OCR hvis nødvendig
            # preprocessed = preprocess_image_for_ocr(answer_region)
            # answer = detect_highlighted_answer(preprocessed)
            
            results.append({
                "page": page_number + 1,  # Gjør det 1-indeksert for lesbarhet
                "answer": answer
            })
        else:
            logging.warning(f"'Velg ett alternativ' ikke funnet på side {page_number + 1}.")
    
    return results