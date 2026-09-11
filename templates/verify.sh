#!/bin/sh
# Replace this stub with reviewed deterministic test/lint/build commands.
# Include every feature's verification in this one gate. Do not make the gate
# depend on passes flags or on a model's report. Evidence files named in
# features.json must be (re)written HERE and contain $HARNESS_RUN_ID so the
# completion gate can prove they came from this run's checks, not from a claim.
# Example:
#   mkdir -p artifacts
#   {{test_cmd}} > artifacts/tests.txt 2>&1
#   printf 'run=%s\n' "$HARNESS_RUN_ID" >> artifacts/tests.txt
echo "Verification is not configured. Replace templates/verify.sh for this project." >&2
exit 1
