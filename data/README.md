# Data (`data/`)

ARC-AGI task JSONs. These are **fetched, not committed** (git-ignored) to keep history clean. Run the fetch script to populate:

```bash
python data/fetch_arc.py
```

This clones (shallow) the public task corpora:

| Dir | Source | Contents |
| --- | --- | --- |
| `data/arc-agi-1/` | `https://github.com/fchollet/ARC-AGI` | ARC-AGI-1 training + evaluation tasks (JSON) |
| `data/arc-agi-2/` | `https://github.com/arcprize/ARC-AGI-2` | ARC-AGI-2 public training + evaluation tasks (JSON) |

Each task JSON has the standard ARC schema: `{"train": [{"input": grid, "output": grid}, ...], "test": [{"input": grid}, ...]}` where a grid is a 2D array of integers 0-9.

After fetching, `fetch_arc.py` prints task counts as a sanity check. If an upstream URL has moved, update it at the top of the script (canonical pointers: the ARC Prize site and the `fchollet/ARC-AGI` repo).
