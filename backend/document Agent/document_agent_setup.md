# Document Agent — Setup Guide

## 1. Python dependencies

```bash
pip install pymupdf pytesseract pillow langchain-core langchain-text-splitters \
            langchain-community sentence-transformers faiss-cpu fastapi
```

## 2. Tesseract OCR (required for scanned PDFs)

`pytesseract` (installed above) is just a Python wrapper — it calls out to
the actual **Tesseract OCR engine**, which is a separate program you must
install yourself. Without it, OCR is skipped automatically (you'll see a
warning in the output, not a crash) and only text-based PDF pages will be
extracted.

### Windows
1. Download the installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Run it. The default install path is `C:\Program Files\Tesseract-OCR\`
   — the code auto-detects this, so no extra config needed.
3. If you installed somewhere else, set an environment variable before
   running the agent:
   ```powershell
   setx TESSERACT_CMD "C:\path\to\your\tesseract.exe"
   ```

### macOS
```bash
brew install tesseract
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update && sudo apt-get install tesseract-ocr
```

### Verify it worked (any OS)
```bash
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```
This should print a version number (e.g. `5.3.0`). If it errors with
`TesseractNotFoundError`, Tesseract isn't installed or isn't on PATH —
recheck the steps above for your OS.

## 3. Running the agent

```bash
python document_agent.py financial_documentation.pdf "Company Name"
```
