import pytesseract
from PIL import Image, ImageOps, ImageFilter
import numpy

from comparison import analyze

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_CONFIG = "--psm 6 -c tessedit_char_whitelist=0123456789"

def get_surrounding_square(rect):
    # Calculate the width and height of the rectangle
    rect_width = rect[2] - rect[0]
    rect_height = rect[3] - rect[1]

    # Determine the size of the square (the maximum dimension of the rectangle)
    square_size = max(rect_width, rect_height)

    # Calculate the coordinates of the square
    square_x1 = rect[0] - (square_size - rect_width) // 2
    square_y1 = rect[1] - (square_size - rect_height) // 2
    square_x2 = square_x1 + square_size
    square_y2 = square_y1 + square_size

    return (square_x1, square_y1, square_x2, square_y2)

def rotate_square_section(img, raw_bbox):

    margin = 3
    square_section = img.crop(
        (
            max(0, raw_bbox[0] - margin),
            max(0, raw_bbox[1] - margin),
            min(img.size[0], raw_bbox[2] + margin),
            min(img.size[1], raw_bbox[3] + margin),
        )
    )
    
    # rotated_section = square_section.rotate(-90, expand=True)

    return square_section

# Finds the bounding box of all the non-white pixels in an image
def get_bounding_box(img):
    bounding_image = img.copy()
    bounding_image = bounding_image.convert("RGBA")
    for x in range(bounding_image.width):
        for y in range(bounding_image.height):
            # Check if the pixel is white
            if bounding_image.getpixel((x, y)) == (255, 255, 255, 255):
                # Set the pixel in the transparent image to transparent
                bounding_image.putpixel((x, y), (0, 0, 0, 0))

    return bounding_image.getbbox()


# Processes the image of a single left clue
def left_clues(img, i):
    # Enlarge
    # size = 2
    # img = img.resize((img.size[0] * size, img.size[1] * size))

    # Crop to content
    raw_bbox = get_bounding_box(img)
    margin = 3
    img = img.crop(
        (
            max(0, raw_bbox[0] - margin),
            max(0, raw_bbox[1] - margin),
            min(img.size[0], raw_bbox[2] + margin),
            min(img.size[1], raw_bbox[3] + margin),
        )
    )

    # img.save(f'l_{i}.png')

    # Get all characters
    res = pytesseract.image_to_boxes(
        img, config=TESSERACT_CONFIG, output_type=pytesseract.Output.DICT
    )
    # Process character in order, adding separations where the gap between the characters is too large
    nums = [res["char"][0]]
    for i in range(1, len(res["char"])):
        if (
            nums[-1] == "1" and res["left"][i] - res["right"][i - 1] < 8
        ):  # potential double digit number
            nums[-1] += res["char"][i]
        else:
            nums.append(res["char"][i])

    return [int(x) for x in nums]


# Processes the image of a single top clue
def top_clues(img, i):
    # Enlarge
    # size = 2
    # img = img.resize((img.size[0] * size, img.size[1] * size))

    # Crop to content
    raw_bbox = get_bounding_box(img)
    margin = 3
    img = img.crop(
        (
            max(0, raw_bbox[0] - margin),
            max(0, raw_bbox[1] - margin),
            min(img.size[0], raw_bbox[2] + margin),
            min(img.size[1], raw_bbox[3] + margin),
        )
    )

    # img.save(f"t_{i}.png")
    
    # Get boxes for numbers
    arr = numpy.array(img.point(lambda x: 0 if x < 128 else 255, "1"))

    positions = []
    start = -1
    left = 10**9
    right = -1
    for j, row in enumerate(arr):
        if not all(row):
            if start == -1:
                start = j
            else:
                t = numpy.where(row == False)[0]
                left = min(left, numpy.min(t))
                right = max(right, numpy.max(t))
        else:
            if start != -1:
                positions.append(get_surrounding_square((left - 1, start - 1, right + 1, j + 1)))
                start = -1
                left = 10**9
                right = -1

    # Rotate numbers
    final = []
    for j, box in enumerate(positions):
        a = rotate_square_section(img, box)
        a = a.point(lambda x: 0 if x < 128 else 255, "1")
        # a.save(f'a_{j}.png')
        num = analyze(a)
        final.append(num)
        
    return final


# Identifies the difficulty of the level and sets the appropriate factor
def get_difficulty(img):
    FACTOR = 0

    level_box = (1240, 84, 1310, 115)  # (1390, 84, 1460, 115)

    img = img.crop(level_box)  # Crop to text
    img = img.resize((img.size[0] * 2, img.size[1] * 2))  # Scale up
    img = ImageOps.autocontrast(ImageOps.grayscale(img))  # Simplify image

    raw_bbox = get_bounding_box(img)
    margin = 1
    img = img.crop(
        (
            max(0, raw_bbox[0] - margin),
            max(0, raw_bbox[1] - margin),
            min(img.size[0], raw_bbox[2] + margin),
            min(img.size[1], raw_bbox[3] + margin),
        )
    )

    level_text = pytesseract.image_to_string(img, config="--psm 8").lower().strip()
    print("Level difficulty:", level_text)

    if level_text == "easy" or level_text == "medium":
        FACTOR = 10
    elif level_text == "hard":
        FACTOR = 15

    return FACTOR


if __name__ == "__main__":
    # for i in range(7,8):
    i = 11
    print(top_clues(Image.open(f"t_{i}.png"), i=i))
