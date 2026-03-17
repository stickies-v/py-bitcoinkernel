#!/usr/bin/env bash
#
# Post-processes clang2py output for use as src/pbk/capi/bindings.py.
#
# Replaces the clang2py stub library loader with an import of
# BITCOINKERNEL_LIB from pbk.capi.library, which handles finding
# the bundled shared library at runtime.
#
# Usage: contrib/bump-bindings/fix-bindings.sh src/pbk/capi/bindings.py

set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Usage: $0 <bindings.py>"
    exit 1
fi

FILE="$1"

# Normalize the TARGET arch line to remove local system paths
sed -i.bak 's/^# TARGET arch is: \[.*\]$/# TARGET arch is: []/' "$FILE"

# Add the import after the ctypes import line
sed -i.bak '/^import ctypes$/a\
\
from pbk.capi.library import BITCOINKERNEL_LIB
' "$FILE"

# Replace _libraries['FIXME_STUB'] references with BITCOINKERNEL_LIB
sed -i.bak "s/_libraries\['FIXME_STUB'\]/BITCOINKERNEL_LIB/g" "$FILE"

# Remove the FunctionFactoryStub block (class, comments, stub assignment)
# including 2 blank lines before and 1 after
ex -sc '/^class FunctionFactoryStub/-2,/^BITCOINKERNEL_LIB = FunctionFactoryStub.*$/+1d' -cx "$FILE"

# Clean up backup files
rm -f "$FILE.bak"
