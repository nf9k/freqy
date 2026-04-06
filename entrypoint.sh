#!/bin/sh
# Ensure APP_VERSION reflects the version baked into the image at build time,
# overriding any stale value that may be set in the env file.
export APP_VERSION="${_FREQY_VERSION:-dev}"
exec "$@"
