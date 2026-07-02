ARG TARGET=archivematica-acceptance-tests

ARG UBUNTU_VERSION=24.04
# Keep these in sync with tool.uv.required-version in pyproject.toml.
ARG UV_VERSION=0.11.30
ARG UV_DIGEST=sha256:93b61e21202b1dab861092748e46bbd6e0e41dd84f59b9174efd2353186e1b47
ARG PYTHON_INSTALL_DIR=/python

FROM ghcr.io/astral-sh/uv:${UV_VERSION}@${UV_DIGEST} AS uv

FROM ubuntu:${UBUNTU_VERSION} AS base

ARG USER_ID=1000
ARG GROUP_ID=1000
ARG PYTHON_VERSION=3.10
ARG PYTHON_INSTALL_DIR=/python
ARG SELENIUM_DIR=/selenium

ENV DEBIAN_FRONTEND=noninteractive

# Ubuntu 24.04 and later Docker images include a default user with UID (1000)
# and GID (1000). Remove this user to prevent conflicts with the USER_ID and
# GROUP_ID build arguments.
RUN set -ex \
	&& id -u ubuntu >/dev/null 2>&1 \
	&& userdel --remove ubuntu || true

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
	--mount=type=cache,target=/var/lib/apt,sharing=locked \
	set -ex \
	&& apt-get -qqy update \
	&& apt-get -qqy --no-install-recommends install \
		ca-certificates \
		curl \
		git \
		gnupg \
		jq \
		locales

RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

ENV PATH=${PYTHON_INSTALL_DIR}/venv/bin:${SELENIUM_DIR}/bin:$PATH

# -----------------------------------------------------------------------------

FROM base AS browsers-builder

ARG SELENIUM_DIR=/selenium

RUN set -ex \
	&& SELENIUM_CACHE=${SELENIUM_DIR}/cache \
	&& SELENIUM_BIN=${SELENIUM_DIR}/bin \
	&& mkdir -p $SELENIUM_CACHE $SELENIUM_BIN \
	&& SELENIUM_MANAGER_DOWNLOAD_URL=$(curl -sL -o /dev/null -w '%{url_effective}' https://github.com/SeleniumHQ/selenium_manager_artifacts/releases/latest | sed -e 's|/tag/\(.*\)|/download/\1/selenium-manager-linux|g') \
	&& curl -o $SELENIUM_BIN/selenium-manager -L $SELENIUM_MANAGER_DOWNLOAD_URL \
	&& chmod +x $SELENIUM_BIN/selenium-manager \
	&& CHROME_OUTPUT=$($SELENIUM_BIN/selenium-manager --cache-path $SELENIUM_CACHE --browser chrome --output JSON) \
	&& FIREFOX_OUTPUT=$($SELENIUM_BIN/selenium-manager --cache-path $SELENIUM_CACHE --browser firefox --output JSON) \
	&& ln -s $(echo $CHROME_OUTPUT | jq -r '.result.browser_path') $SELENIUM_BIN/google-chrome \
	&& ln -s $(echo $CHROME_OUTPUT | jq -r '.result.driver_path') $SELENIUM_BIN/chromedriver \
	&& ln -s $(echo $FIREFOX_OUTPUT | jq -r '.result.browser_path') $SELENIUM_BIN/firefox \
	&& ln -s $(echo $FIREFOX_OUTPUT | jq -r '.result.driver_path') $SELENIUM_BIN/geckodriver

# -----------------------------------------------------------------------------

FROM base AS python-builder

ARG PYTHON_VERSION

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python
ENV UV_PYTHON_INSTALL_DIR=${PYTHON_INSTALL_DIR}/managed
ENV UV_PYTHON_PREFERENCE=only-managed
ENV UV_PROJECT_ENVIRONMENT=${PYTHON_INSTALL_DIR}/venv

COPY --from=uv --link /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
	set -ex \
	&& uv python install --no-bin ${PYTHON_VERSION} \
	&& uv sync --locked --no-install-project --python ${PYTHON_VERSION}

# -----------------------------------------------------------------------------

FROM base AS archivematica-acceptance-tests

ARG USER_ID=1000
ARG GROUP_ID=1000
ARG PYTHON_INSTALL_DIR=/python

ENV SE_MANAGER_PATH=${SELENIUM_DIR}/bin/selenium-manager
ENV SE_CHROME_PATH=${SELENIUM_DIR}/bin/google-chrome
ENV SE_FIREFOX_PATH=${SELENIUM_DIR}/bin/firefox

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
	--mount=type=cache,target=/var/lib/apt,sharing=locked \
	set -ex \
	&& apt-get -qqy update \
	&& apt-get -qqy --no-install-recommends install \
		bzip2 \
		libasound2t64 \
		libdbus-glib-1-2 \
		libdrm2 \
		libgbm1 \
		libglib2.0-0 \
		libgtk-3-0 \
		libnss3 \
		libx11-xcb1 \
		libxcb1 \
		libxslt-dev \
		libxtst6 \
		make \
		openssh-client \
		p7zip-full \
		tzdata \
		unzip

COPY --chown=${USER_ID}:${GROUP_ID} --from=browsers-builder --link /selenium /selenium
COPY --chown=${USER_ID}:${GROUP_ID} --from=python-builder --link ${PYTHON_INSTALL_DIR} ${PYTHON_INSTALL_DIR}
COPY --chown=${USER_ID}:${GROUP_ID} --link . /home/artefactual/acceptance-tests

RUN set -ex \
	&& if getent group ${GROUP_ID} >/dev/null; then \
		GROUP_NAME=$(getent group ${GROUP_ID} | cut -d: -f1); \
	else \
		GROUP_NAME=artefactual; \
		groupadd --gid ${GROUP_ID} ${GROUP_NAME}; \
	fi \
	&& useradd --uid ${USER_ID} --gid ${GROUP_ID} --create-home artefactual

WORKDIR /home/artefactual/acceptance-tests

USER artefactual
