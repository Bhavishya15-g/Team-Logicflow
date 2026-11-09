# Aligned codebook version 3

## Construct definitions and scale
Use the proposal's responsibility, procedure, assurance and failure_response framework.

Responsibility: accountable decision role, authority or oversight mandate.
Procedure: operational governance routine, decision process or repeatable control.
Assurance: checking/testing/audit arrangements and the evidence supporting their operation. An audit mention alone is not an identified audit output.
Failure_response: escalation, remediation, redress or corrective arrangements.

0 = no evidence disclosed after full-scope review.
1 = generic statement or mention.
2 = a concrete mechanism or arrangement.
3 = a traceable mechanism with an identifiable artifact, reference or dated record.

Every component at least 2 and all three explicit links are required for substantive complete-chain disclosure. The lenient threshold uses components at least 1, with links still required. Detail score is total component ratings divided by12 times100. These are study-specific disclosure measures, not governance-effectiveness or compliance certifications.

## Links
responsibility_procedure, procedure_assurance, assurance_failure_response are binary. Score 1 only when cited text explicitly connects the components for the SAME control. Co-occurrence does not establish linkage. Record exact link_quote and explanatory review_note. Current controls and future intentions must be distinguished; intentions do not establish an operational control.

## Eligibility
Use verifiable identity sources, canonical IDs for confirmed aliases and explicit corporate eligibility decisions. Resolve duplicate canonical-company/period source selection before freeze. Do not infer aliases or sectors from names alone. If exclusions or source rules change after freeze, version the study.

## Main reviewed chain coding
chain_units.csv: unit_id unique; report_id from eligible_reports.csv; stable control_id within a canonical company; lifecycle stage; row_ids separated by |; exact supporting quote; four component scores; three link scores; link_quote; artifact_access public/internal/unclear/none; artifact_url if public; reviewed=1; review_note; traceability_reference when any component receives 3.

Code one aggregated governance CONTROL per report-stage, supporting it with one or several answers. A control can occur in several stages. Match controls across stages/reports only with substantive evidence. The code checks source IDs/quotes and score ranges, but cannot establish semantic validity on its own. For score3, record the specific artifact/reference/date and verify that it supports traceability; this check is the reviewers' responsibility. Public URLs must be checked by reviewers and the date recorded. The code does not automatically validate external content.

coverage.csv: every eligible report and four lifecycle stages requires applicable 0/1, review_complete=1, scope and rationale. Applicable stage with no disclosed control requires ONE all-zero placeholder with documented complete search. Inapplicable stage receives no units. Missing answers alone do not establish inapplicability or absent practice.

## Independent sample validation
Use blinded coder_A.csv and coder_B.csv independently. Every frozen sampled answer needs the four 0–3 ratings and three link ratings. The sampled ANSWER is the validation unit; links dispersed across answers are assessed separately in the main control coding. Preserve positive source quotations, uncertainty notes and original ratings. Do not discuss labels before recording independent decisions.

Reconcile into adjudicated_sample.csv with an adjudication_note on every row. Evaluation uses held-out canonical companies only and compares lexical candidates with gold substantive evidence (rating>=2), plus complete-chain gold (all components>=2 and all links1). It reuses frozen design weights. Do not alter sampling membership after seeing results. Undefined kappa and insufficient bootstrap information remain missing.

Main report-control ratings also require a documented independent review/adjudication procedure. Sampled answer agreement is not by itself a validation of every report-level control judgment.

## Interpretation
No evidence in this public corpus does not establish no internal practice. A chain rate measures disclosed connections, not operating effectiveness. Principles and governance evidence are different constructs. Country/period comparisons remain descriptive. Record sampling/self-selection, role applicability, template differences, uncertain matches, inaccessible evidence and reporting-length sensitivity.
