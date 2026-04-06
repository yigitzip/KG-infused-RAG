#!/usr/bin/env python3
"""Metrics for Turkish cinema seeds: P495=Q43 ∧ P31=Q11424. See README."""

from __future__ import annotations

import argparse
from collections import defaultdict


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--triplets", required=True)
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    p495, is_film = set(), set()
    with open(args.triplets, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            h, r, t = parts
            if r == "P495" and t == "Q43":
                p495.add(h)
            elif r == "P31" and t == "Q11424":
                is_film.add(h)

    seeds = p495 & is_film
    deg = defaultdict(int)
    with open(args.triplets, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            h, _, _ = parts
            if h in seeds:
                deg[h] += 1

    ranked = sorted(seeds, key=lambda x: -deg[x])
    top = ranked[: args.top]
    out_edges: dict[str, list[tuple[str, str]]] = {s: [] for s in top}
    neighbor: set[str] = set()
    with open(args.triplets, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            h, r, t = parts
            if h in out_edges:
                out_edges[h].append((r, t))
                neighbor.add(t)

    out2: dict[str, list[tuple[str, str]]] = defaultdict(list)
    with open(args.triplets, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            h, r, t = parts
            if h in neighbor:
                out2[h].append((r, t))

    two_hop = sum(len(out2.get(b, [])) for s in top for r1, b in out_edges[s])
    print("Domain: P495=Q43 ∧ P31=Q11424 (Turkish-origin films)")
    print(f"Total seeds: {len(seeds)}")
    for s in top:
        rels = {e[0] for e in out_edges[s]}
        print(f"  {s}  triples={len(out_edges[s])}  distinct_P={len(rels)}")
    print(f"2-hop paths from top-{args.top} seeds: {two_hop}")


if __name__ == "__main__":
    main()
