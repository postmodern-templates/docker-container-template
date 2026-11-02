#!/usr/bin/env bash
# Runs the command as the image's non-root user, or as `docker run --user`'s. To give
# that user the host's IDs instead, so files on a bind mount keep the right owner:
#   docker run --user 0 -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" ...
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  if [ -n "${HOST_UID:-}${HOST_GID:-}" ]; then
    echo "HOST_UID and HOST_GID need --user 0, or use --user \"\$(id -u):\$(id -g)\" alone." >&2
    exit 1
  fi
  # A --user ID with no passwd entry gets HOME=/, which it can't write to.
  [ -w "${HOME:-/}" ] || export HOME=/tmp
  exec "$@"
fi

for id in "${HOST_UID:-}" "${HOST_GID:-}"; do
  if ! [[ "${id}" =~ ^[1-9][0-9]*$ ]]; then
    echo "--user 0 needs HOST_UID and HOST_GID set to non-zero numeric IDs." >&2
    exit 1
  fi
done

# The Dockerfile's USER, under whatever name the base image gives it.
IFS=: read -r APP_USER _ _ _ _ APP_HOME _ < <(getent passwd 1000)
usermod -o -u "${HOST_UID}" "${APP_USER}" >/dev/null
groupmod -o -g "${HOST_GID}" "${APP_USER}" >/dev/null

# setpriv leaves HOME as root's.
export HOME="${APP_HOME}"
# exec makes the command PID 1, so it receives the signal from `docker stop`.
exec setpriv --reuid="${HOST_UID}" --regid="${HOST_GID}" --clear-groups \
  --no-new-privs --bounding-set=-all --inh-caps=-all "$@"
