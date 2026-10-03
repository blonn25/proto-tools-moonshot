"""Collect campaign-only SLURM accounting and verify actual GPU concurrency."""

import argparse
import csv
import getpass
import io
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from execution_provenance import revisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--since', default='2026-10-02')
    parser.add_argument('--output', type=Path, default=Path('data/corehpc/protease_design/job_inventory.json'))
    parser.add_argument('--include-jobs', nargs='*', default=[], help='Also retain known jobs cancelled before they started.')
    args = parser.parse_args()
    fields = ['JobIDRaw', 'JobName', 'State', 'ExitCode', 'ElapsedRaw', 'Start', 'End', 'AllocTRES', 'ReqTRES', 'NodeList']
    command = ['sacct', '-n', '-P', '-X', '-u', getpass.getuser(), '--starttime', args.since,
               '--format', ','.join(fields)]
    raw = subprocess.check_output(command, env=dict(os.environ, TZ='UTC'), text=True)
    commands = [command]
    if args.include_jobs:
        extra = ['sacct', '-n', '-P', '-X', '-u', getpass.getuser(), '--jobs', ','.join(args.include_jobs),
                 '--format', ','.join(fields)]
        raw += subprocess.check_output(extra, env=dict(os.environ, TZ='UTC'), text=True)
        commands.append(extra)
    records, events, seen = [], [], set()
    now = datetime.now(timezone.utc)
    for row in csv.reader(io.StringIO(raw), delimiter='|'):
        if not row:
            continue
        record = dict(zip(fields, row))
        if not record['JobName'].startswith('protease-') or record['JobIDRaw'] in seen:
            continue
        seen.add(record['JobIDRaw'])
        matches = re.findall(r'(?:^|,)gres/gpu=(\d+)(?:,|$)', record['AllocTRES'])
        gpus = int(matches[0]) if matches else 0
        record['allocated_gpus'] = gpus
        records.append(record)
        if gpus and record['Start'] not in ('Unknown', 'None', ''):
            start = datetime.fromisoformat(record['Start']).replace(tzinfo=timezone.utc)
            end = (datetime.fromisoformat(record['End']).replace(tzinfo=timezone.utc)
                   if record['End'] not in ('Unknown', 'None', '') else now)
            events += [(start, gpus), (end, -gpus)]
    concurrent = maximum = 0
    for _, delta in sorted(events, key=lambda e: (e[0], e[1])):
        concurrent += delta
        maximum = max(maximum, concurrent)
    result = {**revisions(), 'collected_utc': now.isoformat(), 'time_zone_requested': 'UTC',
              'commands': commands, 'maximum_observed_concurrent_allocated_gpus': maximum,
              'allocated_gpu_seconds': sum(int(r['ElapsedRaw']) * r['allocated_gpus'] for r in records),
              'records': records}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    if maximum > 2:
        raise RuntimeError(f'Campaign exceeded the GPU cap: {maximum}')


if __name__ == '__main__':
    main()
