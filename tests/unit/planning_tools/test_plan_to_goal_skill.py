"""Contract tests for the planning-tools plugin."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "planning-tools"
SKILL_PATH = PLUGIN_ROOT / "skills" / "plan-to-goal" / "SKILL.md"

class PlanToGoalSkillTest(unittest.TestCase):
    """Verify plugin discovery and the plan-to-goal instruction contract."""

    @staticmethod
    def _load_json(path: Path) -> dict:
        """Load a JSON object from path.

        Args:
            path: JSON file to load.

        Returns:
            Parsed JSON object.
        """
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)

    def test_plugin_is_discoverable_in_manifests_and_marketplaces(self) -> None:
        """Expose planning-tools consistently to Codex and Claude."""
        self.assertTrue(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").is_file(),
            "Codex plugin manifest must exist",
        )
        self.assertTrue(
            (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").is_file(),
            "Claude plugin manifest must exist",
        )
        codex_manifest = self._load_json(
            PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
        )
        claude_manifest = self._load_json(
            PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        )
        codex_marketplace = self._load_json(
            REPO_ROOT / ".agents/plugins/marketplace.json"
        )
        claude_marketplace = self._load_json(
            REPO_ROOT / ".claude-plugin/marketplace.json"
        )

        self.assertEqual(codex_manifest["name"], "planning-tools")
        self.assertEqual(codex_manifest["skills"], "skills")
        self.assertEqual(claude_manifest["name"], "planning-tools")

        codex_entry = next(
            plugin
            for plugin in codex_marketplace["plugins"]
            if plugin["name"] == "planning-tools"
        )
        self.assertEqual(
            codex_entry["source"],
            {"source": "local", "path": "./planning-tools"},
        )
        self.assertEqual(
            codex_entry["policy"],
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        )

        claude_entry = next(
            plugin
            for plugin in claude_marketplace["plugins"]
            if plugin["name"] == "planning-tools"
        )
        self.assertEqual(claude_entry["source"], "./planning-tools")

    def test_skill_contract_preserves_plan_as_the_only_source(self) -> None:
        """Require grounded generation rather than requirement invention."""
        self.assertTrue(
            SKILL_PATH.is_file(), "plan-to-goal SKILL.md must exist"
        )
        skill = SKILL_PATH.read_text(encoding="utf-8")
        normalized_skill = " ".join(skill.lower().split())

        self.assertIn("name: plan-to-goal", skill)
        self.assertIn("required", normalized_skill)
        self.assertIn("absolute path", normalized_skill)
        self.assertIn("sole source of truth", normalized_skill)
        self.assertIn("do not inspect", normalized_skill)
        self.assertIn("do not create or invoke a goal", normalized_skill)
        self.assertIn("primary language", normalized_skill)
        self.assertIn("not specified", normalized_skill)

    def test_skill_contract_defines_the_goal_prompt_sections(self) -> None:
        """Keep the goal prompt complete and predictably structured."""
        self.assertTrue(
            SKILL_PATH.is_file(), "plan-to-goal SKILL.md must exist"
        )
        skill = SKILL_PATH.read_text(encoding="utf-8")
        normalized_skill = " ".join(skill.lower().split())

        expected_headings = (
            "**Task**",
            "**Expected behavior**",
            "**Constraints**",
            "**Verification**",
            "**Definition of done**",
        )
        positions = [skill.index(heading) for heading in expected_headings]

        self.assertEqual(positions, sorted(positions))
        self.assertIn("implement the functionality in", normalized_skill)
        self.assertIn("conflict", normalized_skill)
        self.assertIn("partial prompt", normalized_skill)


if __name__ == "__main__":
    unittest.main()
