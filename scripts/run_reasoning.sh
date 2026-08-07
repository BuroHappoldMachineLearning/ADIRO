#!/usr/bin/env bash
#
# ADIRO ontology reasoning + QC (RES-36) — the SINGLE source of truth run by
# both CI (.github/workflows/ontology-reasoning.yml) and humans locally, so a
# local run matches CI exactly.
#
# Runs an OWL 2 DL reasoner (HermiT) over all src/*.ttl merged at latest to
# check CONSISTENCY + UNSATISFIABLE classes, then ROBOT `report` for logical /
# structural QC. Imports resolve offline via src/catalog-v001.xml.
#
# Requirements: Java 11+ on PATH (see AGENTS.md "Local ontology reasoning").
# ROBOT is fetched automatically to .tools/robot.jar on first run.
#
# Usage:
#   scripts/run_reasoning.sh            # download ROBOT if needed, then run
#   REASONER=elk scripts/run_reasoning.sh
#   ROBOT_JAR=/path/to/robot.jar scripts/run_reasoning.sh
#
# Exit code: 0 always in the default (warn) mode. Set ENFORCE=1 to exit with the
# reasoner's code (non-zero on inconsistency / unsatisfiable classes / non-DL).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ROBOT_VERSION="${ROBOT_VERSION:-v1.9.10}"
ROBOT_JAR="${ROBOT_JAR:-$REPO_ROOT/.tools/robot.jar}"
REASONER="${REASONER:-hermit}"
OUT_DIR="${OUT_DIR:-$REPO_ROOT/.tools/reasoning-out}"
CATALOG="src/catalog-v001.xml"

if ! command -v java >/dev/null 2>&1; then
  echo "ERROR: 'java' not found on PATH. Install a JDK 11+ (see AGENTS.md), then open a new terminal." >&2
  exit 2
fi

if [ ! -f "$ROBOT_JAR" ]; then
  echo "Downloading ROBOT $ROBOT_VERSION -> $ROBOT_JAR"
  mkdir -p "$(dirname "$ROBOT_JAR")"
  curl -fL -o "$ROBOT_JAR" \
    "https://github.com/ontodev/robot/releases/download/${ROBOT_VERSION}/robot.jar"
fi

mkdir -p "$OUT_DIR"

# Discover all modules (new modules are picked up automatically; add a matching
# catalog entry in src/catalog-v001.xml so their imports resolve offline).
INPUTS=()
for f in src/*.ttl; do INPUTS+=(--input "$f"); done
echo "Modules: ${INPUTS[*]}"

echo "== Consistency + unsatisfiable-class check (HermiT: '$REASONER') =="
java -jar "$ROBOT_JAR" merge --catalog "$CATALOG" "${INPUTS[@]}" \
  reason --reasoner "$REASONER" --output "$OUT_DIR/reasoned.ttl" 2>&1 | tee "$OUT_DIR/reason.out"
REASON_RC=${PIPESTATUS[0]}
echo "$REASON_RC" > "$OUT_DIR/reason.rc"
echo "reason exit code: $REASON_RC"

echo "== ROBOT report (logical / structural QC) =="
java -jar "$ROBOT_JAR" merge --catalog "$CATALOG" "${INPUTS[@]}" \
  report --fail-on none --output "$OUT_DIR/report.tsv" 2>&1 | tee "$OUT_DIR/report.out" || true

if [ -f "$OUT_DIR/report.tsv" ]; then
  echo "== report summary =="
  awk -F'\t' 'NR>1{c[$1]++} END{for (l in c) printf "  %-6s %d\n", l, c[l]}' "$OUT_DIR/report.tsv"
fi

if [ "${ENFORCE:-0}" = "1" ]; then
  exit "$REASON_RC"
fi
exit 0
