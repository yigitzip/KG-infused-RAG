#!/usr/bin/env python3
"""Undirected k-hop neighborhood from seed Q-ids → filtered TSV. See module docstring in repo README."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict


def expand_one_hop(path: str, nodes: set[str], chunk: int = 5_000_000) -> set[str]:
    out = set(nodes)
    n = 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            n += 1
            if n % chunk == 0:
                print(f"    scan lines: {n:,}", file=sys.stderr)
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            h, _, t = parts
            if h in nodes or t in nodes:
                out.add(h)
                out.add(t)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--triplets", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", action="append", default=[])
    ap.add_argument("--hops", type=int, default=2)
    args = ap.parse_args()

    seeds = set(args.seed if args.seed else ["Q43"])
    nodes = set(seeds)
    for hop in range(args.hops):
        print(f"Hop {hop + 1}/{args.hops} |nodes|={len(nodes):,}", file=sys.stderr)
        nodes = expand_one_hop(args.triplets, nodes)

    kept = 0
    with open(args.triplets, "r", encoding="utf-8", errors="replace") as fin, open(
        args.out, "w", encoding="utf-8", newline=""
    ) as fout:
        for line in fin:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            h, r, t = parts
            if h in nodes and t in nodes:
                fout.write(f"{h}\t{r}\t{t}\n")
                kept += 1
    print(f"Wrote {kept:,} triples → {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
