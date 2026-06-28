#!/usr/bin/env python3
"""
apple_music_similar.py — "songs like this one" for Apple Music, computed from
the audio-feature numbers apple_music_mood.py stored in each song's Comments.

100% OFFLINE: no Spotify, no ReccoBeats, no network, no rate limit. It reads the
cached feature vectors, measures how close every library song is to the song(s)
you have SELECTED, and builds a playlist of the closest matches.

Because it uses YOUR stored numbers (not Apple's model), it works for regional
catalogs (Tamil, etc.) that Apple's recommender is weak on.

------------------------------------------------------------------------------
PREREQUISITE
------------------------------------------------------------------------------
Tag your library first with `apple_music_mood.py` so each song's Comments hold
its feature numbers. Songs without cached numbers are ignored here.

------------------------------------------------------------------------------
USAGE
------------------------------------------------------------------------------
  1. In Music, SELECT one or more "seed" songs (the vibe you want more of).
  2. Run:
       python3 apple_music_similar.py                  # top 25 -> a playlist
       python3 apple_music_similar.py --count 40       # more results
       python3 apple_music_similar.py --same-language  # only the seed's language
       python3 apple_music_similar.py --dry-run        # just print, no playlist
       python3 apple_music_similar.py --name "My Mix"  # custom playlist name
"""

import argparse
import sys

import apple_music_mood as core   # reuse run_osascript + parse_comments

# How much each feature matters for "similar". All are 0..1 so same scale.
# Tune freely — bump groove/energy to weight rhythm + intensity higher.
WEIGHTS = {
    "energy": 1.5,
    "danceability": 1.5,
    "valence": 1.2,
    "acousticness": 1.0,
    "speechiness": 0.6,
    "instrumentalness": 0.6,
}
DEFAULT_COUNT = 25


def _esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def get_candidate_tracks():
    """Every library track that has our cached feature numbers in Comments."""
    SEP = "␟"
    script = (
        'tell application "Music"\n'
        '    set out to ""\n'
        '    set sep to "' + SEP + '"\n'
        '    repeat with t in (every track of library playlist 1 whose comment contains "energy=")\n'
        '        try\n'
        '            set out to out & (database ID of t as text) & sep & (name of t) & sep & '
        '(artist of t) & sep & (comment of t) & sep & (grouping of t) & linefeed\n'
        '        end try\n'
        '    end repeat\n'
        '    return out\n'
        'end tell'
    )
    raw = core.run_osascript(script)
    out = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        p = line.split(SEP)
        if len(p) < 5:
            continue
        feats = core.parse_comments(p[3])
        if not feats:
            continue
        out.append({"dbid": p[0], "name": p[1], "artist": p[2],
                    "feats": feats, "grouping": p[4]})
    return out


def seed_centroid(seeds):
    """Average feature vector of the selected seed songs (with cached numbers)."""
    vecs = [core.parse_comments(s.get("comment", "")) for s in seeds]
    vecs = [v for v in vecs if v]
    if not vecs:
        return None, []
    avg = {}
    for k in WEIGHTS:
        vals = [v[k] for v in vecs if k in v]
        if vals:
            avg[k] = sum(vals) / len(vals)
    return avg, vecs


def distance(a, b):
    """Weighted Euclidean distance over the features both vectors share."""
    total = wsum = 0.0
    for k, w in WEIGHTS.items():
        if k in a and k in b:
            total += w * (a[k] - b[k]) ** 2
            wsum += w
    return (total / wsum) ** 0.5 if wsum else float("inf")


def build_playlist(name, dbids):
    """Create (or clear) a regular playlist and add the given tracks in order."""
    lines = ['tell application "Music"',
             f'    if not (exists playlist "{_esc(name)}") then make new playlist with properties {{name:"{_esc(name)}"}}',
             f'    try', f'        delete every track of playlist "{_esc(name)}"', '    end try']
    for d in dbids:
        lines.append(f'    duplicate (first track of library playlist 1 whose database ID is {d}) '
                     f'to playlist "{_esc(name)}"')
    lines.append('end tell')
    core.run_osascript("\n".join(lines))


def main():
    p = argparse.ArgumentParser(description="Build a playlist of songs similar to the selected one(s).")
    p.add_argument("--count", type=int, default=DEFAULT_COUNT, help="How many similar songs (default 25)")
    p.add_argument("--same-language", action="store_true", help="Only songs in the seed's language")
    p.add_argument("--name", help="Playlist name (default: 'Similar to <seed>')")
    p.add_argument("--dry-run", action="store_true", help="Print ranked matches; don't make a playlist")
    args = p.parse_args()

    try:
        seeds = core.get_selected_tracks()
    except RuntimeError as e:
        sys.exit(f"Couldn't read the Music selection. Is Music open with a song selected?\n{e}")
    if not seeds:
        sys.exit("Select one or more 'seed' songs in Music, then run again.")

    centroid, used = seed_centroid(seeds)
    if not centroid:
        sys.exit("The selected song(s) have no cached feature numbers in Comments.\n"
                 "Tag them first:  python3 apple_music_mood.py")

    seed_dbids = {s["dbid"] for s in seeds}
    seed_lang = (seeds[0].get("grouping") or "").split()[:1]
    seed_lang = seed_lang[0].lower() if seed_lang else None

    candidates = get_candidate_tracks()
    if not candidates:
        sys.exit("No library songs have cached features yet. Tag some with apple_music_mood.py first.")

    ranked = []
    for c in candidates:
        if c["dbid"] in seed_dbids:
            continue
        if args.same_language and seed_lang:
            if not c["grouping"].lower().startswith(seed_lang):
                continue
        ranked.append((distance(centroid, c["feats"]), c))
    ranked.sort(key=lambda x: x[0])
    top = ranked[:args.count]

    seed_name = seeds[0]["name"] + (f" +{len(seeds) - 1}" if len(seeds) > 1 else "")
    name = args.name or f"Similar to {seed_name}"

    print(f"Seed: {seed_name}   (using {len(used)} seed vector(s))")
    print(f"Scanned {len(candidates)} songs with cached features.\n")
    for dist, c in top:
        print(f"  {dist:.3f}  {c['name']} — {c['artist']}")

    if args.dry_run:
        print("\n(dry run — no playlist created)")
        return
    if not top:
        sys.exit("\nNo similar songs found (try without --same-language, or tag more songs).")

    build_playlist(name, [c["dbid"] for _, c in top])
    print(f"\nCreated playlist '{name}' with {len(top)} song(s).")


if __name__ == "__main__":
    main()
