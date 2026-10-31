FROM ubuntu:24.04@sha256:80dd3c3b9c6cecb9f1667e9290b3bc61b78c2678c02cbdae5f0fea92cc6734ab
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
