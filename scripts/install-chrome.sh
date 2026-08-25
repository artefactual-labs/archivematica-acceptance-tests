#!/usr/bin/env bash

set -euo pipefail

chrome_for_testing_version="151.0.7922.174"
install_dir="${CHROME_INSTALL_DIR:-${PWD}/.cache/chrome}"
architecture="${TARGETARCH:-$(uname -m)}"
operating_system="${TARGETOS:-$(uname -s)}"

if [[ -z "${install_dir}" || "${install_dir}" == "/" ]]; then
    echo "Refusing unsafe Chrome installation directory: ${install_dir}" >&2
    exit 1
fi

case "${operating_system}:${architecture}" in
    Linux:amd64|Linux:x86_64|linux:amd64)
        platform="linux64"
        executable="chrome"
        ;;
    Linux:arm64|Linux:aarch64|linux:arm64)
        # Chrome for Testing Stable does not yet publish linux-arm64. When
        # updating chrome_for_testing_version, check the availability dashboard
        # and replace this fallback once Stable lists that artifact:
        # https://googlechromelabs.github.io/chrome-for-testing/
        playwright install chromium >&2
        chromium_install_dir="$(
            playwright install --dry-run chromium |
                awk '/Install location:/ {
                    sub(/^[^:]+:[[:space:]]*/, "")
                    print
                    exit
                }'
        )"
        chromium_executable="${chromium_install_dir}/chrome-linux/chrome"
        if [[ ! -x "${chromium_executable}" ]]; then
            echo "Unable to locate Playwright Chromium: ${chromium_executable}" >&2
            exit 1
        fi
        rm -rf "${install_dir}"
        mkdir -p "${install_dir}"
        ln -s "${chromium_executable}" "${install_dir}/chrome"
        echo "${install_dir}/chrome"
        exit 0
        ;;
    Darwin:amd64|Darwin:x86_64|darwin:amd64)
        platform="mac-x64"
        executable="Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
        ;;
    Darwin:arm64|Darwin:aarch64|darwin:arm64)
        platform="mac-arm64"
        executable="Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
        ;;
    *)
        echo "Unsupported Chrome platform: ${operating_system}/${architecture}" >&2
        exit 1
        ;;
esac

temporary_dir="$(mktemp -d)"
trap 'rm -rf "${temporary_dir}"' EXIT

archive="chrome-${platform}.zip"
url="https://storage.googleapis.com/chrome-for-testing-public/${chrome_for_testing_version}/${platform}/${archive}"
curl --location --fail --silent --show-error --output "${temporary_dir}/${archive}" "${url}"
unzip -q "${temporary_dir}/${archive}" -d "${temporary_dir}"

rm -rf "${install_dir}"
mkdir -p "$(dirname "${install_dir}")"
mv "${temporary_dir}/chrome-${platform}" "${install_dir}"

echo "${install_dir}/${executable}"
