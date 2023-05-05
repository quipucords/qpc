FROM redhat/ubi8-minimal

WORKDIR /app/qpc
VOLUME ["/root/.config"]

COPY pyproject.toml poetry.lock ./
RUN microdnf update \
    && microdnf install -y \
        gcc \
        git \
        glibc-langpack-en \
        jq \
        make \
        openssh-clients \
        procps-ng \
        python39 \
        python39-pip \
        tar \
        which \
    && if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3.9 /usr/bin/python; fi \
    && if [[ ! -e /usr/bin/pip    ]]; then ln -sf /usr/bin/pip3.9    /usr/bin/pip;    fi \
    && pip install -U pip \
    && pip install poetry \
    && poetry config virtualenvs.in-project true \
    && poetry install -n

ENV VIRTUAL_ENV=/app/qpc/.venv
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

# Copy QPC
COPY . .

ENTRYPOINT ["/bin/bash", "deploy/docker_run.sh"]

