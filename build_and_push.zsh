#!/usr/bin/env zsh
# build_and_push.zsh
# A simple wrapper to build with buildx and then push

set -euo pipefail

# ——— Configuration (override with environment variables if you like) ———
: ${TAG:=cwebster/eflm:bv_python_api}
: ${DOCKERFILE:=Dockerfile}
: ${PLATFORMS:=linux/amd64}

# ——— Build ———
echo "⇨ Building ${TAG} for ${PLATFORMS} using ${DOCKERFILE}"
docker buildx build --platform "${PLATFORMS}" -f "${DOCKERFILE}" -t "${TAG}" --push .

echo "✅ Build Done!"

# ——— Push ———
echo "⇨ Pushing ${TAG}"
docker push "${TAG}"

echo "✅ Done!"

