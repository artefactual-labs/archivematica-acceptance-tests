ARG TARGET=archivematica-acceptance-tests

ARG UBUNTU_VERSION=24.04
# Pin the Docker tool image independently for reproducible builds.
ARG UV_VERSION=0.11.30
ARG UV_DIGEST=sha256:93b61e21202b1dab861092748e46bbd6e0e41dd84f59b9174efd2353186e1b47
ARG PYTHON_INSTALL_DIR=/python

FROM ghcr.io/astral-sh/uv:${UV_VERSION}@${UV_DIGEST} AS uv

FROM ubuntu:${UBUNTU_VERSION} AS base

ARG USER_ID=1000
ARG GROUP_ID=1000
ARG PYTHON_INSTALL_DIR=/python

ENV DEBIAN_FRONTEND=noninteractive

# Ubuntu 24.04 and later Docker images include a default user with UID (1000)
# and GID (1000). Remove it before creating the runtime user with configurable
# identifiers.
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
		locales \
		unzip

RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV PATH=${PYTHON_INSTALL_DIR}/venv/bin:$PATH

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

COPY .python-version pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
	set -ex \
	&& if [ -n "${PYTHON_VERSION}" ]; then \
		uv python install --no-bin "${PYTHON_VERSION}"; \
		uv sync --locked --no-install-project --python "${PYTHON_VERSION}"; \
	else \
		uv python install --no-bin; \
		uv sync --locked --no-install-project; \
	fi

# -----------------------------------------------------------------------------

FROM base AS browsers-builder

ARG TARGETARCH
ARG TARGETOS
ARG PYTHON_INSTALL_DIR=/python

ENV PLAYWRIGHT_BROWSERS_PATH=/playwright
ENV CHROME_INSTALL_DIR=/opt/chrome

COPY --from=python-builder --link ${PYTHON_INSTALL_DIR} ${PYTHON_INSTALL_DIR}
COPY scripts/install-chrome.sh /usr/local/bin/install-chrome

# Install browser binaries: project-managed Chrome/Chromium and Playwright Firefox.
RUN set -ex \
	&& bash /usr/local/bin/install-chrome \
	&& playwright install firefox

# -----------------------------------------------------------------------------

FROM base AS archivematica-acceptance-tests

ARG USER_ID=1000
ARG GROUP_ID=1000
ARG PYTHON_INSTALL_DIR=/python

ENV PLAYWRIGHT_BROWSERS_PATH=/playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV CHROME_EXECUTABLE_PATH=/opt/chrome/chrome

COPY --from=python-builder --link ${PYTHON_INSTALL_DIR} ${PYTHON_INSTALL_DIR}
COPY --from=browsers-builder --link /playwright /playwright
COPY --from=browsers-builder --link /opt/chrome /opt/chrome

# install-deps adds runtime OS libraries only; browser binaries were copied above.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
	--mount=type=cache,target=/var/lib/apt,sharing=locked \
	set -ex \
	&& playwright install-deps chromium firefox \
	&& apt-get -qqy --no-install-recommends install \
		bzip2 \
		make \
		openssh-client \
		p7zip-full \
		tzdata

COPY --chown=${USER_ID}:${GROUP_ID} --link . /home/artefactual/acceptance-tests

RUN set -ex \
	&& if getent group ${GROUP_ID} >/dev/null; then \
		GROUP_NAME=$(getent group ${GROUP_ID} | cut -d: -f1); \
	else \
		GROUP_NAME=artefactual; \
		groupadd --gid ${GROUP_ID} ${GROUP_NAME}; \
	fi \
	&& useradd --uid ${USER_ID} --gid ${GROUP_ID} --create-home artefactual \
	&& chown -R ${USER_ID}:${GROUP_ID} /playwright /opt/chrome

WORKDIR /home/artefactual/acceptance-tests

USER artefactual
