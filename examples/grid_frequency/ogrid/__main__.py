#!/usr/bin/env python3
"""CLI entry point for O-Grid."""

import argparse
import json
import sys
import time
from collections import Counter

from ogrid import load_frequency_csv, classify_stream


def cmd_classify(args):
    print(f"Loading: {args.input}", file=sys.stderr)
    freq = load_frequency_csv(args.input)
    print(f"Loaded {len(freq):,} valid points", file=sys.stderr)

    t0 = time.time()
    results = classify_stream(
        freq,
        window=args.window,
        stride=args.stride,
        segment_duration=args.segment,
        H_threshold=args.H_threshold,
        H_v3_threshold=args.H_v3_threshold,
        freq_std_threshold=args.freq_std_threshold,
    )
    elapsed = time.time() - t0
    print(f"Classified {len(results)} segments in {elapsed:.1f}s", file=sys.stderr)

    counts = Counter(r["label"] for r in results)
    print(f"Distribution: {dict(counts)}", file=sys.stderr)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"{'Start':>10s} {'End':>10s} {'Label':>22s} {'Conf':>6s} {'H':>8s} {'H_v3':>6s} {'f_std':>8s}")
        print("-" * 80)
        for r in results:
            print(f"{r['start_s']:>10d} {r['end_s']:>10d} {r['label']:>22s} "
                  f"{r['confidence']:>6s} {r['H']:>8.1f} {r['H_v3']:>6.2f} {r['freq_std']:>8.1f}")


def main():
    parser = argparse.ArgumentParser(
        description="Ô Grid Frequency Diagnostic Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    cl = subparsers.add_parser("classify", help="Classify frequency CSV")
    cl.add_argument("--input", "-i", required=True, help="CSV of frequency values (mHz)")
    cl.add_argument("--window", "-w", type=int, default=100)
    cl.add_argument("--stride", "-s", type=int, default=50)
    cl.add_argument("--segment", type=int, default=3600)
    cl.add_argument("--H-threshold", type=float, default=10.0)
    cl.add_argument("--H-v3-threshold", type=float, default=1.5)
    cl.add_argument("--freq-std-threshold", type=float, default=22.0)
    cl.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.command == "classify":
        cmd_classify(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
