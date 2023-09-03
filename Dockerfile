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
		wget \
		xz-utils \
		zlib1g-dev \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ENV PYENV_ROOT="/pyenv/data"
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN set -ex \
	&& groupadd --gid ${GROUP_ID} artefactual \
	&& useradd --uid ${USER_ID} --gid ${GROUP_ID} --create-home artefactual \
	&& mkdir -p /pyenv /home/artefactual/acceptance-tests \
	&& chown -R artefactual:artefactual /pyenv /home/artefactual/acceptance-tests

#
# Chrome
#

ARG CHROME_VERSION="google-chrome-stable"
RUN CHROME_STABLE_VERSION=$(wget -qO- https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.version') \
	&& CHROME_VERSION=$(if [ ${CHROME_VERSION:-google-chrome-stable} = "google-chrome-stable" ]; then echo $CHROME_STABLE_VERSION; else echo $CHROME_VERSION; fi) \
	&& CHROME_DOWNLOAD_URL=$(wget -qO- https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | jq -r --arg version "$CHROME_VERSION" '.versions[] | select(.version == $version) | .downloads.chrome[] | select(.platform == "linux64") | .url') \
	&& echo "Using chrome version: "$CHROME_VERSION \
	&& wget --no-verbose -O /tmp/chrome_linux64.zip $CHROME_DOWNLOAD_URL \
	&& unzip /tmp/chrome_linux64.zip -d /opt/chrome-$CHROME_VERSION \
	&& rm /tmp/chrome_linux64.zip \
	&& chmod 755 /opt/chrome-$CHROME_VERSION/chrome-linux64/chrome \
	&& ln -fs /opt/chrome-$CHROME_VERSION/chrome-linux64/chrome /usr/bin/google-chrome

ARG CHROME_DRIVER_VERSION="latest"
RUN CHROMEDRIVER_STABLE_VERSION=$(wget -qO- https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.version') \
	&& CHROMEDRIVER_VERSION=$(if [ ${CHROME_DRIVER_VERSION:-latest} = "latest" ]; then echo $CHROMEDRIVER_STABLE_VERSION; else echo $CHROME_DRIVER_VERSION; fi) \
	&& CHROMEDRIVER_DOWNLOAD_URL=$(wget -qO- https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | jq -r --arg version "$CHROMEDRIVER_VERSION" '.versions[] | select(.version == $version) | .downloads.chromedriver[] | select(.platform == "linux64") | .url') \
	&& echo "Using chromedriver version: "$CHROMEDRIVER_VERSION \
	&& wget --no-verbose -O /tmp/chromedriver_linux64.zip $CHROMEDRIVER_DOWNLOAD_URL \
	&& unzip /tmp/chromedriver_linux64.zip -d /opt/chromedriver-$CHROMEDRIVER_VERSION \
	&& rm /tmp/chromedriver_linux64.zip \
	&& chmod 755 /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver-linux64/chromedriver \
	&& ln -fs /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver-linux64/chromedriver /usr/bin/chromedriver

#
# Firefox
#

ARG FIREFOX_VERSION=117.0
RUN FIREFOX_DOWNLOAD_URL=$(if [ $FIREFOX_VERSION = "latest" ] || [ $FIREFOX_VERSION = "nightly-latest" ] || [ $FIREFOX_VERSION = "devedition-latest" ]; then echo "https://download.mozilla.org/?product=firefox-$FIREFOX_VERSION-ssl&os=linux64&lang=en-US"; else echo "https://download-installer.cdn.mozilla.net/pub/firefox/releases/$FIREFOX_VERSION/linux-x86_64/en-US/firefox-$FIREFOX_VERSION.tar.bz2"; fi) \
	&& apt-get update -qqy \
	&& apt-get -qqy --no-install-recommends install firefox \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
	&& wget --no-verbose -O /tmp/firefox.tar.bz2 $FIREFOX_DOWNLOAD_URL \
	&& apt-get -y purge firefox \
	&& rm -rf /opt/firefox \
	&& tar -C /opt -xjf /tmp/firefox.tar.bz2 \
	&& rm /tmp/firefox.tar.bz2 \
	&& mv /opt/firefox /opt/firefox-$FIREFOX_VERSION \
	&& ln -fs /opt/firefox-$FIREFOX_VERSION/firefox /usr/bin/firefox

ARG GECKODRIVER_VERSION=0.33.0
RUN GK_VERSION=$(if [ ${GECKODRIVER_VERSION:-latest} = "latest" ]; then echo $(wget -qO- "https://api.github.com/repos/mozilla/geckodriver/releases/latest" | grep '"tag_name":' | sed -E 's/.*"v([0-9.]+)".*/\1/'); else echo $GECKODRIVER_VERSION; fi) \
	&& echo "Using GeckoDriver version: "$GK_VERSION \
	&& wget --no-verbose -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v$GK_VERSION/geckodriver-v$GK_VERSION-linux64.tar.gz \
	&& rm -rf /opt/geckodriver \
	&& tar -C /opt -zxf /tmp/geckodriver.tar.gz \
	&& rm /tmp/geckodriver.tar.gz \
	&& mv /opt/geckodriver /opt/geckodriver-$GK_VERSION \
	&& chmod 755 /opt/geckodriver-$GK_VERSION \
	&& ln -fs /opt/geckodriver-$GK_VERSION /usr/bin/geckodriver

USER artefactual

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

