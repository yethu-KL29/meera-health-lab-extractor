"""Extract source-faithful lab rows: python extract.py <PDF/JPG/PNG>.

Python 3.11+, pip install -r requirements.txt; set GEMINI_API_KEY.
Successful stdout contains only schema-valid JSON. Errors use stderr/nonzero exit.
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from pydantic import ValidationError

from lab_extractor.documents import load_pages
from lab_extractor.schemas import LabReport

MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.1-flash-lite')
DPI = int(os.environ.get('EXTRACT_DPI', '150'))
ROOT = Path(__file__).resolve().parents[1]
SCHEMA = LabReport.model_json_schema()

PROMPT = (ROOT / 'prompts' / 'final.txt').read_text(encoding='utf-8')


def parse_response(response: dict) -> dict:
    candidates = response.get('candidates') or []
    if not candidates or candidates[0].get('finishReason') != 'STOP':
        raise RuntimeError('Model response blocked, incomplete, or empty; no extraction emitted.')
    text = ''.join(p.get('text', '') for p in candidates[0].get('content', {}).get('parts', [])
                   if not p.get('thought'))
    try:
        result = LabReport.model_validate_json(text).model_dump()
        # Also reject non-finite values inside otherwise permitted extra fields.
        json.dumps(result, allow_nan=False)
        return result
    except (ValueError, ValidationError, TypeError):
        raise RuntimeError('Model output is not valid lab-result JSON; no extraction emitted.') from None


def extract(path: Path) -> dict:
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('Set GEMINI_API_KEY in your environment; see README.md.')
    if not 60 <= DPI <= 300:
        raise RuntimeError('EXTRACT_DPI must be between 60 and 300.')
    body = {'contents': [{'role': 'user', 'parts': [{'text': PROMPT}, *load_pages(path, DPI)]}],
            'generationConfig': {'temperature': 0, 'maxOutputTokens': 16000,
                                 'responseMimeType': 'application/json',
                                 'responseJsonSchema': SCHEMA}}
    request = urllib.request.Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent',
        data=json.dumps(body).encode(),
        headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return parse_response(json.load(response))
        except urllib.error.HTTPError as error:
            if attempt == 0 and error.code in (429, 500, 502, 503, 504):
                time.sleep(2)
                continue
            raise RuntimeError(f'Gemini HTTP {error.code}; check model access, key, or quota.') from None
        except (urllib.error.URLError, TimeoutError):
            raise RuntimeError('Gemini connection failed or timed out; check network and retry.') from None
        except ValueError:
            raise RuntimeError('Gemini returned an invalid JSON response.') from None
