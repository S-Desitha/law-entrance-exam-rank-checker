# Law Entrance Exam Rank Checker (HTML + Python)

This workspace contains two friendly apps to check merit ranks from an entrance exam results sheet.

Files:
- `rank_checker.html` — Standalone attractive HTML app (already created). Open it in any browser.
- `streamlit_rank_checker.py` — Python Streamlit app (this adds file upload/path support and richer visuals).

Quick start (Python / Streamlit):

1. Create a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run Streamlit app:

```bash
streamlit run streamlit_rank_checker.py
```

Usage:
- The app automatically scans the current directory for year subfolders (e.g., `2021/`, `2022/`).
- Select the year from the dropdown to load that year's results.
- Enter Sub 01 and Sub 02 marks and press "Check Rank" to see rank, percentile, and comparisons.
- Year folders should contain CSV or PDF files with results (columns: `serial, sub01, sub02, total, rank`).

Windows executable options:

1. Run from Python (recommended if you can install Python on the laptop):
   - Install Python 3.10 or 3.11 for Windows and add it to PATH.
   - Open a command prompt in this project folder.
   - Run `python -m pip install -r requirements.txt`.
   - Run `streamlit run streamlit_rank_checker.py`.

2. Build a Windows `.exe` using PyInstaller:
   - Install PyInstaller in the same environment: `python -m pip install pyinstaller`.
   - From the project folder, run:
     ```bash
     pyinstaller --onefile --name LawCollegeRankChecker streamlit_rank_checker.py
     ```
   - The executable will be created in `dist\LawCollegeRankChecker.exe`.
   - Copy the `dist\LawCollegeRankChecker.exe` file to a folder that also contains the year subfolders (for example, `2021\`).
   - Run the `.exe`; it should start the Streamlit app and open the browser.

Notes:
- The app still needs the year folders (e.g. `2021/`) next to the executable so it can find the result files.
- If PyInstaller misses a package, install the missing module or use the Python-run option instead.

Windows batch launcher:
- You can also run `run_rank_checker.bat` from the project folder on Windows.
- This installs requirements and launches the Streamlit app in your browser.

Folder structure:
```
/media/sathira/Education2/Nangi Law/
  2021/
    Law_College_Entrance_Exam_2021_Merit_List(Merit List Data).csv
  2022/
    results.csv
```

Notes:
- PDF parsing uses simple heuristics and may not always extract a clean table — CSV is more reliable.
- The HTML file remains available for an offline, offline-friendly UI experience.

If you want, I can:
- Add an installer/executable (PyInstaller) so your sister can double-click an app.
- Improve PDF parsing for your exact PDF layout if you upload a sample.
