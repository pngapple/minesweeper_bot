# Minesweeper Bot

A Python-based automation bot that plays Google Minesweeper by analyzing the game board in real time.
It uses Playwright for browser control, OpenCV + SSIM for tile recognition, and a simple logical solver to automatically reveal safe tiles and flag mines.

Features:

- Automatically loads Google Minesweeper in Chromium
- Captures the game board as screenshots
- Detects numbers and tile states using structural similarity (SSIM) and HSV color thresholds
- Applies basic Minesweeper solving rules
- Simulates mouse clicks on safe tiles
- Flags mines internally to avoid mistakes
- Debugging tools to save tile crops for success/failure cases

Demo:

- [Watch demo video](https://youtu.be/xjz0Xv_d9kg)

Installation:

1. Clone the repo:
   git clone https://github.com/yourusername/minesweeper-bot.git
   cd minesweeper-bot

2. Install dependencies:
   pip install -r requirements.txt

   Example requirements.txt:
   playwright
   pillow
   opencv-python
   numpy
   scikit-image

3. Install Playwright browsers:
   playwright install

Usage:

- Run the bot with:
  python bot.py

Steps:

1. The bot launches Google Minesweeper in Chromium.
2. Solve the CAPTCHA manually if prompted.
3. The bot clicks Play automatically (or wait for you to do so).
4. The game board is scanned, and the solver begins playing.
5. Detected mines are flagged internally, and safe tiles are clicked.

File Structure:
minesweeper-bot/
│── bot.py # Main bot script
│── templates/ # Template images for numbers and tiles
│── debug_tiles/ # Auto-saved debug crops of recognized tiles
│── requirements.txt # Dependencies
│── README.md # Project documentation

Known Issues / Improvements:

- Some numbers (e.g., 2 vs 3) may still be misclassified depending on tile resolution
- HSV thresholds for unrevealed/empty tiles may vary by theme or lighting
- Solver currently supports basic deterministic rules (no probability-based solving yet)
- Templates for numbers 1–5 are included — extend to 6–8 for better accuracy

License:
MIT License

Copyright (c) 2025 Max Xu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Contributing:

- Pull requests, improvements, and better solvers are welcome.
- If you create new templates, add advanced solving strategies, or improve recognition, feel free to open a PR.
