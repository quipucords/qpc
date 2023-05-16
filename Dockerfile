FROM redhat/ubi9-minimal

WORKDIR /app/qpc
VOLUME ["/root/.config/qpc"]
VOLUME ["/root/.local/share/qpc"]

COPY pyproject.toml poetry.lock ./
RUN microdnf update -y \
    && microdnf install -y \
        git \
        jq \
        make \
        man-db \
        man \
        openssh-clients \
        procps-ng \
        python3.11 \
        python3.11-pip \
        tar \
        which \
    && if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3.11 /usr/bin/python; fi \
    && if [[ ! -e /usr/bin/pip    ]]; then ln -sf /usr/bin/pip3.11    /usr/bin/pip;    fi \
    && pip install -U pip \
    && pip install poetry \
    && poetry config virtualenvs.in-project true \
    && poetry install -n --only main

ENV VIRTUAL_ENV=/app/qpc/.venv
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

# Copy QPC
COPY . .
COPY docs/qpc.1 /usr/local/share/man/man1/qpc.1

ENTRYPOINT ["deploy/docker_run.sh"]

