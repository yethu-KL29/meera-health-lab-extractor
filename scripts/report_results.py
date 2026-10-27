"""Reproduce original/audited scores and list-price estimates without API calls."""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate import FIELDS, score

RATES = {'gemini-3.1-flash-lite': (0.25, 1.50), 'gemini-3.5-flash-lite': (0.30, 2.50)}


def summarize(folder):
    metadata = json.loads((folder / 'run.json').read_text(encoding='utf-8'))
    records = [json.loads(path.read_text(encoding='utf-8')) for path in sorted(folder.glob('report_*.json'))]
    results = {}
    for labels in ['gold', 'gold_audited']:
        scores = []
        for record in records:
            label = ROOT / labels / (Path(record['report']).stem + '.json')
            if label.exists():
                expected = json.loads(label.read_text(encoding='utf-8'))['tests']
                actual = (record.get('prediction') or {}).get('tests', [])
                scores.append({'report': record['report'], **score(expected, actual)})
        total = {key: sum(s[key] for s in scores)
                 for key in ['expected', 'predicted', 'matched', 'fully_correct']}
        denom = total['expected'] + total['predicted']
        results[labels] = {**total, 'strict_row_f1': 2 * total['fully_correct'] / denom if denom else 0,
                          'strict_row_precision': total['fully_correct'] / total['predicted'] if total['predicted'] else 0,
                          'strict_row_recall': total['fully_correct'] / total['expected'] if total['expected'] else 0,
                          'field_accuracy': {f: sum(s['field_correct'][f] for s in scores) / total['expected']
                                             if total['expected'] else 0 for f in FIELDS},
                          'per_report': scores}
    for record in records:
        usages = record.get('usage', [])
        rates = RATES.get(metadata['model'])
        if rates and usages and all('promptTokenCount' in u and 'candidatesTokenCount' in u for u in usages):
            record['estimated_list_cost_usd'] = sum(
                (u['promptTokenCount'] * rates[0] + (u['candidatesTokenCount'] + u.get('thoughtsTokenCount', 0)) * rates[1]) / 1e6
                for u in usages)
        else:
            record['estimated_list_cost_usd'] = None
    costs = [r['estimated_list_cost_usd'] for r in records]
    results.update(model=metadata['model'], report_count=len(records),
                   failed_reports=sum(r.get('error') is not None for r in records),
                   median_latency_seconds=statistics.median(r['latency_seconds'] for r in records),
                   mean_latency_seconds=statistics.mean(r['latency_seconds'] for r in records),
                   mean_estimated_list_cost_usd=statistics.mean(costs) if all(c is not None for c in costs) else None,
                   actual_spend_usd=None,
                   per_report_usage=[{'report': r['report'], 'latency_seconds': r['latency_seconds'],
                                      'estimated_list_cost_usd': r['estimated_list_cost_usd'],
                                      'usage': r['usage'], 'error': r['error']} for r in records])
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', nargs='*', default=['baseline-flash-lite', 'final-verified', 'experiment-300dpi',
                                                 'baseline-35-flash-lite', 'final-35-flash-lite',
                                                 'final-pydantic-31', 'final-pydantic-35'])
    args = parser.parse_args()
    comparison = {run: summarize(ROOT / 'results' / run) for run in args.runs}
    (ROOT / 'results' / 'comparison.json').write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding='utf-8')
    print('| Run | Original F1 | Audited F1 | Median seconds | Mean list USD/report | Failed |')
    print('|---|---:|---:|---:|---:|---:|')
    for run, data in comparison.items():
        cost = data['mean_estimated_list_cost_usd']
        cost_text = f'{cost:.6f}' if cost is not None else 'unknown'
        print(f"| {run} | {data['gold']['strict_row_f1']:.2%} | {data['gold_audited']['strict_row_f1']:.2%} | "
              f"{data['median_latency_seconds']:.2f} | {cost_text} | {data['failed_reports']} |")


if __name__ == '__main__':
    main()
