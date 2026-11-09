"""Synthetic fixtures validate software only; they are never research data or findings."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

import implementation as m


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.w = Path(self.temp.name)

        reports = []
        rows = []
        eligibility = []

        self.quote = (
            "The board reviews audit reports and orders corrective action."
        )

        for i in range(4):
            firm = f"Company{i}"
            report_id = f"report{i}"

            reports.append(
                {
                    "report_id": report_id,
                    "Organization": firm,
                    "Country": "Country" + str(i % 2),
                    "Reporting Period": "Q2 2026",
                    "Publication Date": "June 1, 2026",
                    "date": "2026-06-01",
                    "template_fingerprint": "template",
                }
            )

            rows.append(
                {
                    "row_id": f"answer{i}",
                    "report_id": report_id,
                    "Organization": firm,
                    "Country": "Country" + str(i % 2),
                    "question": "Governance question",
                    "answer": self.quote,
                    "eligible": "True",
                    "all_four_answer": str(i % 2 == 0),
                    **{
                        "original_" + component: str(i % 2 == 0)
                        for component in m.COMP
                    },
                }
            )

            eligibility.append(
                {
                    "Organization": firm,
                    "Country": "Country" + str(i % 2),
                    "canonical_id": f"company{i}",
                    "corporate_eligible": "1",
                    "reviewed": "1",
                    "identity_source": "fixture only",
                    "decision_note": "fixture only",
                }
            )

        pd.DataFrame(reports).to_csv(
            self.w / "report_inventory.csv",
            index=False,
        )
        pd.DataFrame(rows).to_csv(
            self.w / "answer_features_and_audit.csv",
            index=False,
        )
        pd.DataFrame(eligibility).to_csv(
            self.w / "eligibility.csv",
            index=False,
        )

        (self.w / "lexicon_and_stage_rules.json").write_text(
            "{}",
            encoding="utf-8",
        )

        self.data = self.w / "input.csv"
        self.data.write_text("fixture only", encoding="utf-8")

        study = {
            "input_sha256": m.digest(self.data),
            "corpus_sha256": m.digest(
                self.w / "answer_features_and_audit.csv"
            ),
            "reports_sha256": m.digest(
                self.w / "report_inventory.csv"
            ),
        }

        (self.w / "study.json").write_text(
            json.dumps(study),
            encoding="utf-8",
        )

        self.args = SimpleNamespace(
            workspace=self.w,
            data=self.data,
        )

        m.freeze(self.args)

    def tearDown(self):
        self.temp.cleanup()

    def annotate(self):
        """Create synthetic reviewed controls for software tests only."""
        reports = m.read(self.w / "eligible_reports.csv")
        answers = m.read(self.w / "eligible_answers.csv")

        rows = []

        for _, report in reports.iterrows():
            report_id = report.report_id
            row_id = answers.loc[
                answers.report_id.eq(report_id),
                "row_id",
            ].iloc[0]

            for stage in m.STAGES:
                row = {
                    "unit_id": report_id + stage,
                    "report_id": report_id,
                    "control_id": "control1",
                    "stage": stage,
                    "row_ids": row_id,
                    "quote": self.quote,
                    "link_quote": self.quote,
                    "artifact_access": "internal",
                    "artifact_url": "",
                    "reviewed": "1",
                    "review_note": "fixture only",
                }

                row.update(
                    {component: "2" for component in m.COMP}
                )
                row.update(
                    {link: "1" for link in m.LINKS}
                )

                rows.append(row)

        pd.DataFrame(rows).to_csv(
            self.w / "chain_units.csv",
            index=False,
        )

        coverage = m.read(self.w / "coverage.csv")
        coverage["applicable"] = "1"
        coverage["review_complete"] = "1"
        coverage["review_scope"] = "All fixture answers"
        coverage["rationale"] = "fixture"

        coverage.to_csv(
            self.w / "coverage.csv",
            index=False,
        )

        principles = m.read(self.w / "principles.csv")
        principles["present"] = "1"
        principles["row_id"] = principles.report_id.map(
            answers.set_index("report_id").row_id
        )
        principles["quote"] = self.quote
        principles["reviewed"] = "1"
        principles["rationale"] = "fixture only"

        principles.to_csv(
            self.w / "principles.csv",
            index=False,
        )

    def fill_raters(self):
        """Populate synthetic coder fixtures; never use as research ratings."""
        filenames = [
            "coder_A.csv",
            "coder_B.csv",
            "adjudicated_sample.csv",
        ]

        for filename in filenames:
            frame = m.read(self.w / filename)

            for component in m.COMP:
                frame[component] = "2"

            for link in m.LINKS:
                frame[link] = "1"

            frame["supporting_quote"] = self.quote
            frame["adjudication_note"] = "fixture adjudication"

            frame.to_csv(
                self.w / filename,
                index=False,
            )

    def test_unknown_ids_rejected(self):
        frame = pd.DataFrame({"row_id": ["unknown"]})

        with self.assertRaises(ValueError):
            m.check_ids(
                frame,
                "row_id",
                {"known"},
                "test",
            )

    def test_freeze_never_redraws(self):
        original = m.digest(self.w / "frozen_sample.csv")

        with self.assertRaises(ValueError):
            m.freeze(self.args)

        self.assertEqual(
            original,
            m.digest(self.w / "frozen_sample.csv"),
        )

    def test_eligibility_change_blocks_analysis(self):
        with (self.w / "eligibility.csv").open(
            "a",
            encoding="utf-8",
        ) as stream:
            stream.write("\n")

        with self.assertRaises(ValueError):
            m.load_frozen(self.w)

    def test_empty_human_codes_block_findings(self):
        with self.assertRaises(ValueError):
            m.validate_units(self.w)

    def test_reviewed_units_and_16_exports(self):
        self.annotate()
        m.validate_units(self.w)
        self.fill_raters()
        m.analyse(self.args)

        output = next(
            path
            for path in self.w.glob("reviewed_results_*")
            if path.is_dir()
        )

        manifest = json.loads(
            (output / "manifest.json").read_text(
                encoding="utf-8"
            )
        )

        records = manifest["outputs"]
        self.assertEqual(len(records), 16)

        for record in records:
            pdf = output / (record["id"] + ".pdf")
            self.assertGreater(pdf.stat().st_size, 100)

    def test_invalid_quote_blocks_analysis(self):
        self.annotate()

        units = m.read(self.w / "chain_units.csv")
        units.loc[0, "quote"] = "fabricated quotation"

        units.to_csv(
            self.w / "chain_units.csv",
            index=False,
        )

        with self.assertRaises(ValueError):
            m.validate_units(self.w)

    def test_unknown_gold_ids_not_silently_dropped(self):
        filenames = [
            "coder_A.csv",
            "coder_B.csv",
            "adjudicated_sample.csv",
        ]

        for filename in filenames:
            frame = m.read(self.w / filename)
            frame.loc[0, "row_id"] = "unknown"

            frame.to_csv(
                self.w / filename,
                index=False,
            )

        with self.assertRaises(ValueError):
            m.evaluate(self.args)

    def test_heldout_evaluation_from_completed_fixtures(self):
        self.fill_raters()
        output = m.evaluate(self.args)

        validation = pd.read_csv(
            output / "candidate_validation.csv"
        )

        self.assertEqual(len(validation), 5)

    def test_invalid_scale_rejected(self):
        self.annotate()
        units = m.read(self.w / "chain_units.csv")

        # m.read() loads text columns: assign text, not an integer.
        # Validation must then reject the out-of-range score.
        units.loc[0, m.COMP[0]] = "4"

        units.to_csv(
            self.w / "chain_units.csv",
            index=False,
        )

        with self.assertRaises(ValueError):
            m.validate_units(self.w)

    def test_score_three_needs_traceability(self):
        self.annotate()
        units = m.read(self.w / "chain_units.csv")

        # Score 3 is valid only with a traceability reference.
        # This fixture deliberately lacks that reference.
        units.loc[0, m.COMP[0]] = "3"

        units.to_csv(
            self.w / "chain_units.csv",
            index=False,
        )

        with self.assertRaises(ValueError):
            m.validate_units(self.w)

    def test_bootstrap_small_sample_is_not_fabricated(self):
        result = m.cluster_intervals(
            np.array([True]),
            np.array([True]),
            np.array([1]),
            np.array(["one"]),
        )

        self.assertTrue(
            all(np.isnan(value) for value in result.values())
        )

    def test_estimable_context_adjustment(self):
        rng = np.random.default_rng(10)
        n = 60

        frame = pd.DataFrame(
            {
                "Country": ["A", "B"] * 30,
                "template_fingerprint": ["x", "x", "y", "y"] * 15,
                "answer_words": rng.integers(50, 2000, n),
            }
        )

        frame["strict"] = (
            10
            + 2 * np.log1p(frame.answer_words)
            + rng.normal(0, 1, n)
        )

        coefficients, info = m.adjust_context(frame)

        self.assertEqual(info["status"], "estimated")
        self.assertIn(
            "log_answer_words",
            set(coefficients.term),
        )

    def test_bootstrap_with_enough_companies(self):
        result = m.cluster_intervals(
            np.array([True, False] * 6),
            np.array([True, True] * 6),
            np.ones(12),
            np.repeat(np.arange(6), 2),
        )

        self.assertTrue(
            all(np.isfinite(value) for value in result.values())
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)