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
catalog.json
catalog.json.sha256
scripts/build-catalog
```

## Build and validate

```bash
./scripts/validate-repository.sh
./scripts/build-catalog
```

The validation output is `dist/catalog.json`. The same generated catalog and
its SHA-256 are checked into the repository as `catalog.json` and
`catalog.json.sha256`. A production service release selects the catalog by an
HTTPS URL tied to an exact commit SHA and by this digest; mutable branch URLs
are not a production release mechanism.

## Release automation

Every validated push to `main` verifies that the checked-in artifact matches
the catalog sources, downloads it from GitHub through a URL fixed to that
commit SHA, and verifies its SHA-256. HomeLab Service polls the public
`main/catalog.json` and `main/catalog.json.sha256` pair, activates only a
consistent validated download, and keeps serving the last valid catalog when a
refresh fails. This uses GitHub repository storage and does not require paid
object storage or dispatch credentials. The repository must be public so
clients can download the catalog without credentials.
