# Completed AI-reviewed CSV drafts — Team LogicFlow

These five CSVs now contain actual AI semantic assessments of the supplied text. They are NOT the earlier blank templates or regex-score suggestions. They are also NOT independent human annotations or a publication-ready validated dataset.

## Contents

| File | Completed AI work |
| --- | --- |
| coder_A.csv | 190 answers assessed in a separate AI reviewer context |
| coder_B.csv | 190 answers assessed independently in a second AI reviewer context |
| adjudicated_sample.csv | 190 AI reconciliations: 134 full-score agreements retained; 56 disputed answers reread and explicitly resolved |
| chain_units.csv | 267 selected, aggregated control-stage units from 53 reports |
| coverage.csv | All 212 report-stage applicability/coverage decisions |

Source sample IDs, questions, answer text and sampling membership are preserved. Supporting quotations and link quotations were mechanically checked against cited eligible answer text. All five CSVs identify reviewer_type=AI and human_validation_status=PENDING. In chain/coverage files reviewed=1 or review_complete=1 means completed AI review only.

## What remains

1. Independently check the proposed judgments against the codebook and source reports before adopting them as final research labels. Two AI contexts are not two humans; they share an underlying model and can make correlated errors.
2. Verify artifact/reference interpretation, current versus planned controls, same-control links, role-specific stage applicability and scope/aggregation of the selected units.
3. Main controls are a salient selection/aggregation after full-report reading, NOT an exhaustive enumeration of every governance control. The denominator is not an independently established universe of all corporate controls. Do not claim exhaustive control prevalence or operating effectiveness from these selected units.
4. External documents and URLs were not opened for this review. Some sampled-answer ratings of3 refer to an identifiable artifact/reference as reported in the answer; they are provisional and require verification. Main full-report coders conservatively capped ratings at2 because artifacts were not independently verified. Resolve that interpretive difference before final threshold comparisons or publication.
5. Document AI assistance and any amendment from the original independent-human-coding plan. If the intended validation is human inter-rater reliability or human gold-standard accuracy, obtain genuinely independent human ratings. Do not present AI agreement as human agreement or AI reference labels as independently verified ground truth.

## Use the files without losing work

Keep this ZIP and your previous files. First review AI_REVIEW_PROTOCOL.md and VALIDATION_REPORT.json. Inspect the files in a separate folder; do not automatically overwrite completed human work.

If you choose to examine compatibility with your existing frozen sample, back up the five existing review CSVs, then copy ONLY the five corresponding CSVs into that workspace. Confirm the row IDs, questions and answers belong to that exact sample. Do not replace eligibility.csv, frozen.json, locked corpus/sample/rules or source code with this package.

```powershell
python implementation.py status --workspace study_run3
python implementation.py evaluate --workspace study_run3
python implementation.py analyse --workspace study_run3
```

The existing implementation ignores the added provenance columns. Therefore it may produce numeric output from these AI drafts without requiring a human approval flag. That software behavior does not make the labels human-validated. Label any such output as exploratory AI-coded disclosure analysis. Do not submit it as the original human-validated final study.

## Verification performed

All 190 sampled answers were checked for source identity, unique IDs, score ranges and verbatim quotations. All 267 units and 212 stage records were checked for eligible source IDs, source quotations, unique keys and applicability consistency. The existing implementation's validate_units and evaluate functions were exercised on a temporary copy using these AI review files; see VALIDATION_REPORT.json. No main results ZIP or final manuscript has been fabricated or certified.

The original Git checkout had line-ending changes in frozen inputs. For that temporary compatibility test only, byte representations were restored ONLY when they exactly reproduced the original recorded SHA256. Original frozen hashes were not changed, and no corrected frozen inputs are supplied here. This package does not itself repair your Git configuration or regenerate your study.

## Audit files

- AI_REVIEW_PROTOCOL.md: reviewer process and methodological limitations.
- AI_REVIEW_LOG.json: report-level reading scope, control selection and caveats.
- AI_ADJUDICATION_AUDIT.json: both original score vectors and reasons for all56 disputed decisions.
- VALIDATION_REPORT.json: structural/source/integrity checks and compatibility status.
- CODEBOOK.md: unchanged original human coding protocol.
- FILE_CHECKSUMS.json: checksums of delivered files.
