import cv2
import os

# ---------------------------
# Config
# ---------------------------
TILE_SIZE = 30  # adjust if needed
ROWS = 14      # set to the number of rows on your screenshot
COLS = 18      # set to the number of columns
SCREENSHOT_PATH = "board.png"  # your Minesweeper screenshot
TEMPLATE_DIR = "templates"     # folder to save labeled tiles

os.makedirs(TEMPLATE_DIR, exist_ok=True)

# ---------------------------
# Extract tiles from screenshot
# ---------------------------
image = cv2.imread(SCREENSHOT_PATH)
tiles = []

for r in range(ROWS):
    row_tiles = []
    for c in range(COLS):
        x = c * TILE_SIZE
        y = r * TILE_SIZE
        tile_img = image[y:y+TILE_SIZE, x:x+TILE_SIZE]
        row_tiles.append(tile_img)
    tiles.append(row_tiles)

# ---------------------------
# Interactive labeling
# ---------------------------
for r, row in enumerate(tiles):
    for c, tile in enumerate(row):
        cv2.imshow("Tile", tile)
        cv2.waitKey(1)  # allow window to render

        # Ask user to label the tile
        label = input(
            f"Tile at row {r}, col {c} - enter value (-1=unrevealed, 0=empty, 1-8 for numbers): "
        ).strip()

        # Optional: also ask for background type for empty/unrevealed
        bg_type = ""
        if label in ["0", "-1"]:
            bg_type = input("Enter background type ('light' or 'dark'): ").strip()

        # Construct filenames
        if bg_type:
            filename = f"{label}_{bg_type}.png"
        else:
            filename = f"{label}.png"

        save_path = os.path.join(TEMPLATE_DIR, filename)
        cv2.imwrite(save_path, tile)

        # If it's a number tile, save grayscale edge template
        if label.isdigit() and int(label) >= 1 and int(label) <= 8:
            gray_tile = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
            edges_tile = cv2.Canny(gray_tile, 50, 150)
            edge_filename = f"{label}_edges.png"
            cv2.imwrite(os.path.join(TEMPLATE_DIR, edge_filename), edges_tile)

        cv2.destroyAllWindows()

print("✅ All tiles labeled and saved with edges for numbers!")
