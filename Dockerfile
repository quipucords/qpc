FROM fedora as manpage_builder
RUN dnf install -y make pandoc
WORKDIR /app
COPY docs/source/man.rst docs/source/man.rst
COPY Makefile Makefile
RUN make manpage

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
    && poetry install -n --only main --no-root

ENV VIRTUAL_ENV=/app/qpc/.venv
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

# copy manpage
COPY --from=manpage_builder /app/docs/qpc.1 /usr/local/share/man/man1/qpc.1

# copy the rest of the application
COPY . .
# install the aplication itself
RUN poetry install -n --only main --sync

ENTRYPOINT ["deploy/docker_run.sh"]
