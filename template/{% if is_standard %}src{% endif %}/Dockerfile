FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# renovate: datasource=repology depName=ubuntu_24_04/ca-certificates versioning=loose
ENV RENOVATE_CA_CERTIFICATES_VERSION=20240203

# renovate: datasource=repology depName=ubuntu_24_04/curl versioning=loose
ENV RENOVATE_CURL_VERSION=8.5.0-2ubuntu10.6

# renovate: datasource=github-releases depName=tianon/gosu
ENV RENOVATE_GOSU_VERSION=1.17

# renovate: datasource=repology depName=ubuntu_24_04/nano versioning=loose
ENV RENOVATE_NANO_VERSION=7.2-2ubuntu0.1


ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    ca-certificates="${RENOVATE_CA_CERTIFICATES_VERSION}" \
    curl="${RENOVATE_CURL_VERSION}" \
    nano="${RENOVATE_NANO_VERSION}" \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN DPKG_ARCH="$(dpkg --print-architecture | awk -F- '{ print $NF }')" \
	&& curl -fsSL -o gosu --output-dir /usr/local/bin "https://github.com/tianon/gosu/releases/download/$RENOVATE_GOSU_VERSION/gosu-$DPKG_ARCH" \
	&& chmod +x /usr/local/bin/gosu \
	&& gosu --version \
	&& gosu nobody true

WORKDIR /srv/dockercontainer
COPY entrypoint.sh ./
ENTRYPOINT ["/srv/dockercontainer/entrypoint.sh"]
CMD ["nano", "--version"]
