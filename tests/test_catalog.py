from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader(
    "build_catalog", str(ROOT / "scripts" / "build-catalog")
)
spec = importlib.util.spec_from_loader(loader.name, loader)
build_catalog = importlib.util.module_from_spec(spec)
loader.exec_module(build_catalog)


class CatalogTests(unittest.TestCase):
    def test_release_workflow_verifies_immutable_public_catalog(self) -> None:
        workflow = (ROOT / ".github/workflows/validate.yml").read_text()
        self.assertIn("cmp --silent catalog.json dist/catalog.json", workflow)
        self.assertIn("raw.githubusercontent.com/${GITHUB_REPOSITORY}/${GITHUB_SHA}/catalog.json", workflow)
        self.assertIn('test "$actual" = "$digest"', workflow)
        self.assertNotIn('event_type: "catalog-published"', workflow)
        self.assertNotIn("/dispatches", workflow)
        self.assertNotIn("LOCKFILE_DISPATCH_TOKEN", workflow)
        self.assertNotRegex(workflow, r"uses: [^\n]+@v[0-9]+")

    def test_checked_in_catalog_matches_sources(self) -> None:
        checked_in = json.loads((ROOT / "catalog.json").read_text())
        self.assertEqual(checked_in, build_catalog.build())

    def test_catalog_contains_every_application_directory(self) -> None:
        catalog = build_catalog.build()
        expected = sorted(
            json.loads((path / "manifest.json").read_text())["id"]
            for path in (ROOT / "Apps").iterdir()
            if path.is_dir()
        )
        self.assertEqual([app["id"] for app in catalog["apps"]], expected)
        for app in catalog["apps"]:
            self.assertRegex(app["compose"], r"(?m)^  id: com\.alcoit\.[a-z0-9]+$")
            self.assertIn(f'  version: "{app["version"]}"\n', app["compose"])

    def test_catalog_keeps_only_the_two_supported_apps(self) -> None:
        catalog = build_catalog.build()

        self.assertEqual(
            {app["id"] for app in catalog["apps"]}, {"jellyfin", "pi-hole"}
        )
        self.assertEqual(len(catalog["apps"]), 2)

    def test_pihole_uses_the_casaos_legacy_application_name(self) -> None:
        app = next(app for app in build_catalog.build()["apps"] if app["id"] == "pi-hole")

        self.assertIn("name: pihole\n", app["compose"])
        self.assertIn("  pihole:\n", app["compose"])
        self.assertIn("  main: pihole\n", app["compose"])

    def test_catalog_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            self.assertEqual(build_catalog.main.__name__, "main")
            payload = build_catalog.canonical(build_catalog.build())
            first.write_bytes(payload)
            second.write_bytes(build_catalog.canonical(build_catalog.build()))
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_every_compose_uses_pinned_images(self) -> None:
        for app in build_catalog.build()["apps"]:
            self.assertNotIn(":latest", app["compose"])
            self.assertNotIn("privileged: true", app["compose"].lower())

    def test_volume_mounts_are_compatible_with_casaos_compose_parser(self) -> None:
        for app in build_catalog.build()["apps"]:
            self.assertNotRegex(
                app["compose"],
                r'^\s*-\s*["\']?\$\{[^\n]+:[^\n]+$',
                msg=f'{app["id"]} uses variable expansion in a short volume mount',
            )

    def test_every_compose_resolves_without_required_external_variables(self) -> None:
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("Docker Compose is not installed")

        for compose in sorted((ROOT / "Apps").glob("*/docker-compose.yml")):
            result = subprocess.run(
                [docker, "compose", "-f", str(compose), "config", "-q"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"{compose} cannot be installed by Compose: {result.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
