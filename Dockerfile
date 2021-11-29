FROM ubuntu:18.04

RUN echo "deb http://archive.ubuntu.com/ubuntu bionic main universe\n" > /etc/apt/sources.list \
	&& echo "deb http://archive.ubuntu.com/ubuntu bionic-updates main universe\n" >> /etc/apt/sources.list \
	&& echo "deb http://security.ubuntu.com/ubuntu bionic-security main universe\n" >> /etc/apt/sources.list

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

RUN apt-get -qqy update \
	&& apt-get -qqy --no-install-recommends install \
		gnupg \
		bzip2 \
		ca-certificates \
		tzdata \
		sudo \
		unzip \
		curl \
		wget \
		git \
		build-essential \
		locales \
		openssh-client \
		p7zip-full \
		python \
		python3-pip \
		python3-setuptools \
		python3-dev \
		libxml2-dev \
		libxslt-dev \
		zlib1g-dev \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/*


# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ENV TZ "UTC"
RUN echo "${TZ}" > /etc/timezone \
	&& dpkg-reconfigure --frontend noninteractive tzdata

RUN groupadd --gid 333 archivematica \
	&& useradd --shell /bin/bash --groups sudo,archivematica --create-home artefactual \
	&& echo 'ALL ALL = (ALL) NOPASSWD: ALL' >> /etc/sudoers \
	&& echo 'artefactual:secret' | chpasswd

#
# Chrome
#

ARG CHROME_VERSION="google-chrome-stable"
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
	&& echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
	&& apt-get update -qqy \
	&& apt-get -qqy install ${CHROME_VERSION:-google-chrome-stable} \
	&& rm /etc/apt/sources.list.d/google-chrome.list \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/*

ARG CHROME_DRIVER_VERSION="latest"
RUN CD_VERSION=$(if [ ${CHROME_DRIVER_VERSION:-latest} = "latest" ]; then echo $(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE); else echo $CHROME_DRIVER_VERSION; fi) \
	&& echo "Using chromedriver version: "$CD_VERSION \
	&& wget --no-verbose -O /tmp/chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/$CD_VERSION/chromedriver_linux64.zip \
	&& rm -rf /opt/selenium/chromedriver \
	&& unzip /tmp/chromedriver_linux64.zip -d /opt/selenium \
	&& rm /tmp/chromedriver_linux64.zip \
	&& mv /opt/selenium/chromedriver /opt/selenium/chromedriver-$CD_VERSION \
	&& chmod 755 /opt/selenium/chromedriver-$CD_VERSION \
	&& sudo ln -fs /opt/selenium/chromedriver-$CD_VERSION /usr/bin/chromedriver

#
# Firefox
#

ARG FIREFOX_VERSION=94.0.2
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

ARG GECKODRIVER_VERSION=0.30.0
RUN GK_VERSION=$(if [ ${GECKODRIVER_VERSION:-latest} = "latest" ]; then echo $(wget -qO- "https://api.github.com/repos/mozilla/geckodriver/releases/latest" | grep '"tag_name":' | sed -E 's/.*"v([0-9.]+)".*/\1/'); else echo $GECKODRIVER_VERSION; fi) \
	&& echo "Using GeckoDriver version: "$GK_VERSION \
	&& wget --no-verbose -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v$GK_VERSION/geckodriver-v$GK_VERSION-linux64.tar.gz \
	&& rm -rf /opt/geckodriver \
	&& tar -C /opt -zxf /tmp/geckodriver.tar.gz \
	&& rm /tmp/geckodriver.tar.gz \
	&& mv /opt/geckodriver /opt/geckodriver-$GK_VERSION \
	&& chmod 755 /opt/geckodriver-$GK_VERSION \
	&& ln -fs /opt/geckodriver-$GK_VERSION /usr/bin/geckodriver

COPY requirements /home/artefactual/acceptance-tests/requirements/
RUN pip3 install wheel \
	&& pip3 install -r /home/artefactual/acceptance-tests/requirements/base.txt \
	&& pip3 install -r /home/artefactual/acceptance-tests/requirements/test.txt
COPY . /home/artefactual/acceptance-tests
WORKDIR /home/artefactual/acceptance-tests
RUN chown -R artefactual:artefactual /home/artefactual

USER artefactual
ENV HOME /home/artefactual
ENV USER artefactual
