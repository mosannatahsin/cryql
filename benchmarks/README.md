# CryQL benchmark scaffolding

Benchmark runs must use the synthetic lab and record measured values rather
than claiming results. Recommended measurements are recovered field precision
and recall, request count, runtime, false positives, and memory use. This
directory intentionally contains no fabricated result files.

Run a local measurement with:

```bash
python benchmarks/run.py
python benchmarks/run.py --output benchmark-result.json
```

The output is generated from the current implementation and lab run.
