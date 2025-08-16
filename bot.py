from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
import cv2
from io import BytesIO
import os
import shutil
from skimage.metrics import structural_similarity as ssim

# ---------------------------
# Config
# ---------------------------
TEMPLATE_DIR = "templates"  # folder containing number and special tile templates
TILE_SIZE = 30  # approximate tile size (adjust if needed)
NUM_MINES = 40 
DEBUG_DIR = "debug_tiles"
DEBUG_LOG = "debug_log.txt"


# Delete old debug folder if it exists
if os.path.exists(DEBUG_DIR):
    shutil.rmtree(DEBUG_DIR)

os.makedirs(DEBUG_DIR, exist_ok=True)
os.makedirs(os.path.join(DEBUG_DIR, "success"), exist_ok=True)
os.makedirs(os.path.join(DEBUG_DIR, "fail"), exist_ok=True)

# ---------------------------
# Logging
# ---------------------------
log_file = open(DEBUG_LOG, "w")
def log(msg):
    print(msg)
    log_file.write(msg + "\n")

# ---------------------------
# Load templates
# ---------------------------
# Numbers 1-8
templates = {}
number_edges = {}
for i in range(1, 6):  # adjust to 1-8 if needed
    path = os.path.join(TEMPLATE_DIR, f"{i}.png")
    templates[i] = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    number_edges[i] = cv2.Canny(templates[i], 50, 150)

# Special tiles (-1 = unrevealed, 0 = empty)
special_templates = {}
for num in [-1, 0]:
    for bg in ["light", "dark"]:
        path = os.path.join(TEMPLATE_DIR, f"{num}_{bg}.png")
        special_templates[f"{num}_{bg}"] = cv2.imread(path, cv2.IMREAD_COLOR)  # color template

# ---------------------------
# Functions
# ---------------------------
def extract_tiles(opencv_image, rows, cols):
    tiles = []
    for r in range(rows):
        row_tiles = []
        for c in range(cols):
            x = c * TILE_SIZE
            y = r * TILE_SIZE
            tile_img = opencv_image[y:y+TILE_SIZE, x:x+TILE_SIZE]
            row_tiles.append(tile_img)
        tiles.append(row_tiles)
    return tiles

from skimage.metrics import structural_similarity as ssim  # Add this at the top of your script

def detect_tile(tile_img, r=None, c=None):
    gray_tile = cv2.cvtColor(tile_img, cv2.COLOR_BGR2GRAY)
    gray_tile = cv2.GaussianBlur(gray_tile, (3, 3), 0)
    h, w = gray_tile.shape

    # Only attempt number detection if edges exist
    edges_tile = cv2.Canny(gray_tile, 50, 150)
    if cv2.countNonZero(edges_tile) > 20:
        best_num = None
        best_score = -1
        for num, template_gray in templates.items():
            resized_template = cv2.resize(template_gray, (w, h), interpolation=cv2.INTER_NEAREST)
            score = ssim(gray_tile, resized_template)
            log(f"   Num {num} SSIM score: {score:.3f}")
            if score > best_score:
                best_score = score
                best_num = num

        if best_score > 0.6:  # adjust threshold if needed
            log(f"[Tile {r},{c}]✅ Matched number {best_num} with SSIM {best_score:.3f}")
            if r is not None and c is not None:
                cv2.imwrite(f"{DEBUG_DIR}/success/num{best_num}_r{r}_c{c}.png", tile_img)
            return best_num
        else:
            log(f"❌ Number detection failed (best SSIM {best_score:.3f})")
            if r is not None and c is not None:
                cv2.imwrite(f"{DEBUG_DIR}/fail/fail_num_r{r}_c{c}.png", tile_img)
            return -2

    # Hue-based detection for special tiles
    tile_hsv = cv2.cvtColor(tile_img, cv2.COLOR_BGR2HSV)
    avg_hue = np.mean(tile_hsv[:, :, 0])
    if 30 < avg_hue < 50:
        tile_type = -1
    elif 10 < avg_hue < 20:
        tile_type = 0
    else:
        tile_type = -2

    if r is not None and c is not None:
        subdir = "success" if tile_type != -2 else "fail"
        cv2.imwrite(f"{DEBUG_DIR}/{subdir}/num{tile_type}_r{r}_c{c}.png", tile_img)

    return tile_type

