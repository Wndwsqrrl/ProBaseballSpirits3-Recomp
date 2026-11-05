"""Summarize a selected, comparable section of the opt-in frame profile."""
import argparse
import csv
import json
from pathlib import Path
import statistics

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('csv',type=Path)
parser.add_argument('--start-seconds',type=float,default=10,help='Skip startup/warmup; default 10 seconds')
parser.add_argument('--end-seconds',type=float)
args=parser.parse_args()
with args.csv.open(newline='') as stream:
    rows=[{key:float(value) for key,value in row.items()} for row in csv.DictReader(stream)]
rows=[row for row in rows if row['elapsed_ms']>=args.start_seconds*1000 and
      (args.end_seconds is None or row['elapsed_ms']<=args.end_seconds*1000)]
if not rows:parser.error('No samples in the selected time range')
def percentile(values,p):
    ordered=sorted(values)
    at=(len(ordered)-1)*p
    low=int(at);high=min(low+1,len(ordered)-1)
    return ordered[low]+(ordered[high]-ordered[low])*(at-low)
intervals=[row['frame_interval_ms'] for row in rows]
overhead=[row['text_hook_cpu_ms'] for row in rows]
if any(value<=0 for value in intervals):parser.error('Non-positive frame interval')
print(json.dumps(dict(samples=len(rows),
    submitted_fps=1000/statistics.mean(intervals),
    median_frame_ms=statistics.median(intervals),
    p95_frame_ms=percentile(intervals,.95),p99_frame_ms=percentile(intervals,.99),
    mean_text_hook_cpu_ms=statistics.mean(overhead),
    p95_text_hook_cpu_ms=percentile(overhead,.95),
    note='Submission cadence, not GPU completion. Compare the same scene, settings, cache state and power mode. No long intervals are discarded.'),indent=2))
