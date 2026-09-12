from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
RESOURCE_PAGES = {
    "prakticke-informace",
    "zapojte-se",
    "pro-media",
    "ochrana-osobnich-udaju",
}


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.references: list[tuple[str, str, int]] = []
        self.forms: list[dict[str, object]] = []
        self._form: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name: value or "" for name, value in attrs}
        if values.get("id"):
            self.ids.add(values["id"])

        for attribute in ("href", "src"):
            if values.get(attribute):
                self.references.append((attribute, values[attribute], self.getpos()[0]))

        if tag == "form":
            self._form = {"attrs": values, "inputs": []}
            self.forms.append(self._form)
        elif tag == "input" and self._form is not None:
            self._form["inputs"].append(values)

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self._form = None


def parse_document(path: Path) -> DocumentParser:
    parser = DocumentParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def exact_case_exists(path: Path) -> bool:
    """Check every path component exactly, including on case-insensitive macOS."""
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        return False

    current = ROOT
    for part in relative.parts:
        if not current.is_dir() or part not in {entry.name for entry in current.iterdir()}:
            return False
        current /= part
    return current.is_file()


def local_target(source: Path, raw_url: str) -> tuple[Path, str] | None:
    parsed = urlsplit(raw_url)
    if parsed.scheme or parsed.netloc or raw_url.startswith(("//", "mailto:", "tel:", "data:")):
        return None

    route = unquote(parsed.path)
    if not route:
        target = source
    elif route == "/":
        target = ROOT / "index.html"
    else:
        target = (ROOT if route.startswith("/") else source.parent) / route.lstrip("/")
        if not target.suffix:
            target = target.with_suffix(".html")
    return target, unquote(parsed.fragment)


class SiteIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html_files = sorted(ROOT.glob("*.html"))
        cls.documents = {path: parse_document(path) for path in cls.html_files}

    def test_local_links_and_assets_resolve_with_exact_case(self) -> None:
        failures: list[str] = []
        for source, document in self.documents.items():
            for attribute, url, line in document.references:
                resolved = local_target(source, url)
                if resolved is None:
                    continue
                target, fragment = resolved
                if not exact_case_exists(target):
                    failures.append(f"{source.name}:{line}: {attribute}=\"{url}\" nenalezen")
                    continue
                if fragment:
                    target_document = self.documents.get(target) or parse_document(target)
                    if fragment not in target_document.ids:
                        failures.append(f"{source.name}:{line}: kotva #{fragment} v {target.name} nenalezena")

        self.assertEqual([], failures, "\n" + "\n".join(failures))

    def test_new_resource_pages_are_reachable_from_every_page(self) -> None:
        failures: list[str] = []
        for path in self.html_files:
            local_routes = {
                urlsplit(url).path.strip("/")
                for attribute, url, _line in self.documents[path].references
                if attribute == "href" and not urlsplit(url).scheme
            }
            missing = RESOURCE_PAGES - local_routes
            if missing:
                failures.append(f"{path.name}: chybí odkazy na {', '.join(sorted(missing))}")

        self.assertEqual([], failures, "\n" + "\n".join(failures))

    def test_netlify_forms_have_detection_fields_and_valid_action(self) -> None:
        failures: list[str] = []
        form_count = 0
        for path, document in self.documents.items():
            for form in document.forms:
                attrs = form["attrs"]
                if attrs.get("data-netlify") != "true":
                    continue
                form_count += 1
                inputs = form["inputs"]
                form_name = attrs.get("name")
                hidden_names = {
                    field.get("value")
                    for field in inputs
                    if field.get("type") == "hidden" and field.get("name") == "form-name"
                }
                input_names = {field.get("name") for field in inputs}
                if attrs.get("method", "").upper() != "POST":
                    failures.append(f"{path.name}: formulář {form_name!r} nepoužívá POST")
                if not form_name or form_name not in hidden_names:
                    failures.append(f"{path.name}: formulář {form_name!r} nemá správné skryté form-name")
                if "bot-field" not in input_names:
                    failures.append(f"{path.name}: formulář {form_name!r} nemá honeypot bot-field")
                action = attrs.get("action", "")
                resolved = local_target(path, action)
                if resolved is None or not exact_case_exists(resolved[0]):
                    failures.append(f"{path.name}: formulář {form_name!r} má neplatný action {action!r}")

        self.assertGreater(form_count, 0, "Nebyl nalezen žádný Netlify formulář")
        self.assertEqual([], failures, "\n" + "\n".join(failures))

    def test_sync_workflow_is_non_destructive_and_covers_all_html_pages(self) -> None:
        workflow_path = ROOT / ".github/workflows/sync-netlify-deploy.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertNotRegex(workflow, r"rm\s+-f\s+\./\*\.html")
        self.assertNotRegex(workflow, r"rm\s+-rf\s+\./(?:assets|images)")

        match = re.search(r"files=\(\n(?P<body>.*?)\n\s*\)", workflow, re.DOTALL)
        self.assertIsNotNone(match, "Ve workflow chybí pole files")
        synced_files = set(re.findall(r'^\s*"([^"]+)"\s*$', match.group("body"), re.MULTILINE))
        expected_html = {path.name for path in self.html_files}
        self.assertEqual(set(), expected_html - synced_files, "Workflow nestahuje všechny HTML stránky")


if __name__ == "__main__":
    unittest.main()
