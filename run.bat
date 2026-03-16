@echo off
echo ============================================================
echo  Multi-Source Scraping Engine - Setup ^& Run
echo ============================================================

echo.
echo [1/2] Installing dependencies...
pip install newspaper3k readability-lxml youtube-transcript-api yt-dlp biopython langdetect rake-nltk "pydantic>=2.0" requests lxml nltk tqdm

echo.
echo [2/2] Running the scraper...
python main.py

echo.
echo Done! Check the scraped_data\ folder for output files.
pause
