FROM ubuntu:14.04

ENV DEBIAN_FRONTEND noninteractive

RUN set -ex \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
		apt-transport-https \
		curl \
		git \
		python-software-properties \
		software-properties-common \
	&& rm -rf /var/lib/apt/lists/*

RUN set -ex \
		&& apt-get update \
		&& apt-get install -y --no-install-recommends \
			build-essential \
			python3-pip \
			python3-dev \
			unzip

# MERGE LATER!
RUN set -ex \
		&& apt-get update \
		&& apt-get install -y --no-install-recommends \
			libxml2-dev \
			libxslt-dev \
			zlib1g-dev

COPY requirements.txt /home/archivematica/acceptance-tests/requirements.txt
RUN pip3 install -r /home/archivematica/acceptance-tests/requirements.txt
RUN pip3 install parse parse_type

RUN groupadd archivematica && useradd -m -g archivematica archivematica

COPY . /home/archivematica/acceptance-tests
WORKDIR /home/archivematica/acceptance-tests
RUN chown -R archivematica:archivematica /home/archivematica

ENV HOME /home/archivematica
ENV USER archivematica
USER archivematica

ENTRYPOINT ["/home/archivematica/acceptance-tests/entrypoint.sh"]
