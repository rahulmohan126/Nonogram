from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity, mean_squared_error

DB = [None]*16

GLOBAL_SCALE = 3

def compare(image1, image2):
    # Assures that 2-digit num does not get confused with 1-digit num
    if image1.size[0] > GLOBAL_SCALE * 14 and image2.size[0] < GLOBAL_SCALE * 14:
        return 0

    # Find the minimum size
    min_width = min(image1.width, image2.width)
    min_height = min(image1.height, image2.height)

    # Resize the images to the minimum size
    image1 = image1.resize((min_width, min_height))
    image2 = image2.resize((min_width, min_height))

    a1 = np.array(image1)
    a2 = np.array(image2)

    # Calculate the SSIM score
    score = structural_similarity(a1, a2)
    # score_2 = mean_squared_error(a1, a2)
    
    return score

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

def load():
    for i in range(16):
        img = Image.open(f'db/d{i}.png').convert('1')
        img = img.crop(get_bounding_box(img))
        img = img.resize((img.size[0]*GLOBAL_SCALE, img.size[1]*GLOBAL_SCALE))
        DB[i] = img

def analyze(img):
    og = img
    img = img.crop(get_bounding_box(img))
    img = img.resize((img.size[0]*GLOBAL_SCALE, img.size[1]*GLOBAL_SCALE))

    best = []
    for i in range(1,16):
        s = compare(DB[i].copy(), img)

        best.append((i, s))
    
    best.sort(key=lambda x: x[1], reverse=True)

    res = [x[0] for x in best]

    if set(res[:2]) == set([3, 8]):
        l_h = img.crop((0, img.size[1] // 4, img.size[0] // 2, img.size[1] * 3 // 4))
        l_3 = DB[3].crop((0, DB[3].size[1] // 4, DB[3].size[0] // 2, DB[3].size[1] * 3 // 4))
        l_8 = DB[8].crop((0, DB[8].size[1] // 4, DB[8].size[0] // 2, DB[8].size[1] * 3 // 4))

        s_3 = compare(l_3, l_h)
        s_8 = compare(l_8, l_h)
        
        if s_3 > s_8:
            return 3
        else:
            return 8
    elif set(res[:2]) == set([5,6]):
        l_h = img.crop((0, img.size[1] // 2, img.size[0] // 3, img.size[1]))
        l_5 = DB[5].crop((0, DB[5].size[1] // 2, DB[5].size[0] // 3, DB[5].size[1]))
        l_6 = DB[6].crop((0, DB[6].size[1] // 2, DB[6].size[0] // 3, DB[6].size[1]))
        
        s_5 = compare(l_5, l_h)
        s_6 = compare(l_6, l_h)

        if s_5 > s_6:
            return 5
        else:
            return 6
    elif res[0] >= 10:
        l_h = img.crop((img.size[0] // 2 - 3, 0, img.size[0], img.size[1]))
        l_h = l_h.crop(get_bounding_box(l_h))

        best = []
        for i in range(6):
            s = compare(DB[i].copy(), l_h)

            best.append((i, s))
        
        best.sort(key=lambda x: x[1], reverse=True)
        
        res = [x[0] for x in best]

        return res[0] + 10


    return res[0]


load()