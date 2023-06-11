import threading
import pynput, pyautogui
from PIL import ImageOps, ImageFilter
from solver import solve
from clues import top_clues, left_clues, get_difficulty

from pynput.mouse import Button, Controller
import time

listener = None

INFINITE = True
OVERRIDE = False
FACTOR = 0

TESSERACT_CONFIG = "--psm 6 -c tessedit_char_whitelist=0123456789"

constants = {
    10: {
        "LEFT_BOX": (0, 200, 140, 800),
        "TOP_BOX": (140, 50, 750, 195),
        "START": (145, 200),
        "SIZE": 60,
    },
    15: {
        "LEFT_BOX": (0, 200, 140, 800),
        "TOP_BOX": (140, 50, 750, 195),
        "START": (142, 200),
        "SIZE": 40,
    },
}

# Simplifies image for clue data
def process_image(img):
    def change_contrast(x, level):
        factor = (259 * (level + 255)) / (255 * (259 - level))

        def contrast(c):
            return 128 + factor * (c - 128)

        return x.point(contrast)

    img = img.convert("L")
    img = change_contrast(img, 100)
    img = img.crop((880, 200, 1640, 1010))  # img.crop((1040,200,1800,1010))
    return img


# Clicks all items in the input matrix according to the given grid start and size
def click_grid_items(input_matrix, start, size):
    grid_width = grid_height = size
    grid_top_left_x = start[0]
    grid_top_left_y = start[1]

    # Global offset
    grid_top_left_x += 890  # 1040
    grid_top_left_y += 200

    # Create a mouse controller instance
    mouse = Controller()

    # Loop through each item in the input matrix
    for i in range(len(input_matrix)):
        for j in range(len(input_matrix[i])):
            if input_matrix[i][j]:
                # Calculate the position of the current grid item
                grid_item_x = grid_top_left_x + j * grid_width
                grid_item_y = grid_top_left_y + i * grid_height

                # Move the mouse to the center of the current grid item
                mouse.position = (
                    grid_item_x + grid_width // 2,
                    grid_item_y + grid_height // 2,
                )

                # Click the left mouse button
                mouse.click(Button.left)

                # Wait for a short time to give the click time to register
                time.sleep(0.1)


def click_next():
    mouse = Controller()
    mouse.position = (1260, 1290)

    # Click 5 times just in case
    for _ in range(5):
        mouse.click(Button.left)
        time.sleep(0.1)


def extract_clues(ss):
    global FACTOR

    FACTOR = get_difficulty(ss)

    if FACTOR == 0:
        print("Error: Couldn't read difficulty")
        listener.stop()
        exit()

    ss = process_image(ss)

    left_img = ss.crop(constants[FACTOR]["LEFT_BOX"])
    clue_height = left_img.size[1] / FACTOR
    s_r = []
    for i in range(FACTOR):
        left_clue = left_img.crop((0, clue_height * i, left_img.size[0], clue_height * (i + 1)))
        s_r.append(left_clues(left_clue, i))

    # Write left clues to file
    with open("left.txt", "w") as f:
        for item in s_r:
            f.write(",".join([str(x) for x in item]))
            f.write("\n")

    top_img = ss.crop(constants[FACTOR]["TOP_BOX"])
    clue_width = top_img.size[0] / FACTOR
    s_c = []
    for i in range(FACTOR):
        top_clue = top_img.crop((clue_width * i, 0, clue_width * (i + 1), top_img.size[1]))
        s_c.append(top_clues(top_clue, i=i))

    # Write top clues to file
    with open("top.txt", "w") as f:
        for item in s_c:
            f.write(",".join([str(x) for x in item]))
            f.write("\n")

    print("Successfully scanned clues:")
    l_str = [",".join([str(x) for x in c]) for c in s_r]
    t_str = [",".join([str(x) for x in c]) for c in s_c]
    print("Left clues: |" + ("%-7s|" * FACTOR) % tuple(l_str))
    print("Top clues:  |" + ("%-7s|" * FACTOR) % tuple(t_str))


def run_solve():
    s_r = []
    s_c = []
    with open("left.txt", "r") as f:
        for line in f.readlines():
            s_r.append(list(map(int, line.split(","))))

    with open("top.txt", "r") as f:
        for line in f.readlines():
            s_c.append(list(map(int, line.split(","))))

    FACTOR = len(s_r)

    success, result = solve(FACTOR, s_r, s_c)
    if not success:
        print("Invalid nonogram")
        listener.stop()
        exit()

    click_grid_items(result, constants[FACTOR]["START"], constants[FACTOR]["SIZE"])


def threaded_solver():
    count = 1
    current = time.time()
    while True:
        if not (OVERRIDE and count == 1):
            ss = pyautogui.screenshot()
            extract_clues(ss)
        run_solve()
        time.sleep(5)
        click_next()
        time.sleep(1.5)
        print("Solved: #", count, "in", round(time.time() - current, 2), "s")
        print("-" * 25)
        count += 1
        current = time.time()


def keyboard_logger(key):
    global FACTOR, OVERRIDE

    if not (hasattr(key, "vk") and 96 <= key.vk <= 105):
        return

    NUMPAD = 96
    # Exit
    if key.vk == (NUMPAD + 7):  # NUM 7
        return False
    # Scan (and solve)
    elif key.vk == (NUMPAD + 1):  # NUM 1
        if INFINITE:
            driver = threading.Thread(target=threaded_solver)
            driver.start()
        else:
            ss = pyautogui.screenshot()
            extract_clues(ss)
            run_solve()
            time.sleep(8)
            click_next()
    elif key.vk == (NUMPAD + 6):  # NUM 1
        if INFINITE:
            OVERRIDE = True
            driver = threading.Thread(target=threaded_solver)
            driver.start()


if __name__ == "__main__":
    listener = pynput.keyboard.Listener(on_release=keyboard_logger)
    listener.start()
    listener.join()
