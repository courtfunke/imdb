#!/usr/bin/env python3
"""
Build movies.js for Cast Call from IMDb's official non-commercial datasets
(https://developer.imdb.com/non-commercial-datasets/).

Default: the 10,000 feature films with the most IMDb votes (the most recognizable
films, which keeps the game guessable). Use --sort rating to rank by IMDb rating
instead (among films with at least --min-votes votes).

Usage:
    python tools/build_movies.py                 # writes ./movies.js
    python tools/build_movies.py --count 5000 --sort rating --min-votes 25000

Downloads ~1.5 GB of compressed files into ./imdb-data (cached between runs).
Standard library only; no pip installs needed.
"""
import argparse, gzip, json, os, sys, urllib.request

BASE = "https://datasets.imdbws.com/"
FILES = ["title.ratings.tsv.gz", "title.basics.tsv.gz", "title.crew.tsv.gz",
         "title.principals.tsv.gz", "name.basics.tsv.gz"]


def download(data_dir, name, refresh):
    path = os.path.join(data_dir, name)
    if os.path.exists(path) and not refresh:
        return path
    print(f"Downloading {name} ...", flush=True)
    tmp = path + ".part"
    req = urllib.request.Request(BASE + name, headers={"User-Agent": "cast-call-builder"})
    with urllib.request.urlopen(req) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    os.replace(tmp, path)
    return path


def rows(path):
    """Yield split rows from a gzipped IMDb TSV, skipping the header."""
    with gzip.open(path, "rt", encoding="utf-8", newline="\n") as f:
        next(f)
        for line in f:
            yield line.rstrip("\n").split("\t")


def nul(v):
    return None if v == "\\N" else v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--count", type=int, default=10000, help="number of movies (default 10000)")
    ap.add_argument("--sort", choices=["votes", "rating"], default="votes")
    ap.add_argument("--min-votes", type=int, default=None,
                    help="minimum votes (default 5000 for votes, 25000 for rating)")
    ap.add_argument("--cast", type=int, default=10, help="actors per movie (default 10)")
    ap.add_argument("--min-cast", type=int, default=4, help="skip movies with fewer listed actors")
    ap.add_argument("--data-dir", default="imdb-data")
    ap.add_argument("--out", default="movies.js")
    ap.add_argument("--refresh", action="store_true", help="re-download the IMDb files")
    a = ap.parse_args()
    min_votes = a.min_votes if a.min_votes is not None else (5000 if a.sort == "votes" else 25000)

    os.makedirs(a.data_dir, exist_ok=True)
    p = {n: download(a.data_dir, n, a.refresh) for n in FILES}

    print("Reading ratings ...", flush=True)
    ratings = {}
    for r in rows(p["title.ratings.tsv.gz"]):
        votes = int(r[2])
        if votes >= min_votes:
            ratings[r[0]] = (float(r[1]), votes)

    print("Reading titles ...", flush=True)
    movies = {}
    for r in rows(p["title.basics.tsv.gz"]):
        tid = r[0]
        if tid not in ratings or r[1] != "movie" or r[4] == "1" or not nul(r[5]):
            continue
        movies[tid] = {"id": tid, "t": r[2], "o": r[3], "y": int(r[5]),
                       "g": [g for g in (nul(r[8]) or "").split(",") if g]}

    key = (lambda t: (ratings[t][1], ratings[t][0])) if a.sort == "votes" \
        else (lambda t: (ratings[t][0], ratings[t][1]))
    # take extra so that movies dropped for thin cast lists can be replaced
    ranked = sorted(movies, key=key, reverse=True)[: int(a.count * 1.15) + 200]
    chosen = set(ranked)

    print("Reading directors ...", flush=True)
    directors = {}
    for r in rows(p["title.crew.tsv.gz"]):
        if r[0] in chosen and nul(r[1]):
            directors[r[0]] = r[1].split(",")

    print("Reading cast (largest file, takes a few minutes) ...", flush=True)
    cast = {}
    for r in rows(p["title.principals.tsv.gz"]):
        if r[0] in chosen and r[3] in ("actor", "actress"):
            cast.setdefault(r[0], []).append((int(r[1]), r[2]))

    needed = {n for ds in directors.values() for n in ds}
    for tid, lst in cast.items():
        lst.sort()
        cast[tid] = [n for _, n in lst[: a.cast]]
        needed.update(cast[tid])

    print("Reading names ...", flush=True)
    names = {}
    for r in rows(p["name.basics.tsv.gz"]):
        if r[0] in needed:
            names[r[0]] = r[1]

    out = []
    for tid in ranked:
        actors = [names[n] for n in cast.get(tid, []) if n in names]
        if len(actors) < a.min_cast:
            continue
        m = movies[tid]
        entry = {"id": tid, "t": m["t"], "y": m["y"], "g": m["g"],
                 "d": [names[n] for n in directors.get(tid, []) if n in names], "c": actors}
        if m["o"] and m["o"] != m["t"]:
            entry["o"] = m["o"]
        out.append(entry)
        if len(out) >= a.count:
            break

    with open(a.out, "w", encoding="utf-8") as f:
        f.write("// Generated by tools/build_movies.py from IMDb non-commercial datasets.\n")
        f.write(f"// {len(out)} movies, ranked by {a.sort} (min {min_votes} votes). Personal, non-commercial use only.\n")
        f.write("window.MOVIES = [\n")
        f.write(",\n".join(json.dumps(m, ensure_ascii=False, separators=(",", ":")) for m in out))
        f.write("\n];\n")
    print(f"Wrote {len(out)} movies to {a.out}")
    if len(out) < a.count:
        print(f"Note: only {len(out)} films met the criteria; lower --min-votes for more.", file=sys.stderr)


if __name__ == "__main__":
    main()
