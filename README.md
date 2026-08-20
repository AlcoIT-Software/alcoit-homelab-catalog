# AlcoIT HomeLab Catalog

Canonical source for every application offered by AlcoIT HomeLab. This
repository owns application metadata, pinned container definitions, catalog
validation, and the immutable catalog artifact consumed by
`alcoit-homelab-service`.

It does not contain subscriber data, device activation, deployment workflows,
or Raspberry Pi installer code.

## Layout

```text
apps/<application>/manifest.json
apps/<application>/docker-compose.yml
catalog.release.json
scripts/build-catalog
```

## Build and validate

```bash
./scripts/validate-repository.sh
./scripts/build-catalog
```

The output is `dist/catalog.json`. Its SHA-256 is written to
`dist/catalog.json.sha256`. A production service release must select the
catalog by HTTPS URL and this digest; mutable branch URLs are not a production
release mechanism.
