from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
import cv2
from io import BytesIO
import os

# ---------------------------
# Config
# ---------------------------
TEMPLATE_DIR = "templates"  # folder containing number and special tile templates
TILE_SIZE = 30  # approximate tile size (adjust if needed)
DEBUG_DIR = "debug_tiles"
DEBUG_LOG = "debug_log.txt"

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
for i in range(1, 5):  # adjust to 1-8 if needed
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

def detect_tile(tile_img, r=None, c=None):
    """
    Detect Minesweeper tile:
      -1: unrevealed
       0: empty revealed
       1-8: numbers
    """
    # 1. Edge detection for number templates
    gray_tile = cv2.cvtColor(tile_img, cv2.COLOR_BGR2GRAY)
    gray_tile = cv2.GaussianBlur(gray_tile, (3, 3), 0)
    edges_tile = cv2.Canny(gray_tile, 50, 150)
    h, w = edges_tile.shape

    edge_count = cv2.countNonZero(edges_tile)
    log(f"[Tile {r},{c}] Edge count: {edge_count}")

    min_edge_pixels = 20
    if edge_count > min_edge_pixels:
        best_num = None
        best_score = -1

        for num, template_edges in number_edges.items():
            resized_template = cv2.resize(template_edges, (w, h))
            res = cv2.matchTemplate(edges_tile, resized_template, cv2.TM_CCOEFF_NORMED)
            score = float(np.max(res))
            log(f"   Num {num} score: {score:.3f}")
            if score > best_score:
                best_score = score
                best_num = num

        if best_score > 0.25:
            log(f"✅ Matched number {best_num} with score {best_score:.3f}")
            if r is not None and c is not None:
                cv2.imwrite(f"{DEBUG_DIR}/success/num_r{r}_c{c}.png", tile_img)
            return best_num
        else:
            log(f"❌ No number match above threshold (best={best_score:.3f})")
            if r is not None and c is not None:
                cv2.imwrite(f"{DEBUG_DIR}/fail/fail_num_r{r}_c{c}.png", tile_img)
                cv2.imwrite(f"{DEBUG_DIR}/fail/fail_edges_r{r}_c{c}.png", edges_tile)
            return -2

    # 2. Check special tiles (color match)
    h_tile, w_tile = tile_img.shape[:2]
    for num in [-1, 0]:
        for bg in ["light", "dark"]:
            template = special_templates[f"{num}_{bg}"]
            resized_template = cv2.resize(template, (w_tile, h_tile))
            # Convert tile and template to same color format (BGR)
            res = cv2.matchTemplate(tile_img, resized_template, cv2.TM_CCOEFF_NORMED)
            score = float(np.max(res))
            log(f"   Special {num}_{bg} score: {score:.3f}")
            if score > 0.3:
                log(f"✅ Matched special {num}_{bg} with score {score:.3f}")
                if r is not None and c is not None:
                    cv2.imwrite(f"{DEBUG_DIR}/success/special_{num}_{bg}_r{r}_c{c}.png", tile_img)
                return num

    # 3. If all fails
    log(f"❌ Completely failed to detect tile {r},{c}")
    if r is not None and c is not None:
        cv2.imwrite(f"{DEBUG_DIR}/fail/fail_other_r{r}_c{c}.png", tile_img)
        cv2.imwrite(f"{DEBUG_DIR}/fail/fail_other_edges_r{r}_c{c}.png", edges_tile)
    return -2

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

    # Convert to OpenCV
    image = Image.open(BytesIO(canvas_screenshot))
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    tiles = extract_tiles(opencv_image, rows, cols)

    # Optionally display board
    cv2.imshow("Board", opencv_image)
    log("Press any key in the OpenCV window to close...")
    cv2.waitKey(0)

    # Detect board numbers
    board_numbers = []
    for r in range(rows):
        row_numbers = []
        for c in range(cols):
            num = detect_tile(tiles[r][c], r, c)
            if num == -2:
                log(f"failed to detect: row {r}, column {c}")
            row_numbers.append(num)
        board_numbers.append(row_numbers)

    # Print detected board
    log("Detected board:")
    for row in board_numbers:
        log(str(row))

    cv2.destroyAllWindows()
    browser.close()
    log_file.close()
