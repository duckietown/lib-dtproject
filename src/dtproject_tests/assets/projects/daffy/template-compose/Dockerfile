# parameters
ARG REPO_NAME="<REPO_NAME_HERE>"
ARG DESCRIPTION="<DESCRIPTION_HERE>"
ARG MAINTAINER="<YOUR_FULL_NAME> (<YOUR_EMAIL_ADDRESS>)"
# pick an icon from: https://fontawesome.com/v4.7.0/icons/
ARG ICON="cube"

# ==================================================>
# ==> Do not change this code
ARG ARCH=arm32v7
ARG COMPOSE_VERSION=v1.1.6
ARG BASE_IMAGE=compose
ARG BASE_TAG=${COMPOSE_VERSION}-${ARCH}
ARG LAUNCHER=default

# extend dt-commons
ARG SUPER_IMAGE=dt-commons
ARG DISTRO=daffy
ARG SUPER_IMAGE_TAG=${DISTRO}-${ARCH}
ARG DOCKER_REGISTRY=docker.io
FROM ${DOCKER_REGISTRY}/duckietown/${SUPER_IMAGE}:${SUPER_IMAGE_TAG} as dt-commons

# define base image
FROM afdaniele/${BASE_IMAGE}:${BASE_TAG}

# move compose entrypoint
RUN cp /entrypoint.sh /compose-entrypoint.sh

# copy stuff from the super image
COPY --from=dt-commons /entrypoint.sh /entrypoint.sh
COPY --from=dt-commons /environment.sh /environment.sh
COPY --from=dt-commons /usr/local/bin/dt-* /usr/local/bin/
COPY --from=dt-commons /code/dt-commons /code/dt-commons

# recall all arguments
ARG ARCH
ARG DISTRO
ARG REPO_NAME
ARG DESCRIPTION
ARG MAINTAINER
ARG ICON
ARG BASE_TAG
ARG BASE_IMAGE
ARG LAUNCHER

# check build arguments
RUN dt-build-env-check "${REPO_NAME}" "${MAINTAINER}" "${DESCRIPTION}"

# code environment
ENV SOURCE_DIR /code
ENV LAUNCH_DIR /launch

# define/create repository path
ARG REPO_PATH="${SOURCE_DIR}/${REPO_NAME}"
ARG LAUNCH_PATH="${LAUNCH_DIR}/${REPO_NAME}"
RUN mkdir -p "${REPO_PATH}"
RUN mkdir -p "${LAUNCH_PATH}"

# keep some arguments as environment variables
ENV DT_MODULE_TYPE "${REPO_NAME}"
ENV DT_MODULE_DESCRIPTION "${DESCRIPTION}"
ENV DT_MODULE_ICON "${ICON}"
ENV DT_MAINTAINER "${MAINTAINER}"
ENV DT_REPO_PATH "${REPO_PATH}"
ENV DT_LAUNCH_PATH "${LAUNCH_PATH}"
ENV DT_LAUNCHER "${LAUNCHER}"

# configure HTTP port
ENV HTTP_PORT 8080

# install apt dependencies
COPY ./dependencies-apt.txt "${REPO_PATH}/"
RUN dt-apt-install ${REPO_PATH}/dependencies-apt.txt

# install python3 dependencies
COPY ./dependencies-py3.* "${REPO_PATH}/"
# TODO: we cannot use the .resolved file because pip is too old on python3.5 (upgrade compose env)
RUN dt-pip3-install "${REPO_PATH}/dependencies-py3.txt"

# copy dependencies files only
COPY ./dependencies-compose.txt "${REPO_PATH}/"

# switch to simple user
USER www-data

# install compose dependencies
RUN python3 ${COMPOSE_DIR}/public_html/system/lib/python/compose/package_manager.py \
  --install $(awk -F: '/^[^#]/ { print $1 }' ${REPO_PATH}/dependencies-compose.txt | uniq)

# switch back to root
USER root

# install launcher scripts
COPY ./launchers/. "${LAUNCH_PATH}/"
COPY ./launchers/default.sh "${LAUNCH_PATH}/"
RUN dt-install-launchers "${LAUNCH_PATH}"

# reset the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# define default command
CMD ["bash", "-c", "dt-launcher-${DT_LAUNCHER}"]

# store module metadata
LABEL org.duckietown.label.module.type="${REPO_NAME}" \
    org.duckietown.label.module.description="${DESCRIPTION}" \
    org.duckietown.label.module.icon="${ICON}" \
    org.duckietown.label.architecture="${ARCH}" \
    org.duckietown.label.code.location="/var/www/html" \
    org.duckietown.label.code.version.distro="${DISTRO}" \
    org.duckietown.label.base.image="${BASE_IMAGE}" \
    org.duckietown.label.base.tag="${BASE_TAG}" \
    org.duckietown.label.maintainer="${MAINTAINER}"
# <== Do not change this code
# <==================================================

# switch to simple user
USER www-data

# configure \compose\
RUN python3 ${COMPOSE_DIR}/configure.py \
  # --<KEY_1> <VALUE_1> \
  # --<KEY_2> <VALUE_2> \
  # ...

# switch back to root
USER root
