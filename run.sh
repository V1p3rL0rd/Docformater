#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Forward to start_unix.sh
exec ./start_unix.sh "$@"
