# Studies

A study is a declarative, reproducible workflow over registered code and data.
Each study directory should contain:

```text
README.md             scientific question and allowed claims
study.toml            grids, solver, gauges, seeds, bounds, and outputs
selection.toml        explicit branch/gate policy
expected/             small golden summaries
figures.py            pure rendering from registered datasets
```

Generated roots, checkpoints, and logs belong under ignored `runs/` and are
promoted only through a validated dataset manifest.
