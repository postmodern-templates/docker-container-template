FROM debian:trixie-slim@sha256:f6b08b09a05725f9431502d3b5714f5c4576e82c1a84fa1debe0c24a7e0c3ec4

# Install what your application needs here, before USER drops root.

WORKDIR /app
# A project generated on Windows loses entrypoint.sh's executable bit.
COPY --chmod=755 entrypoint.sh ./
# Some base images already have a UID 1000, such as Ubuntu's ubuntu user; this one doesn't.
RUN id 1000 >/dev/null 2>&1 || useradd --uid 1000 --user-group --create-home app \
    && chown 1000:1000 /app
# Numeric, so Kubernetes' runAsNonRoot can verify it.
USER 1000:1000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["echo", "Replace this CMD with your application's command."]
