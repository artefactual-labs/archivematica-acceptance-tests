FROM ubuntu:22.04

ARG USER_ID=1000
ARG GROUP_ID=1000
ARG PYTHON_VERSION=3.9

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

RUN set -ex \
	&& apt-get -qqy update \
	&& apt-get -qqy --no-install-recommends install \
		build-essential \
		bzip2 \
		ca-certificates \
		curl \
		git \
		gnupg \
		jq \
		libasound2 \
		libbz2-dev \
		libdbus-glib-1-2 \
		libdrm2 \
		libffi-dev \
		libgbm1 \
		libglib2.0-0 \
		libgtk-3-0 \
		liblzma-dev \
		libncursesw5-dev \
		libnss3 \
		libreadline-dev \
		libsqlite3-dev \
		libssl-dev \
		libx11-xcb1 \
		libxcb1 \
		libxml2-dev \
		libxmlsec1-dev \
		libxslt-dev \
		libxtst6 \
		locales \
		openssh-client \
		p7zip-full \
		tk-dev \
		tzdata \
		unzip \
		xz-utils \
		zlib1g-dev \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ENV PYENV_ROOT="/pyenv/data"
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:/selenium/bin:$PATH

RUN set -ex \
	&& groupadd --gid ${GROUP_ID} artefactual \
	&& useradd --uid ${USER_ID} --gid ${GROUP_ID} --create-home artefactual \
	&& mkdir -p /pyenv /selenium/bin /home/artefactual/acceptance-tests \
	&& chown -R artefactual:artefactual /pyenv /selenium /home/artefactual/acceptance-tests

USER artefactual

RUN set -ex \
	&& SELENIUM_CACHE=/selenium/cache \
	&& SELENIUM_BIN=/selenium/bin \
	&& curl -o $SELENIUM_BIN/selenium-manager -L https://github.com/SeleniumHQ/selenium/raw/trunk/common/manager/linux/selenium-manager \
	&& chmod +x $SELENIUM_BIN/selenium-manager \
	&& CHROME_OUTPUT=$(selenium-manager --cache-path $SELENIUM_CACHE --browser chrome --output JSON) \
	&& FIREFOX_OUTPUT=$(selenium-manager --cache-path $SELENIUM_CACHE --browser firefox --output JSON) \
	&& ln -s $(echo $CHROME_OUTPUT | jq -r '.result.browser_path') $SELENIUM_BIN/google-chrome \
	&& ln -s $(echo $CHROME_OUTPUT | jq -r '.result.driver_path') $SELENIUM_BIN/chromedriver \
	&& ln -s $(echo $FIREFOX_OUTPUT | jq -r '.result.browser_path') $SELENIUM_BIN/firefox \
	&& ln -s $(echo $FIREFOX_OUTPUT | jq -r '.result.driver_path') $SELENIUM_BIN/geckodriver

RUN set -ex \
	&& curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash \
	&& pyenv install ${PYTHON_VERSION} \
	&& pyenv global ${PYTHON_VERSION}

COPY requirements-dev.txt /home/artefactual/acceptance-tests/requirements-dev.txt

RUN set -ex \
	&& pyenv exec python${PYTHON_VERSION} -m pip install --upgrade pip setuptools \
	&& pyenv exec python${PYTHON_VERSION} -m pip install --requirement /home/artefactual/acceptance-tests/requirements-dev.txt \
	&& pyenv rehash

COPY . /home/artefactual/acceptance-tests
WORKDIR /home/artefactual/acceptance-tests

