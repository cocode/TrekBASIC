#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 program.bas"
  exit 1
fi

basfile="$1"
if [[ ! -f "$basfile" ]]; then
  echo "Error: File not found: $basfile"
  exit 1
fi

# Derive base name without extension
base="${basfile%.*}"
llfile="${base}.ll"
exe="${base}"

echo "Generating LLVM IR from $basfile → $llfile"
# If basic.py writes to stdout LLVM IR, redirect; otherwise adapt as needed
python basic.py "$basfile" > "$llfile"

echo "Compiling $llfile → $exe"
clang "$llfile" -o "$exe"

echo "Running $exe"
"./$exe"
