# KernelMigrate  

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)  
[![Python tests](https://github.com/AdamBoxy/KernelMigrate-Bench/actions/workflows/python-app.yml/badge.svg)](https://github.com/AdamBoxy/KernelMigrate-Bench/actions/workflows/python-app.yml)  

**Can an AI keep accelerated code alive while the stack changes underneath it?**

KernelMigrate is an MVP benchmark for AI-driven GPU-kernel maintenance:
porting, architecture migration, runtime upgrades, stale autotuning recovery,
and accumulated dependency drift.

The benchmark idea was prompted by an observation from **Paige Bailey**:
kernel generation asks whether AI can write a kernel from scratch; production
engineering asks whether AI can keep one alive through driver updates,
architecture bumps, and years of neglect. This initial benchmark design and
implementation grew from that seed through collaboration between AI and human.  

## What version 0.1 measures

Every task supplies:

- an old known-good kernel contract;
- a changed target environment;
- a deliberately stale migration manifest;
- deterministic private-style probes derived from the old behavior;
- compatibility, performance-retention, and hygiene checks.

The included executor is a **CPU-only simulation lane**. It validates the
benchmark design and agent workflow; it does not claim to validate real GPU
machine code. The executor interface is deliberately small so a ROCm/CUDA
container or hardware farm can replace it later.

## Quick start

```bash
python kernelmigrate.py list
python kernelmigrate.py prepare workspace
python kernelmigrate.py grade reference_solutions --output results/reference
python kernelmigrate.py grade starter_solutions --output results/starter
python -m unittest discover -s tests -v
```

To evaluate an agent, copy `starter_solutions/`, let the agent edit the five
`solution.json` files, then grade that directory.

## Score

Each task is worth 100 points:

| Dimension | Points | Meaning |
| --- | ---: | --- |
| Semantic preservation | 35 | New implementation matches the old kernel contract |
| Migration completeness | 20 | Backend/runtime/API changes are internally coherent |
| Target compatibility | 15 | Architecture and launch assumptions match the target |
| Performance retention | 20 | Analytical target estimate stays within the allowed regression |
| Maintenance hygiene | 10 | Stale pins removed and validation evidence recorded |

Critical semantic failures cap a task at 25. A declared target mismatch caps it
at 50. The overall report contains per-check evidence rather than only a scalar.

## Real hardware path

A production executor should preserve the task and report schemas while
replacing the simulated checks with:

1. containerized old and new toolchains;
2. compilation on the declared target;
3. randomized differential tests against the old kernel;
4. profiler-backed latency and throughput measurements;
5. clean-room hidden shapes, dtypes, alignments, and edge cases.

See `docs/HARDWARE_EXECUTOR.md`.

## License

MIT. Attribution for the originating benchmark observation is retained in
`NOTICE.md`.
