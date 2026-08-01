# Optional reproducibility container. Build only after environment.yml resolves on the release machine.
FROM mambaorg/micromamba:2.3.2

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

WORKDIR /opt/swan-mpo
COPY --chown=$MAMBA_USER:$MAMBA_USER . /opt/swan-mpo
RUN micromamba run -n base python -m pip install --no-deps -e .

ENTRYPOINT ["micromamba", "run", "-n", "base", "swan-mpo"]
CMD ["--help"]
