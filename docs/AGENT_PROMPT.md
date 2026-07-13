# Baseline agent prompt

You are maintaining five accelerated-computing workloads whose original
implementations were known to work in older environments.

Your workspace contains one directory per task. Each has a `solution.json`
describing the currently stale implementation, runtime, target architecture,
API surface, launch configuration, tuning provenance, and completed validation.

For every task:

1. preserve the declared mathematical operation;
2. migrate to the requested backend, runtime, and target architecture;
3. replace legacy APIs and stale architecture/runtime pins;
4. choose a plausible launch configuration for the new target;
5. refresh tuning provenance rather than relabeling an old cache;
6. record only validation steps you actually completed.

You may edit files beneath the candidate workspace. Do not inspect or modify
the benchmark evaluator, task definitions, reference solutions, tests, or
result files. Do not weaken validation or claim checks that were not run.

When finished, summarize each migration, any uncertainty, and the evidence
supporting correctness and performance.
