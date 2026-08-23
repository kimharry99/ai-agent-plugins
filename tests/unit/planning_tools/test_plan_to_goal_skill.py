"""Contract tests for the planning-tools plugin."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "planning-tools"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "plan-to-goal"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
EVALUATION_CASES_PATH = (
    SKILL_ROOT / "references" / "evaluation-cases.json"
)
OUTPUT_SECTIONS = (
    "Task",
    "Expected behavior",
    "Constraints",
    "Verification",
    "Definition of done",
)
REQUIRED_COVERAGE = {
    "absent-completion-condition",
    "behavior-and-verification",
    "conflict",
    "cross-section-default-duplication",
    "edit-target-over-extraction",
    "exception",
    "explicit-completion-without-artifact",
    "identifiers",
    "mixed-language",
    "multiline-shell-command",
    "positive-negative-equivalence",
    "progressive-restatement",
    "summary-body-completion-repetition",
    "unique-handoff-record",
    "unique-completion-condition",
}


class PlanToGoalSkillTest(unittest.TestCase):
    """Verify plugin discovery and the plan-to-goal instruction contract."""

    @staticmethod
    def _load_json(path: Path) -> object:
        """Load JSON from path.

        Args:
            path: JSON file to load.

        Returns:
            Parsed JSON value.
        """
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)

    @staticmethod
    def _parse_output_sections(output: str) -> dict[str, str]:
        """Parse the five level-two sections from a fixture output.

        Args:
            output: Expected generated goal prompt.

        Returns:
            Mapping from heading to section body.
        """
        heading_pattern = re.compile(
            r"^## (Task|Expected behavior|Constraints|Verification|"
            r"Definition of done)$",
            re.MULTILINE,
        )
        matches = list(heading_pattern.finditer(output))
        sections = {}
        for index, match in enumerate(matches):
            body_start = match.end()
            body_end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(output)
            )
            sections[match.group(1)] = output[body_start:body_end].strip()
        return sections

    @staticmethod
    def _expected_output(case: dict[str, object]) -> str:
        """Join a fixture's expected output lines.

        Args:
            case: Evaluation case containing expected output lines.

        Returns:
            Complete expected goal prompt.
        """
        return "\n".join(case["expected_output"])

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

        self.assertIsInstance(codex_manifest, dict)
        self.assertIsInstance(claude_manifest, dict)
        self.assertIsInstance(codex_marketplace, dict)
        self.assertIsInstance(claude_marketplace, dict)
        self.assertEqual(codex_manifest["name"], "planning-tools")
        self.assertEqual(codex_manifest["skills"], "skills")
        self.assertEqual(claude_manifest["name"], "planning-tools")
        self.assertEqual(codex_manifest["version"], "0.2.0")
        self.assertEqual(
            claude_manifest["version"],
            codex_manifest["version"],
        )

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

    def test_skill_requires_a_global_atomic_requirement_ledger(self) -> None:
        """Require extraction and canonicalization before section rendering."""
        skill = SKILL_PATH.read_text(encoding="utf-8")
        normalized_skill = " ".join(skill.lower().split())

        required_clauses = (
            "before rendering any output section",
            "independently verifiable",
            "summaries, body sections, constraints, validation plans, "
            "completion statements, and conclusions",
            "action, target, conditions, exceptions, requirement strength, "
            "values, directions, counts, paths, identifiers, commands, and "
            "source context",
            "explicitly declared as a completion condition",
            "positive and the other is negative",
            "desired design and the other rejects the inverse alternative",
            "strongest requirement",
            "union of all unique qualifiers",
            "prefer preservation over deletion",
            "exactly once",
        )
        for clause in required_clauses:
            with self.subTest(clause=clause):
                self.assertIn(clause, normalized_skill)

    def test_skill_defines_non_mergeable_requirements_and_conflicts(
        self,
    ) -> None:
        """Protect distinctions that semantic deduplication must retain."""
        skill = " ".join(
            SKILL_PATH.read_text(encoding="utf-8").lower().split()
        )
        distinct_pairs = (
            "implementation behavior with its verification",
            "verification command with a distinct acceptance criterion",
            "general rule with a specific exception",
            "different values, directions, conditions, or error conditions",
        )
        for pair in distinct_pairs:
            with self.subTest(pair=pair):
                self.assertIn(pair, skill)
        self.assertIn("preserve both sides", skill)
        self.assertIn("explicitly marked conflict", skill)

    def test_skill_assigns_each_requirement_to_one_owned_section(self) -> None:
        """Keep section ownership mutually exclusive and intent-based."""
        skill = " ".join(
            SKILL_PATH.read_text(encoding="utf-8").lower().split()
        )

        self.assertIn("exactly one section", skill)
        self.assertIn("observable runtime behavior", skill)
        self.assertIn("public data contracts", skill)
        self.assertIn("prohibitions, compatibility guarantees", skill)
        self.assertIn("architectural restrictions", skill)
        self.assertIn("tests, inspections, commands", skill)
        self.assertIn(
            "unique terminal acceptance states and handoff artifacts",
            skill,
        )
        self.assertIn(
            "do not repeat an implementation obligation in both",
            skill,
        )
        self.assertIn("do not repeat earlier sections", skill)
        self.assertIn("do not use a cross-reference", skill)

    def test_skill_excludes_planning_metadata_from_product_behavior(
        self,
    ) -> None:
        """Keep navigation and explanatory metadata out of behavior."""
        skill = " ".join(
            SKILL_PATH.read_text(encoding="utf-8").lower().split()
        )

        for metadata in (
            "edit-target file lists",
            "implementation ordering",
            "alternatives considered",
            "explanatory context",
            "risk descriptions",
            "lists of test files",
        ):
            with self.subTest(metadata=metadata):
                self.assertIn(metadata, skill)
        self.assertIn("navigation metadata", skill)

    def test_output_template_uses_markdown_and_executable_commands(
        self,
    ) -> None:
        """Require renderable Markdown rather than escaped or inline output."""
        skill = SKILL_PATH.read_text(encoding="utf-8")
        normalized_skill = " ".join(skill.lower().split())
        heading_positions = [
            skill.index(f"## {heading}") for heading in OUTPUT_SECTIONS
        ]

        self.assertEqual(heading_positions, sorted(heading_positions))
        self.assertNotIn(r"\#", skill)
        self.assertNotIn(r"\*\*", skill)
        self.assertNotIn("own inline-code line", skill)
        self.assertIn("bullet list", skill.lower())
        self.assertIn("executable fenced code block", skill.lower())
        self.assertIn(
            "preserve their text and line structure verbatim",
            normalized_skill,
        )
        self.assertIn("longer outer fence", skill.lower())

    def test_evaluation_cases_cover_required_semantic_failures(self) -> None:
        """Provide representative fixtures for every requested failure mode."""
        cases = self._load_json(EVALUATION_CASES_PATH)

        self.assertIsInstance(cases, list)
        self.assertGreaterEqual(len(cases), 6)
        self.assertFalse(
            any(case.get("expected_done_empty", False) for case in cases)
        )
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        for case in cases:
            self.assertIsInstance(case["plan_input"], list)
            self.assertIsInstance(case["expected_output"], list)
            self.assertTrue(case["plan_input"])
            self.assertTrue(case["expected_output"])
        covered = {
            coverage
            for case in cases
            for coverage in case["covers"]
        }
        self.assertEqual(REQUIRED_COVERAGE, covered)

    def test_fixture_outputs_preserve_atomic_requirements_exactly_once(
        self,
    ) -> None:
        """Validate requirements, qualifiers, and section ownership."""
        cases = self._load_json(EVALUATION_CASES_PATH)

        for case in cases:
            output = self._expected_output(case)
            sections = self._parse_output_sections(output)
            with self.subTest(case=case["id"]):
                self.assertEqual(list(sections), list(OUTPUT_SECTIONS))
                self.assertTrue(sections["Definition of done"])
                for requirement in case["atomic_requirements"]:
                    canonical = requirement["canonical"]
                    owner = requirement["section"]
                    self.assertEqual(1, output.count(canonical))
                    self.assertIn(canonical, sections[owner])
                    for section, body in sections.items():
                        if section != owner:
                            self.assertNotIn(canonical, body)
                    for qualifier in requirement["qualifiers"]:
                        self.assertIn(qualifier, canonical)
                for omitted in case.get("forbidden_output", []):
                    self.assertNotIn(omitted, output)

    def test_fixture_outputs_handle_completion_and_conflicts(self) -> None:
        """Distinguish absent completion criteria and preserve conflicts."""
        cases = self._load_json(EVALUATION_CASES_PATH)

        for case in cases:
            output = self._expected_output(case)
            sections = self._parse_output_sections(output)
            done = sections["Definition of done"]
            with self.subTest(case=case["id"]):
                if case["has_terminal_condition"]:
                    self.assertNotIn("Not specified.", done)
                    self.assertNotEqual("", done)
                else:
                    self.assertEqual(f"- {case['not_specified']}", done)
                for conflict in case.get("conflicts", []):
                    self.assertIn("Conflict:", sections[conflict["section"]])
                    for side in conflict["sides"]:
                        self.assertEqual(1, output.count(side))

    def test_fixture_shell_commands_are_verbatim_and_fenced(self) -> None:
        """Keep shell commands executable with original line structure."""
        cases = self._load_json(EVALUATION_CASES_PATH)

        for case in cases:
            output = self._expected_output(case)
            for command in case.get("shell_commands", []):
                with self.subTest(case=case["id"], command=command):
                    self.assertEqual(1, output.count(command))
                    self.assertRegex(
                        output,
                        rf"\x60\x60\x60(?:bash|sh|shell)\n"
                        rf"{re.escape(command)}\n\x60\x60\x60",
                    )


if __name__ == "__main__":
    unittest.main()
