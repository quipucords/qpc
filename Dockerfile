FROM fedora as manpage_builder
RUN dnf install -y make pandoc python3.11-pip
WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --only build
COPY docs/source/man.j2 docs/source/man.j2
COPY Makefile Makefile
RUN make manpage

FROM redhat/ubi9-minimal

WORKDIR /app/qpc
VOLUME ["/root/.config/qpc"]
VOLUME ["/root/.local/share/qpc"]

COPY pyproject.toml poetry.lock ./
RUN microdnf update -y \
    && microdnf install -y \
        coreutils-single \
        git \
        jq \
        libcap \
        make \
        man \
        man-db \
        openssh-clients \
        passwd \
        procps-ng \
        python3.11 \
        python3.11-pip \
        shadow-utils \
        tar \
        util-linux \
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
COPY --from=manpage_builder /app/docs/*.1 /usr/local/share/man/man1/

# copy the rest of the application
COPY . .
# install the aplication itself
RUN poetry install -n --only main --sync

LABEL com.github.containers.toolbox="true"
# toolbox requires an "empty"entrypoint - which is fine, CMD is ok for qpc usecase
CMD ["deploy/docker_run.sh"]
ENTRYPOINT []
