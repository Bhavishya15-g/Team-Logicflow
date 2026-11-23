"""Prepare a separate AI-reviewed LogicFlow workspace with verified frozen bytes.

Place beside implementation.py and run after installing requirements.txt.
Uses the standard library. The existing frozen hashes remain the authority.
"""

import argparse
import csv
import hashlib
import io
import json
import shutil
import tempfile
from pathlib import Path


REVIEWS = [
    "coder_A.csv", "coder_B.csv", "adjudicated_sample.csv",
    "chain_units.csv", "coverage.csv",
]
COMPONENTS = ["responsibility", "procedure", "assurance", "failure_response"]
LINKS = [
    "responsibility_procedure", "procedure_assurance",
    "assurance_failure_response",
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_csv(path):
    # Normalize physical text line endings, including quoted multiline fields.
    text = path.read_bytes().decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    reader = csv.DictReader(io.StringIO(text))
    return reader.fieldnames, list(reader)


def restore_recorded_bytes(path, expected):
    data = path.read_bytes()
    lf = data.replace(b"\r\n", b"\n")
    variants = [data, lf, lf.replace(b"\n", b"\r\n")]
    if path.suffix.lower() == ".csv":
        rows = csv.reader(io.StringIO(lf.decode("utf-8-sig")))
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\r\n").writerows(rows)
        variants.append(buffer.getvalue().encode("utf-8"))
    for candidate in variants:
        if digest(candidate) == expected:
            return candidate
    raise ValueError(
        f"{path.name}: line-ending restoration cannot reproduce the frozen hash. "
        "Recover the original file or create a documented new study version."
    )


def check_ratings(rows, filename):
    for row in rows:
        for column in COMPONENTS + LINKS:
            allowed = {"0", "1", "2", "3"} if column in COMPONENTS else {"0", "1"}
            if row.get(column) not in allowed:
                raise ValueError(f"{filename}: incomplete or invalid {column}.")


def prepare(project, source_name, destination_name):
    source = project / source_name
    destination = project / destination_name
    if source.parent != project or destination.parent != project:
        raise ValueError("Workspace names must be direct project subfolders.")
    if destination.exists():
        raise ValueError(
            f"{destination.name} already exists. Use --workspace study_ai_run4 "
            "or another unused name."
        )

    frozen_bytes = (source / "frozen.json").read_bytes()
    frozen = json.loads(frozen_bytes)
    for name, key in [
        ("implementation.py", "implementation_sha256"),
        ("exploratory.py", "exploratory_sha256"),
    ]:
        if digest((project / name).read_bytes()) != frozen[key]:
            raise ValueError(f"{name} differs from the frozen code version. Restore that exact version first.")

    staging = Path(tempfile.mkdtemp(prefix=".logicflow_setup_", dir=project))
    try:
        expected = dict(frozen["locked_files"])
        expected["eligibility.csv"] = frozen["eligibility_sha256"]
        for name, expected_hash in expected.items():
            if Path(name).name != name:
                raise ValueError("Unexpected nested path in frozen manifest.")
            restored = restore_recorded_bytes(source / name, expected_hash)
            (staging / name).write_bytes(restored)
            print(f"Verified original frozen hash: {name}")
        (staging / "frozen.json").write_bytes(frozen_bytes)

        for name in [
            "principles.csv", "study.json", "report_inventory.csv",
            "answer_features_and_audit.csv", "source_row_provenance.csv",
        ]:
            if name not in expected and (source / name).exists():
                shutil.copyfile(source / name, staging / name)

        _, design = read_csv(staging / "frozen_sample.csv")
        design_ids = {row["row_id"] for row in design}
        _, answers = read_csv(staging / "eligible_answers.csv")
        answer_map = {row["row_id"]: row for row in answers}
        counts = {}
        for name in REVIEWS:
            headers, rows = read_csv(project / name)
            if not headers or not rows:
                raise ValueError(f"Root-level {name} is empty or missing its header.")
            if name in REVIEWS[:3]:
                ids = [row["row_id"] for row in rows]
                if len(set(ids)) != len(ids) or set(ids) != design_ids:
                    raise ValueError(f"{name}: rows do not match the frozen sample.")
                for row in rows:
                    reference = answer_map[row["row_id"]]
                    for column in ["report_id", "canonical_id", "question", "answer"]:
                        if row[column] != reference[column]:
                            raise ValueError(f"{name}: source mismatch in {column}.")
                check_ratings(rows, name)
            if name == "chain_units.csv":
                check_ratings(rows, name)
            if name == "coverage.csv":
                if any(row.get("applicable") not in {"0", "1"} or row.get("review_complete") != "1" for row in rows):
                    raise ValueError("coverage.csv: review decisions remain incomplete.")
            with (staging / name).open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            counts[name] = len(rows)

        for name in ["AI_REVIEW_PROTOCOL.md", "READ_FIRST.md", "AI_REVIEW_LOG.json", "AI_ADJUDICATION_AUDIT.json"]:
            if (project / name).exists():
                shutil.copyfile(project / name, staging / name)
        (staging / "WORKSPACE_PROVENANCE.json").write_text(
            json.dumps({
                "source_workspace": source_name,
                "annotation_provenance": "AI-reviewed drafts; human validation pending",
                "restoration": "Each locked input matches its existing frozen SHA256.",
                "review_rows": counts,
            }, indent=2), encoding="utf-8",
        )
        staging.rename(destination)
        print(f"\nREADY: {destination}")
        for name, count in counts.items():
            print(f"{name}: {count} rows")
        print("AI-reviewed analysis copy prepared. Human evidence validation remains pending.")
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="study_run3")
    parser.add_argument("--workspace", default="study_ai_run3")
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    try:
        prepare(project, args.source, args.workspace)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"Setup stopped: {error}\n")


if __name__ == "__main__":
    main()
