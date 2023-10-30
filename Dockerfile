ARG TARGET=archivematica-acceptance-tests

ARG UBUNTU_VERSION=22.04

FROM ubuntu:${UBUNTU_VERSION} AS base

ARG USER_ID=1000
ARG GROUP_ID=1000
ARG PYTHON_VERSION=3.9
ARG PYENV_DIR=/pyenv
ARG SELENIUM_DIR=/selenium

ENV DEBIAN_FRONTEND=noninteractive

RUN set -ex \
	&& apt-get -qqy update \
	&& apt-get -qqy --no-install-recommends install \
		ca-certificates \
		curl \
		git \
		jq \
		locales \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/*

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ENV PYENV_ROOT=${PYENV_DIR}/data
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:${SELENIUM_DIR}/bin:$PATH

# -----------------------------------------------------------------------------

FROM base AS browsers-builder

ARG SELENIUM_DIR=/selenium

RUN set -ex \
	&& SELENIUM_CACHE=${SELENIUM_DIR}/cache \
	&& SELENIUM_BIN=${SELENIUM_DIR}/bin \
	&& mkdir -p $SELENIUM_CACHE $SELENIUM_BIN \
	&& curl -o $SELENIUM_BIN/selenium-manager -L https://github.com/SeleniumHQ/selenium/raw/trunk/common/manager/linux/selenium-manager \
	&& chmod +x $SELENIUM_BIN/selenium-manager \
	&& CHROME_OUTPUT=$($SELENIUM_BIN/selenium-manager --cache-path $SELENIUM_CACHE --browser chrome --output JSON) \
	&& FIREFOX_OUTPUT=$($SELENIUM_BIN/selenium-manager --cache-path $SELENIUM_CACHE --browser firefox --output JSON) \
	&& ln -s $(echo $CHROME_OUTPUT | jq -r '.result.browser_path') $SELENIUM_BIN/google-chrome \
	&& ln -s $(echo $CHROME_OUTPUT | jq -r '.result.driver_path') $SELENIUM_BIN/chromedriver \
	&& ln -s $(echo $FIREFOX_OUTPUT | jq -r '.result.browser_path') $SELENIUM_BIN/firefox \
	&& ln -s $(echo $FIREFOX_OUTPUT | jq -r '.result.driver_path') $SELENIUM_BIN/geckodriver

# -----------------------------------------------------------------------------

FROM base AS pyenv-builder

ARG PYTHON_VERSION=3.9

RUN set -ex \
	&& apt-get -qqy update \
	&& apt-get -qqy --no-install-recommends install \
		build-essential \
		libbz2-dev \
		libffi-dev \
		liblzma-dev \
		libncursesw5-dev \
		libreadline-dev \
		libsqlite3-dev \
		libssl-dev \
		libxml2-dev \
		libxmlsec1-dev \
		tk-dev \
		xz-utils \
		zlib1g-dev \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/*

RUN set -ex \
	&& curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash \
	&& pyenv install ${PYTHON_VERSION} \
	&& pyenv global ${PYTHON_VERSION}

COPY requirements-dev.txt requirements-dev.txt

RUN set -ex \
	&& pyenv exec python${PYTHON_VERSION} -m pip install --upgrade pip setuptools \
	&& pyenv exec python${PYTHON_VERSION} -m pip install --requirement requirements-dev.txt \
	&& pyenv rehash

# -----------------------------------------------------------------------------

FROM base AS archivematica-acceptance-tests

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN set -ex \
	&& apt-get -qqy update \
	&& apt-get -qqy --no-install-recommends install \
		bzip2 \
		gnupg \
		libasound2 \
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
		unzip \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/*

COPY --chown=${USER_ID}:${GROUP_ID} --from=browsers-builder --link /selenium /selenium
COPY --chown=${USER_ID}:${GROUP_ID} --from=pyenv-builder --link /pyenv /pyenv
COPY --chown=${USER_ID}:${GROUP_ID} --link . /home/artefactual/acceptance-tests

RUN set -ex \
	&& groupadd --gid ${GROUP_ID} artefactual \
	&& useradd --uid ${USER_ID} --gid ${GROUP_ID} --create-home artefactual

WORKDIR /home/artefactual/acceptance-tests

USER artefactual
