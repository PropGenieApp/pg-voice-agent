ARG UBUNTU_VERSION='22.04'
ARG IMAGE_BUILDER="ubuntu:${UBUNTU_VERSION}"

FROM ${IMAGE_BUILDER}

USER root:root

ENV PYTHONOPTIMIZE='1' \
    WORK_DIR='/usr/src/app' \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en

WORKDIR "${WORK_DIR}"

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get -q update; \
    apt-get -q install -y \
        locales\
        ca-certificates \
        wget \
        git \
        ccache \
        curl \
        vim \
        portaudio19-dev \
        cmake; \
    ccache -s; \
    git --version; \
    cmake --version

COPY --link --chown=root:root ./uv.lock ./pyproject.toml ./


# Install python
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    add-apt-repository ppa:deadsnakes/ppa -y; \
    apt -q update; \
    apt search python3.11 | grep '^python3.11/'; \
    DEBIAN_FRONTEND='noninteractive' apt -q install -y -o Dpkg::Options::='--force-confnew' --no-install-recommends 'python3.11' 'python3.11-dev' 'python3.11-venv'; \
    PYTHON="/usr/bin/python3.11"; \
    update-alternatives --install /usr/bin/python3 python3 "${PYTHON}" 1; \
    ldconfig; \
    "${PYTHON}" --version;

COPY --link ./scripts ./scripts
COPY --link ./patches/ ./patches/

RUN ./scripts/reinit_env.sh

COPY --link --chown=root:root ./src ./src
COPY --link --chown=root:root ./entrypoint.sh .

EXPOSE 5000

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
