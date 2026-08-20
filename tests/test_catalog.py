from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path
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
    def test_catalog_contains_every_application_directory(self) -> None:
        catalog = build_catalog.build()
        expected = sorted(path.name for path in (ROOT / "apps").iterdir() if path.is_dir())
        self.assertEqual([app["id"] for app in catalog["apps"]], expected)
        for app in catalog["apps"]:
            self.assertIn(f"  id: {app['id']}\n", app["compose"])
            self.assertIn(f'  version: "{app["version"]}"\n', app["compose"])

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


if __name__ == "__main__":
    unittest.main()
