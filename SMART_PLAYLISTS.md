# Smart Playlist cookbook

How to **combine** the properties this project writes into recipes — and what
each combination gives you. (For the raw field/tag reference, see
[TAGGING.md](TAGGING.md).)

## The idea

Every property is a **dial**. One rule = a broad slice; combining rules
**narrows** it. Think of it as stacking filters:

```
tamil           → all your Tamil songs
+ groovy        → ...that are danceable
+ bright        → ...and happy/upbeat
+ BPM > 130     → ...and fast
= "Tamil party bangers"
```

Each added rule removes songs that don't match all of them.

## What you can filter on

**Text — use `contains` (in the Grouping field):**

| Group | Words you can match |
|-------|---------------------|
| Language | `tamil` · `english` · `others` |
| Energy | `energy-low` · `energy-mid` · `energy-high` |
| Groove | `groovy` · `dance-mid` · `dance-low` |
| Mood | `bright` · `dark` |
| Texture | `acoustic` · `produced` · `instrumental` · `rappy` · `live` |
| Tempo | `slow` · `mid-tempo` · `fast` |
| Category | `Groove` · `Anthem` · `Intense` · `Warm` · `Soulful` · `untagged` |

**Numeric — use `is greater than` / `is less than` / `in the range`:**

| Field | Holds | Example |
|-------|-------|---------|
| `Rating` | energy ×100 | `Rating > ★★★★` ≈ energy > 0.80 |
| `Movement Number` | danceability ×100 | `Movement Number > 80` = very danceable |
| `BPM` | tempo | `BPM in the range 150–175` |

**Plus Apple's own fields:** `Year`, `Artist`, `Genre`, `Plays`, `Love`,
`Date Added`, `Playlist` (to scope to one playlist), etc.

## AND vs OR

At the top of the editor:

- **Match `all`** = AND — song must satisfy *every* rule (narrows). Most recipes.
- **Match `any`** = OR — song satisfies *at least one* rule (widens). Good for
  "groovy OR fast", or grouping several bands together.
- **Nested groups** (the `…` / `(+)` to add a rule group) let you mix:
  `tamil AND (groovy OR fast)`.

Always: **uncheck "Limit to N"**, keep **"Live updating" ✓**.

## Recipe cookbook

Each = Match **all** unless noted. `[scope]` = optionally add
`Playlist is "<your curated list>"` to limit it to songs you chose.

### By situation
| You want | Rules | What you get |
|----------|-------|--------------|
| 🛏 **Wind-down / bed** | `energy-low` + `bright` + `acoustic` | soft, calm, pleasant melodies |
| 💻 **Focus / desk** | `energy-mid` + `does not contain rappy` | steady, present, not distracting |
| 🚗 **Drive / hype** | `groovy` + `bright` + `energy-high` | sing-along, high-energy bangers |
| 😴 **Sleep** | `energy-low` + `acoustic` + `BPM < 90` | slowest, softest tracks |

### By energy / intensity (numeric, live-tunable)
| You want | Rules | What you get |
|----------|-------|--------------|
| 🔥 **Peak energy only** | `Rating > ★★★★` (energy > 0.80) | only the most intense songs |
| 🌊 **Truly chill** | `Rating < ★★` (energy < 0.40) | the calmest tracks |
| 💃 **Maximum groove** | `Movement Number > 80` | the most danceable songs |
| 🏃 **Running cadence** | `BPM in range 160–180` + `energy-high` | steady fast pace for runs |

### By mood
| You want | Rules | What you get |
|----------|-------|--------------|
| 😀 **Feel-good** | `bright` + `groovy` | happy + danceable |
| 💔 **Heartbreak / emotional** | `dark` + `energy-low` (= `Soulful`) | sad, tender songs |
| 😤 **Intense / mass** | `dark` + `energy-high` (= `Intense`) | heavy, serious, powerful |
| 🎤 **Rap / hip-hop** | `rappy` | spoken/rap-forward tracks |
| 🎸 **Unplugged** | `acoustic` + `energy-low` | soft acoustic-leaning songs |

### By language (combine with anything above)
| You want | Rules |
|----------|-------|
| Tamil dance bangers | `tamil` + `groovy` + `bright` |
| Tamil melodies | `tamil` + `Warm` |
| Tamil rap | `tamil` + `rappy` |
| English chill | `english` + `energy-low` + `bright` |
| Tamil + fast for the gym | `tamil` + `energy-high` + `BPM > 130` |

### By quality / freshness (mix in Apple's fields)
| You want | Rules |
|----------|-------|
| Recent favourites | `Love is Loved` + `Date Added in the last 3 months` |
| New Tamil groove | `tamil` + `groovy` + `Year > 2023` |
| Best high-energy | `Rating > ★★★★` + `Plays > 10` |

### Maintenance
| Playlist | Rule |
|----------|------|
| ✋ **To tag by hand** | `Grouping contains untagged` |
| 🆕 **Not processed yet** | `Grouping is` (blank) *(if your Music matches empty)* |

## Combining numeric + tags for precision

The tags are coarse buckets; the numeric fields are fine sliders. Combine them:

```
Match all:
   tamil                       (Grouping contains)
   groovy                      (Grouping contains)
   Rating       > 75           (energy > 0.75)
   Movement #   > 80           (danceability > 0.80)
   BPM in range 120–140
= "Tamil songs that are danceable AND high-energy AND in dance tempo"
```

Tune the cutoffs live in the rule — no re-running the script.

## Tip: build a folder

Make a **folder** ("Moods", "By Situation", …) in the sidebar and drag related
Smart Playlists into it, so they're grouped instead of loose.

## Tip: scope to your curated set

A Smart Playlist scans your **whole library** by default. To limit any recipe to
a curated playlist, add `Playlist is "<your playlist>"` as another `all` rule.
