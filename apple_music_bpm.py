#!/usr/bin/env python3
"""
apple_music_bpm.py — fill the BPM field of selected Apple Music tracks (Mac)
by looking up each song's tempo in the free GetSongBPM database.

This works for streamed Apple Music tracks too, because it doesn't touch the
audio file — it reads each track's title + artist from the Music app, looks up
the tempo online, and writes the number back via AppleScript (osascript).

------------------------------------------------------------------------------
ONE-TIME SETUP
------------------------------------------------------------------------------
1. Get a free API key:
     - Go to https://getsongbpm.com/api and register with your email.
     - They require a link back to getsongbpm.com somewhere (their rule).
2. Paste your key into API_KEY below.
3. No pip installs needed. Uses only Python 3's standard library + osascript.

------------------------------------------------------------------------------
HOW TO RUN
------------------------------------------------------------------------------
1. Open the Music app, open a playlist, and SELECT the tracks you want
   (Cmd-A selects all in the current list).
2. In Terminal:
     python3 apple_music_bpm.py            # fills in BPM for the selection
     python3 apple_music_bpm.py --dry-run  # just shows what it found, writes nothing
     python3 apple_music_bpm.py --force    # overwrite BPM even if already set

Make the BPM column visible in Music (right-click a column header > BPM) to
watch the values appear.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Your GetSongBPM key. Two ways to supply it:
#   1. Set an env var (recommended for a public repo — keeps the key out of git):
#        export GETSONGBPM_API_KEY="your-key"
#   2. Or paste it directly below (do NOT commit it to a public repo).
API_KEY = os.environ.get("GETSONGBPM_API_KEY", "PASTE_YOUR_GETSONGBPM_KEY_HERE")
API_BASE = "https://api.getsong.co"
REQUEST_PAUSE = 0.4   # seconds between API calls, to be polite / avoid rate limits
# ---------------------------------------------------------------------------


def run_osascript(script):
    """Run an AppleScript string and return its stdout (stripped)."""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.rstrip("\n")


def get_selected_tracks():
    """Return a list of (database_id, title, artist, current_bpm) for the
    tracks currently selected in the Music app."""
    script = (
        'tell application "Music"\n'
        '    set out to ""\n'
        '    set sel to selection\n'
        '    repeat with t in sel\n'
        '        try\n'
        '            set out to out & (database ID of t as text) & tab & '
        '(name of t) & tab & (artist of t) & tab & (bpm of t as text) & linefeed\n'
        '        end try\n'
        '    end repeat\n'
        '    return out\n'
        'end tell'
    )
    raw = run_osascript(script)
    tracks = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        dbid, title, artist, bpm = parts[0], parts[1], parts[2], parts[3]
        try:
            cur = int(bpm)
        except ValueError:
            cur = 0
        tracks.append((dbid, title, artist, cur))
    return tracks


def _fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "apple-music-bpm/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def lookup_bpm(title, artist):
    """Look up tempo for one song. Returns an int BPM or None."""
    # Trim things that hurt matching (feat., remaster tags, etc.)
    clean_title = title.split("(")[0].split("[")[0].split(" - ")[0].strip()
    clean_artist = artist.split("&")[0].split(",")[0].split("feat")[0].strip()

    lookup = f"song:{clean_title} artist:{clean_artist}"
    qs = urllib.parse.urlencode(
        {"api_key": API_KEY, "type": "both", "lookup": lookup},
        quote_via=lambda s, safe, enc, err: urllib.parse.quote(s, safe=":"),
    )
    search_url = f"{API_BASE}/search/?{qs}"

    try:
        data = _fetch_json(search_url)
    except Exception:
        return None

    hits = data.get("search")
    if not isinstance(hits, list) or not hits:
        return None
    first = hits[0]

    # Some responses include tempo directly in the search hit...
    tempo = first.get("tempo")
    if not tempo and first.get("id"):
        # ...otherwise fetch the full song record by id.
        try:
            song_qs = urllib.parse.urlencode({"api_key": API_KEY, "id": first["id"]})
            song = _fetch_json(f"{API_BASE}/song/?{song_qs}")
            tempo = (song.get("song") or {}).get("tempo")
        except Exception:
            tempo = None

    if not tempo:
        return None
    try:
        return int(round(float(tempo)))
    except (ValueError, TypeError):
        return None


def set_bpm(dbid, bpm):
    """Write BPM into the Music track with the given database ID."""
    script = (
        f'tell application "Music" to set bpm of '
        f'(first track whose database ID is {dbid}) to {bpm}'
    )
    run_osascript(script)


def main():
    parser = argparse.ArgumentParser(description="Fill BPM for selected Apple Music tracks.")
    parser.add_argument("--dry-run", action="store_true", help="Show lookups; write nothing")
    parser.add_argument("--force", action="store_true", help="Overwrite BPM even if already set")
    args = parser.parse_args()

    if API_KEY == "PASTE_YOUR_GETSONGBPM_KEY_HERE":
        sys.exit("Add your GetSongBPM API key to the API_KEY line near the top of this file.")

    try:
        tracks = get_selected_tracks()
    except RuntimeError as e:
        sys.exit(f"Couldn't read the Music selection. Is the Music app open with tracks selected?\n{e}")

    if not tracks:
        sys.exit("No tracks selected. Select some songs in the Music app, then run again.")

    print(f"Selected {len(tracks)} track(s).\n")
    found = skipped = missed = 0

    for dbid, title, artist, cur in tracks:
        label = f"{title} — {artist}"
        if cur and not args.force:
            print(f"  skip   {label}  (already {cur} BPM)")
            skipped += 1
            continue

        bpm = lookup_bpm(title, artist)
        time.sleep(REQUEST_PAUSE)

        if bpm is None:
            print(f"  MISS   {label}  (not in database)")
            missed += 1
            continue

        if args.dry_run:
            print(f"  ----   {label}  ->  {bpm} BPM  (dry run)")
        else:
            try:
                set_bpm(dbid, bpm)
                print(f"  set    {label}  ->  {bpm} BPM")
                found += 1
            except RuntimeError as e:
                print(f"  FAIL   {label}  (couldn't write: {e})")
                missed += 1

    print(f"\nDone. Set: {found}   Skipped: {skipped}   Not found: {missed}")
    if missed:
        print("Tracks marked MISS aren't in the database (common for regional/indie songs).\n"
              "You can look those up manually on songbpm.com or tunebat.com and type them in.")


if __name__ == "__main__":
    main()