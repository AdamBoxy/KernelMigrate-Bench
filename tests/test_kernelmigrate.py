import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kernelmigrate import grade, grade_task, performance_ratio, task_map  # noqa: E402


class KernelMigrateTests(unittest.TestCase):
    def test_reference_scores_100(self):
        report = grade(ROOT / "reference_solutions")
        self.assertEqual(report["score"], 100)

    def test_starter_is_broken_but_partially_preserves_behavior(self):
        report = grade(ROOT / "starter_solutions")
        self.assertGreater(report["score"], 0)
        self.assertLess(report["score"], 60)

    def test_semantic_failure_caps_task(self):
        task = task_map()["cuda_to_hip"]
        solution = json.loads(
            (ROOT / "reference_solutions/cuda_to_hip/solution.json").read_text()
        )
        solution["implementation"] = "unrelated"
        result = grade_task(task, solution)
        self.assertLessEqual(result["score"], 25)
        self.assertTrue(result["hard_failures"])

    def test_wrong_target_caps_task(self):
        task = task_map()["gfx942_to_gfx950"]
        solution = json.loads(
            (ROOT / "reference_solutions/gfx942_to_gfx950/solution.json").read_text()
        )
        solution["target"] = "gfx942"
        result = grade_task(task, solution)
        self.assertLessEqual(result["score"], 50)

    def test_stale_tuning_is_slower(self):
        task = task_map()["stale_autotune"]
        good = json.loads(
            (ROOT / "reference_solutions/stale_autotune/solution.json").read_text()
        )
        stale = dict(good)
        stale["launch"] = {"block_size": 64, "vector_width": 2, "waves": 8}
        stale["tuning"] = {"generated_for": "gfx942"}
        self.assertGreater(performance_ratio(task, stale), performance_ratio(task, good))

    def test_missing_candidate_does_not_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            report = grade(Path(directory))
        self.assertEqual(report["score"], 0)


if __name__ == "__main__":
    unittest.main()
