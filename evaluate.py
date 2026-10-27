"""Run: python evaluate.py --implementation baseline --output results/baseline.

Scoring is deliberately independent of extraction; --score-only never calls a model.
"""
import argparse
import hashlib
import importlib
import io
import json
import os
import re
import statistics
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from jsonschema import validate

ROOT = Path(__file__).resolve().parent
FIELDS = ('value', 'unit', 'reference_range')


def load_environment():
    """Optional ignored local file; existing environment values take precedence."""
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('\"\''))


def text(value):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', str(value)).lower()).strip()


def name(value):
    return re.sub(r'[^a-z0-9]', '', text(value))


# Fixed before extraction changes. Explicit synonyms only; no fuzzy name matching.
GROUPS = [
    'Haemoglobin|Hemoglobin|Hemoglobin (Hb)|Hb',
    'Total RBC Count|RBC Count|Red Blood Cell Count',
    'Packed Cell Volume (PCV)|Hematocrit|PCV',
    'MCV|Mean Corpuscular Volume', 'MCH|Mean Corpuscular Hb|Mean Corpuscular Hemoglobin',
    'MCHC|Mean Corp. Hb Conc.|Mean Corpuscular Hemoglobin Concentration',
    'RDW|RDW-CV|Red Cell Distribution Width',
    'Total WBC Count|Total Leucocyte Count|WBC Count|Total Leukocyte Count',
    'Platelet Count|Platelets',
    'Cholesterol - Total|S. Cholesterol|Total Cholesterol',
    'Serum Triglycerides|TG|Triglycerides', 'Cholesterol - HDL|HDL-C|HDL Cholesterol',
    'Cholesterol - LDL|LDL-C (Direct)|LDL Cholesterol|LDL-C',
    'Cholesterol - VLDL|VLDL|VLDL Cholesterol', 'TC/HDL Ratio|Chol/HDL|Total Cholesterol/HDL Ratio',
    'Aspartate Aminotransferase|AST|SGOT|AST (SGOT)',
    'Alanine Aminotransferase|ALT|SGPT|ALT (SGPT)',
    'ALP|Alkaline Phosphatase', 'Protein Total|Total Protein',
    'Serum Albumin|Albumin', 'Serum Globulin|Globulin',
    'T3|Triiodothyronine (T3)|Triiodothyronine', 'T4|Thyroxine (T4)|Thyroxine',
    'TSH (Ultrasensitive)|Thyroid Stimulating Hormone|TSH',
    'Vit D Total|25-Hydroxy Vitamin D|Vitamin D|Vitamin D Total',
    'Vit B12|Cyanocobalamin (B12)|Vitamin B12',
    'Glycated Hb|Glycosylated Haemoglobin (HbA1c)|HbA1c|Glycated Hemoglobin',
    'FBS|Glucose - Fasting|Fasting Blood Sugar|Fasting Glucose',
    'PPBS|Glucose - PP|Postprandial Blood Sugar|Postprandial Glucose',
    'Colour|Color', 'Clarity|Appearance', 'pH|Reaction (pH)',
    'Specific Gravity|Sp. Gravity', 'Sugar|Urine Glucose', 'Ketones|Ketone Bodies',
    'Leucocytes|Pus Cells (WBC)|Pus Cells', 'Erythrocytes|RBC',
    'Squamous Epithelial Cells|Epithelial Cells', 'Albumin/Globulin Ratio|A/G Ratio',
    'CRP|C-Reactive Protein', 'E.S.R. (Westergren)|ESR|Erythrocyte Sedimentation Rate',
    'Serum Uric Acid|Uric Acid', 'Sodium (Na+)|Sodium',
    'Potassium (K+)|Potassium', 'Chloride (Cl-)|Chloride',
]
ALIASES = {name(item): name(group.split('|')[0]) for group in GROUPS for item in group.split('|')}


def canonical_name(value):
    return ALIASES.get(name(value), name(value))


def normal(value, field):
    if value is None:
        return None
    result = text(value).replace('−', '-').replace('–', '-').replace('—', '-')
    result = result.replace('μ', 'u').replace('µ', 'u')
    if field == 'unit':
        return re.sub(r'\s+', '', result)
    # Numeric strings and numbers compare equally; preserve inequality operators.
    result = result.replace(',', '')
    pieces = re.split(r'([<>]=?|<=|>=|\s*-\s*)', result)
    normalized = []
    for piece in pieces:
        piece = piece.strip()
        try:
            number = Decimal(piece)
            normalized.append(format(number.normalize(), 'f') if number.is_finite() else piece)
        except InvalidOperation:
            normalized.append(piece)
    return ''.join(normalized)


