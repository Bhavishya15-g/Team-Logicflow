# LogicFlow aligned research implementation

This version aligns the main analysis with the research questions and 0–3 scoring framework in Corporate_AI_Research_Proposal.docx from your uploaded project. It is not a certification of publication readiness. Real human reviews and a defensible scholarly contribution remain necessary.

## Start in VS Code
Extract the ZIP and open the LogicFlow_Aligned folder. The CSV is included beside the scripts.

```powershell
python -m pip install -r requirements.txt
python implementation.py prepare
python implementation.py status
```

The existing exploratory.py generates automatic candidate results. They remain exploratory and do not constitute the main reviewed findings. Preparation is repeat-safe and does not overwrite an existing study. New output uses a separate study_aligned directory so earlier scoring versions are not mixed.

For another CSV path:
```powershell
python implementation.py prepare --data "C:\Users\bhavi\Downloads\transparency-reports-export.csv"
```

## What you do next
1. Complete study_aligned/eligibility.csv using verifiable organisation identity sources. Review every row, set corporate_eligible to 0 or 1, supply canonical_id for included companies, identity_source and decision_note. Canonical IDs keep aliases together in pilot/held-out splits.
2. Run `python implementation.py freeze`. It fixes the selected corpus, lexical predictions, company-level sample split, sampling weights and code hashes. Do not edit frozen inputs. Rule/code changes require a NEW workspace/version, retaining the prior records.
3. Independently complete coder_A.csv and coder_B.csv, and then reconcile their judgments into adjudicated_sample.csv. Complete report-control-stage coding in chain_units.csv and full-scope applicability review in coverage.csv. Read CODEBOOK.md before scoring.
4. Run `python implementation.py evaluate` for the held-out validation outputs.
5. Run `python implementation.py analyse` for the sixteen main reviewed figures/tables. This stage requires completed reviewed codes AND independent/adjudicated evaluation data. It stops with a specific message when either is missing.

Use `python implementation.py status` whenever you need a list of missing files/blank required fields. A zero blank count is a progress indicator, not proof of semantic validity.

## Exact research question alignment
- RQ1 evidence depth for responsibility, procedure, assurance and failure_response: reviewed specificity heatmap, detail/completeness plot, specificity prevalence and threshold sensitivity.
- RQ2 explicit links and chain breaks: lifecycle specificity, reviewed chain rate, missing components/links and same-control continuity.
- RQ3 contextual comparison: country and period figures, sample/questionnaire composition, and descriptive country contrasts adjusted for log response-word count and questionnaire fingerprint. The HC3 model reports non-estimability when data/design are insufficient; it never silently drops the adjustment. Matched-control historical changes are supplementary. Country contrasts are noncausal and questionnaire fingerprints still require source review.
- RQ4 automated rules versus independent coding: held-out precision/recall/F1 figure, independent kappa figure, accuracy/support/uncertainty table, and agreement table. Four original screening dimensions and complete-chain prediction are assessed separately.

## Methods corrected
All human component ratings use 0/1/2/3. Substantive complete-chain disclosure requires every component at least 2 plus all three explicit links. Lenient comparison permits components at least 1, still requiring the same links. Score 3 needs a traceability reference. The main code and screening scripts are checksummed at freeze. Unknown IDs are rejected before merges; no human scores are filled automatically. Gold labels must be adjudicated after independent coding.

Main results now use reviewed codes. Principles-versus-chains exploratory plots are no longer presented as the main RQ4. principles.csv is an optional legacy supplementary template and is not required to be filled for the main study.

## Uncertainty and robustness
The evaluation includes canonical-company cluster bootstrap intervals for precision/recall/F1, using fixed inverse-stratum sampling weights. It returns missing intervals for fewer than five held-out companies or too few nondegenerate draws. Intervals are descriptive for the selected validation sample, not population-wide causal inference. Agreement refers to the selected held-out sample. A methodologist should review the final sampling/inference choices before journal submission.

RQ3 uses HC3 standard errors, requires a full-rank design with residual degrees of freedom, and reports non-estimability rather than invented coefficients. All observed question-set effects may not identify true questionnaire versions. Semantic question harmonisation, quote interpretation, source accessibility, future/current practices and novelty still require researcher review.

## Outputs
study_aligned/exploratory contains screening results and traceability.
study_aligned/evaluation_TIMESTAMP contains five-dimension validation summaries, agreement and misclassification audit.
study_aligned/reviewed_results_TIMESTAMP contains eight figures (PNG/PDF/source CSV), eight tables (full CSV/PDF preview), reviewed unit/report scores, contextual-model diagnostics, reproducibility metadata and a results ZIP. PDFs are compact previews; full records are in CSV. The .py files contain # %% section markers for reading in VS Code; run staged commands in the terminal.

## Verification
`python -m unittest -v test_reviewed.py`

Synthetic fixtures test code paths only and are never research findings. The real-data preparation is included to make the next task concrete. Eligibility and human annotations are deliberately not invented. This package excludes .venv and old mixed-version results.