def surrounding_vals(detected_board, x, y):
    return [[detected_board[y-1][x-1], detected_board[y-1][x], detected_board[y-1][x+1]],
            [detected_board[y][x-1],None,detected_board[y][x+1]],
            [detected_board[y+1][x-1], detected_board[y+1][x], detected_board[y+1][x+1]]]

def click_tile(page, bounding_box, x, y, tile_size):
    """
    Clicks on the Minesweeper canvas at tile (x, y).
    - page: Playwright page object
    - canvas_selector: CSS selector for the canvas element
    - x, y: tile coordinates (not pixels)
    - tile_size: size of each tile in pixels
    """
    # Convert tile coords -> pixel coords (center of the tile)
    click_x = bounding_box["x"] + (x-1) * tile_size + tile_size // 2
    click_y = bounding_box["y"] + (y-1) * tile_size + tile_size // 2

    # Perform click
    page.mouse.click(click_x, click_y)
    print(f"Clicked tile {x}, {y}")


# ---------------------------
# Main bot
# ---------------------------
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Go to Google Minesweeper
    page.goto("https://www.google.com/search?q=minesweeper")
    input("Solve CAPTCHA manually, then press Enter here...")

    # Click Play
    play_selectors = ['div[jsname="ZC7Tjb"]', 'div[jsname="JNZWEd"]']
    play_clicked = False
    for selector in play_selectors:
        try:
            page.wait_for_selector(selector, timeout=5000)
            page.click(selector)
            play_clicked = True
            print(f"Clicked play button using selector: {selector}")
            break
        except:
            continue
    if not play_clicked:
        print("Failed to find a Play button. Please click it manually.")
        input("Then press Enter to continue...")

    # Wait for canvas
    canvas = page.wait_for_selector("canvas.ecwpfc")

    # Adjust rows/cols according to difficulty
    rows, cols = 14, 18  
    box = canvas.bounding_box()
    canvas_width = box["width"]
    TILE_SIZE = canvas_width // cols

    # Click center to start game
    center_x = box["x"] + box["width"] / 2
    center_y = box["y"] + box["height"] / 2
    page.mouse.click(center_x, center_y)

    page.wait_for_timeout(1000)
    canvas_screenshot = canvas.screenshot()

    mine_coords = set()

    while len(mine_coords) < NUM_MINES:
        # Convert to OpenCV
        image = Image.open(BytesIO(canvas_screenshot))
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        tiles = extract_tiles(opencv_image, rows, cols)

        # # Optionally display board
        # cv2.imshow("Board", opencv_image)
        # log("Press any key in the OpenCV window to close...")
        # cv2.waitKey(0)

        # Detect board numbers
        board_numbers = [[0] * (cols + 2)]  # top border

        for r in range(rows):
            row_numbers = [0]  # left border
            for c in range(cols):
                num = detect_tile(tiles[r][c], r, c)
                if num == -2:
                    log(f"failed to detect: row {r}, column {c}")
                row_numbers.append(num)
            row_numbers.append(0)  # right border
            board_numbers.append(row_numbers)

        board_numbers.append([0] * (cols + 2))  # bottom border

        # Print detected board
        log("Detected board:")
        for row in board_numbers:
            log(str(row))
        for y in range(1,rows+1):
            for x in range(1,cols+1):
                if board_numbers[y][x] > 0:
                    adj_unknown = []
                    adj_mines = []
                    surroundings = surrounding_vals(board_numbers, x, y)
                    for i in range(3):
                        for j in range(3):
                            if surroundings[i][j] == None:
                                continue
                            elif (y + i - 1, x + j - 1) in mine_coords:
                                adj_mines.append((i,j))
                            elif surroundings[i][j] == -1:
                                adj_unknown.append((i,j))
                    # If the full capacity of the block has been reached including unknowns, then everything adjacent is a mine
                    if len(adj_mines) + len(adj_unknown) == board_numbers[y][x]:
                        for value in adj_unknown:
                            mine_coords.add((y + value[0] - 1, x + value[1] - 1))
                    # If all the mines have been found, then everything thats unknown is safe
                    if len(adj_mines) == board_numbers[y][x]:
                        for value in adj_unknown:
                            click_tile(page, box, x + value[1] - 1, y + value[0] - 1, TILE_SIZE)
                            page.wait_for_timeout(10)
        page.wait_for_timeout(200)
        canvas_screenshot = canvas.screenshot()

    input("Press Enter to Close")
    cv2.destroyAllWindows()
    browser.close()
    log_file.close()
