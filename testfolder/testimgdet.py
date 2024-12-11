import cv2
import pytesseract
import numpy as np

def detect_highlighted_answer(image_path, resize_ratio=0.8): #lavere resize er raskere men for lav risikerer unøyaktighet i tolkning av tesseract
    # Load the image
    img = cv2.imread(image_path)
    img = cv2.resize(img, None, fx=resize_ratio, fy=resize_ratio, interpolation=cv2.INTER_AREA)

    # Convert to HSV to detect blue region
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Define the range for detecting blue (adjust as needed) fargen er: 188, 216, 240?? Verdiene under funker gjennom trial and error.
    lower_blue = np.array([70, 40, 230])
    upper_blue = np.array([120, 50, 255])

    # Create a mask for the blue region
    mask = cv2.inRange(hsv_img, lower_blue, upper_blue)

    # Find contours of the blue area
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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

# Example usage
result = detect_highlighted_answer("/Users/jakobildstad/Documents/VSC_general/estimate_grade_webapp/testfolder/imgfolder/cropped_page_17.png")
print(result)