def score(expected, actual):
    remaining = list(enumerate(actual))
    matched = full = 0
    correct = dict.fromkeys(FIELDS, 0)
    errors = []
    for row in expected:
        candidates = [(i, r) for i, r in remaining
                      if canonical_name(r['test_name']) == canonical_name(row['test_name'])]
        # Repeated test names are aligned by occurrence, never by the value being scored.
        if not candidates:
            errors.append({'test_name': row['test_name'], 'missing': True, 'expected': row})
            continue
        index, prediction = candidates[0]
        remaining = [(i, r) for i, r in remaining if i != index]
        matched += 1
        equal = {field: normal(row.get(field), field) == normal(prediction.get(field), field)
                 for field in FIELDS}
        for field in FIELDS:
            correct[field] += int(equal[field])
        full += int(all(equal.values()))
        if not all(equal.values()):
            errors.append({'test_name': row['test_name'], 'expected': row,
                           'actual': prediction, 'incorrect_fields': [k for k, v in equal.items() if not v]})
    return {'expected': len(expected), 'predicted': len(actual), 'matched': matched,
            'fully_correct': full, 'field_correct': correct, 'errors': errors,
            'extra_rows': [r for _, r in remaining]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--implementation', choices=('baseline', 'extract'), default='extract')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--labels', type=Path, default=ROOT / 'gold')
    parser.add_argument('--score-only', action='store_true')
    parser.add_argument('--reports', nargs='*', help='Optional report stems for smoke tests')
    args = parser.parse_args()
    load_environment()
    schema = json.loads((ROOT / 'schema.json').read_text())
    module = importlib.import_module(args.implementation)
    if not args.score_only:
        args.output.mkdir(parents=True, exist_ok=False)
        metadata = {'implementation': args.implementation, 'model': module.MODEL,
                    'started_utc': datetime.now(timezone.utc).isoformat(),
                    'source_sha256': hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
                    'scorer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    'dpi': module.DPI, 'temperature': 0, 'max_output_tokens': 16000,
                    'prompt': module.PROMPT,
                    'actual_spend_usd': None, 'note': 'Spend requires account billing verification.'}
        (args.output / 'run.json').write_text(json.dumps(metadata, indent=2))
    records = []
    for report in sorted((ROOT / 'reports').iterdir()):
        if args.reports and report.stem not in args.reports:
            continue
        path = args.output / (report.stem + '.json')
        if args.score_only:
            if not path.exists():
                continue
            record = json.loads(path.read_text(encoding='utf-8'))
        else:
            record = {'report': report.name, 'prediction': None, 'usage': [], 'error': None}
            original_open = urllib.request.urlopen

            def measured_open(*a, **kw):
                with original_open(*a, **kw) as response:
                    payload = response.read()
                data = json.loads(payload)
                record['usage'].append(data.get('usageMetadata', {}))
                return io.BytesIO(payload)

            started = time.perf_counter()
            urllib.request.urlopen = measured_open
            try:
                record['prediction'] = module.extract(report)
                validate(record['prediction'], schema)
            except Exception as error:
                # Avoid saving exception messages that might contain credentials or URLs.
                record['error'] = {'type': type(error).__name__,
                                   'http_status': getattr(error, 'code', None)}
                print(report.name, 'FAILED:', type(error).__name__, flush=True)
            finally:
                urllib.request.urlopen = original_open
                record['latency_seconds'] = round(time.perf_counter() - started, 3)
            path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding='utf-8')
        label = args.labels / (report.stem + '.json')
        if label.exists():
            expected = json.loads(label.read_text(encoding='utf-8'))['tests']
            record['score'] = score(expected, (record.get('prediction') or {}).get('tests', []))
        records.append(record)
        print(report.name, record.get('score', {}).get('fully_correct', 'unlabelled'),
              'correct rows;', record['latency_seconds'], 'seconds', flush=True)
    labelled = [r['score'] for r in records if 'score' in r]
    totals = {key: sum(r[key] for r in labelled)
              for key in ('expected', 'predicted', 'matched', 'fully_correct')}
    tp = totals['fully_correct']
    precision = tp / totals['predicted'] if totals['predicted'] else 0
    recall = tp / totals['expected'] if totals['expected'] else 0
    summary = {**totals, 'strict_row_precision': precision, 'strict_row_recall': recall,
               'strict_row_f1': 2 * precision * recall / (precision + recall) if precision + recall else 0,
               'field_accuracy': {f: sum(r['field_correct'][f] for r in labelled) / totals['expected']
                                  if totals['expected'] else 0 for f in FIELDS},
               'failed_reports': sum(r['error'] is not None for r in records),
               'median_latency_seconds': statistics.median(r['latency_seconds'] for r in records) if records else None,
               'reports': records}
    filename = 'evaluation.json' if args.labels.name == 'gold' else f'evaluation-{args.labels.name}.json'
    (args.output / filename).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'reports'}, indent=2))


if __name__ == '__main__':
    main()
