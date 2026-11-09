# Your next task

The code has been updated and preparation has already run on the included CSV. The actual study is not finished.

1. Open study_aligned/eligibility.csv. There are 46 organisation-country entries with blank review fields. Research each identity; fill canonical_id for included corporations, corporate_eligible 0/1, reviewed 1, identity_source, and decision_note. Read CODEBOOK.md. Do not guess identities.
2. Run python implementation.py freeze. This creates the fixed sample and coding files.
3. You and your teammate independently complete coder_A.csv and coder_B.csv, then adjudicate into adjudicated_sample.csv. Complete the report-control coding in chain_units.csv and lifecycle applicability in coverage.csv. Human reviews are not automatic predictions.
4. Run python implementation.py analyse. It checks complete reviewed inputs, calculates evaluation, and creates all sixteen main results. Run python implementation.py status for missing fields. Run python implementation.py evaluate separately if only validation results are wanted.

The earlier exploratory results are inside study_aligned/exploratory. Do not describe these as human-confirmed accountability findings. No missing ratings or publication claims are manufactured by this package.
