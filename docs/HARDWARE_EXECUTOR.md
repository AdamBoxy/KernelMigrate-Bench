# Hardware executor contract

KernelMigrate separates **task intent** from **execution substrate**.

A hardware executor consumes one task definition and one candidate
`solution.json`, then returns the same five score dimensions emitted by the
simulator. It must record:

- immutable container/toolchain identifiers;
- physical GPU model and architecture;
- compiler command and exit status;
- randomized correctness cases and tolerances;
- warmup policy, repetitions, latency distribution, and baseline;
- profiler artifacts or a reason they were unavailable.

The old environment should be built once to produce reference outputs and
performance envelopes. The candidate is built only in the new environment.
Reference implementation source may be visible, but randomized verifier inputs
and expected outputs should remain hidden during evaluation.

Recommended isolation:

- no network during candidate execution;
- read-only benchmark and oracle mounts;
- writable candidate/build directories only;
- bounded runtime and device memory;
- rejection of modified tests, timing code, or evaluator imports.

The simulated executor in `kernelmigrate.py` is the conformance reference for
report shape, not for GPU validity.
