import tempfile
from pdf2image import convert_from_path
import cv2
import numpy as np
from tqdm import tqdm
import os

def identify_rectangles(image, upper_color):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 40, 150)

    # Find contours
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for contour in contours:
        # Approximate the contour to a polygon
        epsilon = 0.005 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # If the contour has four vertices, it's likely a rectangle
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            if w > 200 and h > 18: # Adjust this threshold as needed
                # Extract the region of interest
                roi = image[y:y+h, x:x+w]

                # Calculate histogram
                hist = cv2.calcHist([roi], [0], None, [256], [0, 256])
                
                # Find the peak(s) in the histogram
                peaks = np.argmax(hist)
                
                # Background color will be the peak intensity
                background_color = [peaks, peaks, peaks]
                #print(background_color)

                # Check if it's within the limit color
                if (background_color[0] <= upper_color[0] and
                    background_color[1] <= upper_color[1] and
                    background_color[2] <= upper_color[2]):
                    rectangles.append((x, y, x + w, y + h))

    return rectangles

def find_rectangles(pdf_path):
    rectangles_list = []
    rectangles_coords = {}

    with tempfile.TemporaryDirectory() as path:
        images = convert_from_path(pdf_path, output_folder=path)

    bar = tqdm(total=len(images), desc='Removing rectangles')
    for i, image in enumerate(images):
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Define the upper limit of the background color
        gray_upper = (220, 220, 220)

        # Find rectangles with gray and black backgrounds
        gray_rectangles = identify_rectangles(img, gray_upper)

        for _, rect in enumerate(gray_rectangles):
            cv2.rectangle(img, (rect[0], rect[1]), (rect[2], rect[3]), (0, 255, 0), 2)
            rectangles_list.append(rect)  # Append the coordinates to the list

        rectangles_coords[i] = rectangles_list

        # Display or save the modified image
        # if not os.path.exists("images"):
        #     os.makedirs("images")
        # cv2.imwrite(f"images/output_{i}_image.jpg", img)
            
        bar.update(1)
    bar.clear()
    bar.close()

    return rectangles_coords
