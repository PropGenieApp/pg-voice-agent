######################################################################################

# https://hub.docker.com/_/postgres/tags
FROM postgres:16.8-bookworm

######################################################################################

ARG USER_ID
ARG GROUP_ID
ARG USER_NAME

SHELL ["/bin/bash", "-e", "-u", "-o", "pipefail", "-c"]

######################################################################################

USER root:root

######################################################################################

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.12.1/wait /usr/local/bin/wait
ADD https://github.com/Yelp/dumb-init/releases/download/v1.2.5/dumb-init_1.2.5_x86_64 /usr/local/bin/dumb-init

RUN  chmod +x /usr/local/bin/wait /usr/local/bin/dumb-init && \
    /usr/local/bin/dumb-init --version && \
    /usr/local/bin/wait --version

######################################################################################

RUN groupadd -g "${GROUP_ID}" -o "${USER_NAME}"
RUN useradd -m -u "${USER_ID}" -g "${GROUP_ID}" -o -s /bin/bash "${USER_NAME}"

######################################################################################

USER "${USER_ID}":"${GROUP_ID}"

######################################################################################

ENTRYPOINT ["/usr/local/bin/dumb-init", "--"]

ENV WAIT_COMMAND='/usr/local/bin/docker-entrypoint.sh postgres'

CMD ["/usr/local/bin/wait"]

######################################################################################
