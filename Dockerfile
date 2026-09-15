FROM python:3.12-slim

LABEL org.opencontainers.image.title="CMHS VarEnrich"
LABEL org.opencontainers.image.description="Privacy-first human rare-variant enrichment"

WORKDIR /work
COPY . /opt/cmhs-varenrich
RUN python -m pip install --no-cache-dir /opt/cmhs-varenrich

ENTRYPOINT ["varenrich"]
CMD ["--help"]
