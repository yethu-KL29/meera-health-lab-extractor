# Detailed run instructions

Use Python 3.11 or newer (tested 3.13), Git, internet access, and a Gemini API key with model access. Pillow 13 requires 3.11, even though the original starter needed only 3.10. Start by cloning the repository:

```sh
git clone https://github.com/yethu-KL29/meera-health-lab-extractor.git
cd meera-health-lab-extractor
```

## Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$geminiSecret = Read-Host "Gemini API key" -AsSecureString
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new("", $geminiSecret).Password
.\.venv\Scripts\python.exe extract.py reports/report_11.pdf
```

The key is entered at a hidden prompt. Calling the virtual environment's interpreter directly avoids changing PowerShell's script execution policy. For subsequent commands below, replace `python` with `.\.venv\Scripts\python.exe` if you have not activated the environment. To select the other tested model, run `$env:GEMINI_MODEL = 'gemini-3.5-flash-lite'` before starting Python.

## macOS and Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Set `GEMINI_API_KEY` through your normal local secret/environment setup. In **Bash** (start `bash` first if your shell is zsh), you can use a hidden prompt:

```bash
read -r -s -p "Gemini API key: " GEMINI_API_KEY
printf '\n'
export GEMINI_API_KEY
python extract.py reports/report_11.pdf
```

## Credentials and smoke test

Configure `GEMINI_API_KEY` through your normal local secret/environment setup. Never put credentials into tracked files or command history. The evaluator additionally supports an ignored `.env` with `GEMINI_API_KEY=...`; the extraction entry point reads environment variables only. A secure one-report smoke test prompts without saving the key:

```sh
python -c "import getpass, os, subprocess, sys; os.environ['GEMINI_API_KEY']=getpass.getpass('Gemini API key: '); sys.exit(subprocess.call([sys.executable, 'extract.py', 'reports/report_01.pdf']))"
```

## Evaluation and checks

With the environment configured, the first command extracts one report, the second calls the model for all 12, and the third rescores those saved outputs with audited labels. The last two commands run offline without an API key:

```sh
python extract.py reports/report_11.pdf
python scripts/evaluate.py --implementation extract --output results/new-run
python scripts/evaluate.py --output results/new-run --score-only --labels gold_audited
python scripts/report_results.py
python -m unittest discover -v
```

The evaluator runs all 12 supplied reports unless `--reports report_01 report_11` selects a subset. Run directories must not already exist. Scoring-only commands never call a model. `scripts/report_results.py` reproduces the saved historical and Pydantic comparisons offline; to compare your own runs use `python scripts/report_results.py new-run another-run`. This overwrites only the derived `results/comparison.json`.

For the unchanged baseline, install Poppler and put `pdftoppm` on PATH (`brew install poppler` on macOS, `sudo apt-get install poppler-utils` on Debian/Ubuntu; Windows binaries: https://github.com/oschwartz10612/poppler-windows). We used ignored `.tools/poppler/`. Final extraction uses PDFium from pip and requires no Poppler.

Baseline defaults to its original model; explicitly select the comparison model. In PowerShell:

```powershell
$env:GEMINI_MODEL = 'gemini-3.1-flash-lite'
python scripts/evaluate.py --implementation baseline --output results/new-baseline
python scripts/evaluate.py --implementation extract --output results/new-final
$env:EXTRACT_DPI = '300'
python scripts/evaluate.py --implementation extract --output results/new-300dpi
Remove-Item Env:EXTRACT_DPI
$env:GEMINI_MODEL = 'gemini-3.5-flash-lite'
python scripts/evaluate.py --implementation baseline --output results/new-baseline-35
python scripts/evaluate.py --implementation extract --output results/new-final-35
```

In POSIX shells use e.g. `GEMINI_MODEL=gemini-3.5-flash-lite python scripts/evaluate.py --implementation extract --output results/new-final-35`. Rendering resolution supports 60–300 DPI. Leave it unset for the default 150. No sample-specific answers or labels are read by extraction.

Exit behavior: valid JSON on successful stdout; failures on stderr with nonzero exit, never a fabricated empty result. Model requests have a 60-second timeout and one retry after two seconds for HTTP 429/500/502/503/504. Auth errors, malformed/truncated model output, and local input errors do not trigger retries. Quotas can still prevent completion; retain failed runs instead of silently substituting cached successes. Estimated cost excludes charges not returned in usage metadata and is not account billing.
