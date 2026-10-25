#!/usr/bin/env python3
"""Tests for tools/bootstrap.py. Stdlib only: python tools/test_bootstrap.py

Every test uses a temporary home directory. No test reads or writes a real
profile, so a failing run cannot damage an installed tool config.

S01 covers the style source, the marker engine, the atomic write, and the DSH
block target, including the case that matters most: a rules file that already
holds the style text with no markers.

S02 adds detection from config folders, the plan printer, the confirm gate, and
the four block targets.

S04 adds the four `file` targets, where the hub owns the whole file and writes
no markers, and the Cursor paste text.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent


def load_bootstrap():
    """Import tools/bootstrap.py by path, so the test does not need a package."""
    spec = importlib.util.spec_from_file_location("bootstrap", HERE / "bootstrap.py")
    if spec is None or spec.loader is None:
        raise unittest.SkipTest("tools/bootstrap.py does not exist yet")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bootstrap"] = mod
    spec.loader.exec_module(mod)
    return mod


B = load_bootstrap()

STYLE_SOURCE = HERE.parent / "style" / "WRITING-STYLE.md"


class TempHome(unittest.TestCase):
    """A throwaway home directory, cleaned up even when a test fails."""

    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="shub-home-"))
        self.addCleanup(shutil.rmtree, self.home, True)

    def read(self, rel: str) -> str:
        return B.C.read_text(self.home / rel)


class TestBlockEngine(TempHome):
    def test_block_append(self) -> None:
        """An empty home gains the file, with the body between the markers."""
        target = self.home / "AGENTS.md"

        B.apply_block(target, "STYLE BODY")

        text = self.read("AGENTS.md")
        self.assertIn(B.START, text)
        self.assertIn(B.END, text)
        self.assertIn("STYLE BODY", text)
        self.assertLess(text.index(B.START), text.index(B.END))

    def test_block_replace_idempotent(self) -> None:
        """A second run leaves the file byte-identical."""
        target = self.home / "AGENTS.md"

        B.apply_block(target, "STYLE BODY")
        first = self.read("AGENTS.md")
        B.apply_block(target, "STYLE BODY")

        self.assertEqual(first, self.read("AGENTS.md"))

    def test_block_preserves_user_text(self) -> None:
        """Text above and below the markers survives a replace."""
        target = self.home / "AGENTS.md"
        target.write_text(
            "# My rules\n\nKEEP ABOVE\n\n", encoding="utf-8", newline=""
        )
        B.apply_block(target, "OLD BODY")
        with target.open("a", encoding="utf-8", newline="") as fh:
            fh.write("\nKEEP BELOW\n")

        B.apply_block(target, "NEW BODY")

        text = self.read("AGENTS.md")
        self.assertIn("KEEP ABOVE", text)
        self.assertIn("KEEP BELOW", text)
        self.assertIn("NEW BODY", text)
        self.assertNotIn("OLD BODY", text)

    def test_no_duplicate_block(self) -> None:
        """Two runs produce exactly one start marker."""
        target = self.home / "AGENTS.md"

        B.apply_block(target, "STYLE BODY")
        B.apply_block(target, "STYLE BODY")

        self.assertEqual(self.read("AGENTS.md").count(B.START), 1)


class TestUntracked(TempHome):
    """The case that matters: the style text is already there, with no markers."""

    def _write_untracked(self) -> Path:
        target = self.home / "AGENTS.md"
        body = B.style_body()
        target.write_text(
            "# Working rules for this profile\n\nKEEP ABOVE\n\n" + body + "\n",
            encoding="utf-8",
            newline="",
        )
        return target

    def test_untracked_refused_by_default(self) -> None:
        """Without the flag: report it and change nothing."""
        target = self._write_untracked()
        before = self.read("AGENTS.md")

        result = B.apply_block(target, B.style_body(), replace_untracked=False)

        self.assertEqual(result, "untracked")
        self.assertEqual(self.read("AGENTS.md"), before)

    def test_untracked_replaced_when_asked(self) -> None:
        """With the flag: one managed block, no second copy, user text kept."""
        target = self._write_untracked()

        result = B.apply_block(target, B.style_body(), replace_untracked=True)

        text = self.read("AGENTS.md")
        self.assertEqual(result, "replaced")
        self.assertIn("KEEP ABOVE", text)
        self.assertEqual(text.count(B.START), 1)
        self.assertEqual(text.count(B.END), 1)
        # The style prose must appear once, not twice.
        self.assertEqual(text.count("Write all responses and messages"), 1)

    def test_untracked_replacement_is_idempotent(self) -> None:
        """The run after a replace must be a no-op, not a second rewrite."""
        target = self._write_untracked()

        B.apply_block(target, B.style_body(), replace_untracked=True)
        after_first = self.read("AGENTS.md")
        result = B.apply_block(target, B.style_body())

        self.assertEqual(result, "unchanged")
        self.assertEqual(self.read("AGENTS.md"), after_first)

    def test_untracked_replacement_keeps_a_later_comment_region(self) -> None:
        """Content after the style section must survive, comment markers included.

        The real profile file has a `## Writing style` section followed by an
        unrelated `<!-- 5-stack -->` region. A wrap that guesses too far right
        swallows that region and breaks its marker pairing.
        """
        target = self.home / "AGENTS.md"
        target.write_text(
            "# Working rules\n\n"
            + B.style_body()
            + "\n\n<!-- other-tool:start -->\n# Other rules\n\nKEEP BELOW\n"
            "<!-- other-tool:end -->\n",
            encoding="utf-8",
            newline="",
        )

        B.apply_block(target, B.style_body(), replace_untracked=True)

        text = self.read("AGENTS.md")
        self.assertIn("<!-- other-tool:start -->", text)
        self.assertIn("<!-- other-tool:end -->", text)
        self.assertIn("KEEP BELOW", text)
        self.assertIn("# Working rules", text)
        self.assertLess(text.index(B.END), text.index("<!-- other-tool:start -->"))
        self.assertIn("KEEP BELOW", text.split(B.END)[1])
        self.assertEqual(text.count("Write all responses and messages"), 1)

    def test_untracked_region_without_a_style_heading_is_refused(self) -> None:
        """If the copy does not sit under a Writing style heading, do not guess."""
        target = self.home / "AGENTS.md"
        # The prose alone, with the heading removed: there is no anchor, so the
        # region boundaries cannot be known.
        prose = B.style_body()
        prose = prose[prose.index("\n") + 1 :].lstrip("\r\n")
        target.write_text(
            "# Notes\n\n## Deployment\n\n" + prose + "\n",
            encoding="utf-8",
            newline="",
        )
        before = self.read("AGENTS.md")

        result = B.apply_block(target, B.style_body(), replace_untracked=True)

        self.assertEqual(result, "untracked")
        self.assertEqual(self.read("AGENTS.md"), before)

    def test_comment_region_ends_the_wrap_before_a_deeper_heading(self) -> None:
        """Only the comment rule can stop the wrap here, so this test needs it.

        The real profile file puts `<!-- 5-stack:start -->` after the style
        section, and the first heading inside that region is deeper than the
        style heading. A level-only rule walks past the comment, swallows the
        start marker, and leaves an unpaired end marker.
        """
        target = self.home / "AGENTS.md"
        target.write_text(
            "# Working rules\n\n"
            + B.style_body()
            + "\n\n<!-- other-tool:start -->\n### Deeper heading\n\nKEEP BELOW\n"
            "<!-- other-tool:end -->\n",
            encoding="utf-8",
            newline="",
        )

        B.apply_block(target, B.style_body(), replace_untracked=True)

        text = self.read("AGENTS.md")
        self.assertIn("<!-- other-tool:start -->", text)
        self.assertIn("<!-- other-tool:end -->", text)
        self.assertIn("KEEP BELOW", text)
        self.assertLess(text.index(B.END), text.index("<!-- other-tool:start -->"))

    def test_region_covers_a_deeper_subheading_not_stops_at_it(self) -> None:
        """A deeper heading belongs to the section, so the region spans it.

        Stopping at the deeper heading would leave the old text of that
        subsection behind, beside the new block.
        """
        target = self.home / "AGENTS.md"
        target.write_text(
            "# Working rules\n\n"
            + B.style_body()
            + "\n\n### Examples\n\nOLD TEXT TO DROP\n\n## Next section\n\nKEEP BELOW\n",
            encoding="utf-8",
            newline="",
        )

        B.apply_block(target, B.style_body(), replace_untracked=True)

        text = self.read("AGENTS.md")
        self.assertNotIn("OLD TEXT TO DROP", text)
        self.assertIn("KEEP BELOW", text)
        self.assertIn("## Next section", text)
        self.assertEqual(text.count("Write all responses and messages"), 1)

    def test_untracked_not_flagged_when_text_absent(self) -> None:
        """A file without the style text is a plain append, not untracked."""
        target = self.home / "AGENTS.md"
        target.write_text("# My rules\n\nKEEP ABOVE\n", encoding="utf-8", newline="")

        result = B.apply_block(target, B.style_body())

        self.assertEqual(result, "appended")
        self.assertIn("KEEP ABOVE", self.read("AGENTS.md"))


class TestStyleSource(TempHome):
    def test_style_source_exists(self) -> None:
        """The one copy of the style text is in the repo."""
        self.assertTrue(STYLE_SOURCE.is_file(), f"missing {STYLE_SOURCE}")

    def test_style_body_has_no_markers(self) -> None:
        """The source file must not carry the markers it is wrapped in."""
        body = B.C.read_text(STYLE_SOURCE)
        self.assertNotIn(B.START, body)
        self.assertNotIn(B.END, body)

    def test_style_body_ends_with_the_agreed_line(self) -> None:
        body = B.C.read_text(STYLE_SOURCE)
        self.assertIn("quoted output, or the receipt block.", body)


class TestAtomicWrite(TempHome):
    def test_atomic_write_leaves_no_temp_file(self) -> None:
        """The temp file used for the swap must not survive."""
        target = self.home / "AGENTS.md"

        B.apply_block(target, "STYLE BODY")

        leftovers = [p.name for p in self.home.iterdir() if p.name != "AGENTS.md"]
        self.assertEqual(leftovers, [])

    def test_write_failure_keeps_old_file(self) -> None:
        """A failed write leaves the previous content intact.

        The target is a directory, so the final replace fails. That failure is
        portable, unlike a read-only directory, which Windows does not honour.
        """
        target = self.home / "AGENTS.md"
        B.apply_block(target, "OLD BODY")
        before = self.read("AGENTS.md")
        blocked = self.home / "blocked.md"
        blocked.mkdir()
        (blocked / "keep.txt").write_text(before, encoding="utf-8", newline="")

        with self.assertRaises(OSError):
            B.atomic_write(blocked, "NEW")

        self.assertEqual((blocked / "keep.txt").read_text(encoding="utf-8"), before)
        # The temp file must be cleaned up, not left beside the target.
        leftovers = [p.name for p in self.home.iterdir() if p.name not in ("AGENTS.md", "blocked.md")]
        self.assertEqual(leftovers, [])


class TestLineEndings(TempHome):
    """The source is LF and a Windows profile file is CRLF.

    Writing the block verbatim into a CRLF file leaves a mixture. Git diffs,
    editors and some tools then show the whole region as changed.
    """

    def test_block_follows_a_crlf_file(self) -> None:
        target = self.home / "AGENTS.md"
        target.write_bytes(b"# Rules\r\n\r\nKEEP\r\n")

        B.apply_block(target, "LINE ONE\nLINE TWO")

        raw = target.read_bytes()
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
        # 3 original lines, a fixed blank separator, 3 block lines, 1 trailing.
        self.assertEqual(raw.count(b"\r\n"), 9)
        self.assertIn(b"KEEP\r\n\r\n\r\n<!-- skills-hub:writing-style:start -->", raw)

    def test_block_stays_lf_in_an_lf_file(self) -> None:
        target = self.home / "AGENTS.md"
        target.write_bytes(b"# Rules\n\nKEEP\n")

        B.apply_block(target, "LINE ONE\nLINE TWO")

        self.assertNotIn(b"\r", target.read_bytes())

    def test_new_file_uses_lf(self) -> None:
        """A file this tool creates carries the source's endings, not the OS's."""
        target = self.home / "AGENTS.md"

        B.apply_block(target, "LINE ONE\nLINE TWO")

        self.assertNotIn(b"\r", target.read_bytes())

    def test_check_passes_on_a_crlf_file_after_install(self) -> None:
        """--check must judge the block by content, not by line ending.

        The file is CRLF and the source is LF. Comparing raw bytes reports drift
        on a file that was just written correctly.
        """
        target = self.home / ".dsh" / "AGENTS.md"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"# Rules\r\n\r\nKEEP\r\n")
        B.apply_block(target, B.style_body())

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--check", "--only", "dsh", "--home", str(self.home)])

        self.assertEqual(code, 0)

    def test_check_reports_drift_on_a_changed_block(self) -> None:
        """A hand-edited block must still fail, in a CRLF file too."""
        target = self.home / ".dsh" / "AGENTS.md"
        target.parent.mkdir(parents=True)
        B.apply_block(target, B.style_body())
        target.write_bytes(target.read_bytes().replace(b"short sentences", b"tiny sentences"))

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--check", "--only", "dsh", "--home", str(self.home)])

        self.assertEqual(code, 1)


class TestDetect(TempHome):
    def _touch(self, rel: str) -> None:
        p = self.home / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8", newline="")

    def test_absent_tool_is_not_detected(self) -> None:
        """An empty home detects nothing, so nothing is written."""
        self.assertEqual(B.detect(self.home), set())

    def test_config_folder_is_the_signal(self) -> None:
        """A config folder is enough; no binary on PATH is needed."""
        self._touch(".claude/settings.json")

        self.assertEqual(B.detect(self.home), {"claude"})

    def test_several_tools_detected_together(self) -> None:
        self._touch(".claude/settings.json")
        self._touch(".gemini/GEMINI.md")
        self._touch(".dsh/cordis.patch.yml")

        self.assertEqual(B.detect(self.home), {"claude", "gemini", "dsh"})

    def test_detection_reports_tools_with_no_write_target(self) -> None:
        """kilo and cline are installed but only get skills in S03.

        Detection must report them anyway, or the plan hides a real tool.
        """
        self._touch(".config/kilo/kilo.json")
        self._touch(".cline/settings.json")

        self.assertEqual(B.detect(self.home), {"kilo", "cline"})

    def test_shared_skills_folder_is_not_a_tool_signal(self) -> None:
        """`~/.agents` is the shared skills folder, not proof a tool is installed.

        Using it as a codex signal reported codex on a machine that has no
        ~/.codex and no codex binary.
        """
        self._touch(".agents/skills/one/SKILL.md")

        self.assertEqual(B.detect(self.home), set())

    def test_plan_lists_every_tool_marked_present_or_absent(self) -> None:
        """The plan shows all nine tools, so a detection miss is visible."""
        self._touch(".claude/settings.json")

        lines = B.plan_lines(self.home, B.C.get_hub_root(), {"claude"})

        text = "\n".join(lines)
        self.assertIn("claude", text)
        self.assertIn("cursor", text)
        self.assertIn("not detected", text)
        # Every known tool appears, including the ones this slice cannot write.
        for tool in B.tool_names():
            self.assertIn(tool, text)

    def test_plan_shows_skill_writes_it_will_make(self) -> None:
        """The gate asks consent for the plan, so the plan must list every write.

        A skill link that is written but never shown is a write the user did
        not approve.
        """
        self._touch(".cursor/settings.json")

        lines = B.plan_lines(self.home, B.C.get_hub_root(), {"cursor"})
        text = "\n".join(lines).replace("\\", "/")

        self.assertIn(".cursor/skills", text)
        self.assertIn(".agents/skills", text)
        hub = B.C.get_hub_root()
        skills = B.hub_skills(hub)
        self.assertIn("diagram-the-system", {p.name for p in skills})
        expected = sum(
            1 for s in B.C.read_manifest(hub / "manifest.yml")
            if s.get("status") in ("merged", "authored")
        )
        self.assertEqual(len(skills), expected)
        self.assertIn(f"{expected} skills", text)
        self.assertNotIn("no writable target", text)

    def test_unknown_only_name_is_rejected(self) -> None:
        """A typo must fail loudly, not silently select nothing."""
        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--only", "nope", "--home", str(self.home)])

        self.assertEqual(code, 2)

    def test_bare_run_asks_before_writing(self) -> None:
        """A bare run is what install.ps1 calls, so it must hold the gate too.

        The spec says the script never writes silently. Gating only a special
        mode leaves the bare invocation writing every detected target unprompted.
        """
        self._touch(".gemini/GEMINI.md")
        asked = []

        def refuse(prompt: str) -> bool:
            asked.append(prompt)
            return False

        original, B.confirm = B.confirm, refuse
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = B.main(["--home", str(self.home)])
        finally:
            B.confirm = original

        self.assertEqual(len(asked), 1)
        self.assertEqual(code, 1)
        self.assertEqual(self.read(".gemini/GEMINI.md").count(B.START), 0)

    def test_detect_asks_before_writing(self) -> None:
        """The permission gate must actually run, and 'n' must write nothing."""
        self._touch(".gemini/GEMINI.md")
        asked = []

        def refuse(prompt: str) -> bool:
            asked.append(prompt)
            return False

        original, B.confirm = B.confirm, refuse
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = B.main(["--home", str(self.home)])
        finally:
            B.confirm = original

        self.assertEqual(len(asked), 1)
        self.assertEqual(code, 1)
        self.assertFalse((self.home / ".gemini" / "GEMINI.md").read_text().count(B.START))

    def test_detect_writes_when_confirmed(self) -> None:
        self._touch(".gemini/GEMINI.md")

        original, B.confirm = B.confirm, lambda prompt: True
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = B.main(["--home", str(self.home)])
        finally:
            B.confirm = original

        self.assertEqual(code, 0)
        self.assertEqual(self.read(".gemini/GEMINI.md").count(B.START), 1)

    def test_dry_run_never_asks(self) -> None:
        """--dry-run skips the question entirely."""
        self._touch(".gemini/GEMINI.md")

        def explode(prompt: str) -> bool:
            raise AssertionError("--dry-run must not prompt")

        original, B.confirm = B.confirm, explode
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = B.main(["--dry-run", "--home", str(self.home)])
        finally:
            B.confirm = original

        self.assertEqual(code, 0)

    def test_non_tty_refuses_instead_of_writing_silently(self) -> None:
        """The gate must fail closed when there is no terminal to ask on.

        Piped stdin cannot answer, and a naive `isatty()` guard then skips the
        question and writes anyway. That is a silent write past the permission
        gate, so a non-tty run must refuse unless --yes was passed.
        """
        self._touch(".gemini/GEMINI.md")

        class NotATty(io.StringIO):
            def isatty(self) -> bool:
                return False

        original, sys.stdin = sys.stdin, NotATty()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = B.main(["--home", str(self.home)])
        finally:
            sys.stdin = original

        self.assertEqual(code, 1)
        self.assertEqual(self.read(".gemini/GEMINI.md").count(B.START), 0)

    def test_non_tty_with_yes_writes(self) -> None:
        """--yes is the explicit opt-out, and it works without a terminal."""
        self._touch(".gemini/GEMINI.md")

        class NotATty(io.StringIO):
            def isatty(self) -> bool:
                return False

        original, sys.stdin = sys.stdin, NotATty()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = B.main(["--yes", "--home", str(self.home)])
        finally:
            sys.stdin = original

        self.assertEqual(code, 0)
        self.assertEqual(self.read(".gemini/GEMINI.md").count(B.START), 1)

    def test_non_tty_saying_yes_still_refuses(self) -> None:
        """A piped "y" is not consent: the gate needs a real terminal.

        Without the isatty check this run reads "y", takes it as consent and
        writes. That is the difference between an explicit --yes and a pipe that
        happens to contain the letter.
        """
        self._touch(".gemini/GEMINI.md")

        class PipedYes(io.StringIO):
            def isatty(self) -> bool:
                return False

        original, sys.stdin = sys.stdin, PipedYes("y\n")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = B.main(["--home", str(self.home)])
        finally:
            sys.stdin = original

        self.assertEqual(code, 1)
        self.assertEqual(self.read(".gemini/GEMINI.md").count(B.START), 0)


class TestBlockTargets(TempHome):
    def _touch(self, rel: str) -> None:
        p = self.home / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# existing\n\nKEEP\n", encoding="utf-8", newline="")

    def test_four_block_targets_receive_one_block_each(self) -> None:
        for rel in (".claude/CLAUDE.md", ".codex/AGENTS.md", ".gemini/GEMINI.md", ".dsh/AGENTS.md"):
            self._touch(rel)

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--all", "--yes", "--home", str(self.home)])

        self.assertEqual(code, 0)
        for rel in (".claude/CLAUDE.md", ".codex/AGENTS.md", ".gemini/GEMINI.md", ".dsh/AGENTS.md"):
            text = self.read(rel)
            self.assertEqual(text.count(B.START), 1, rel)
            self.assertIn("KEEP", text, rel)

    def test_block_survives_a_second_run(self) -> None:
        self._touch(".claude/CLAUDE.md")
        with contextlib.redirect_stdout(io.StringIO()):
            B.main(["--all", "--yes", "--home", str(self.home)])
        first = self.read(".claude/CLAUDE.md")

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--all", "--yes", "--home", str(self.home)])

        self.assertEqual(code, 0)
        self.assertEqual(self.read(".claude/CLAUDE.md"), first)

    def test_check_reports_drift_across_targets(self) -> None:
        for rel in (".claude/CLAUDE.md", ".gemini/GEMINI.md"):
            self._touch(rel)
        with contextlib.redirect_stdout(io.StringIO()):
            B.main(["--all", "--yes", "--home", str(self.home)])
        p = self.home / ".gemini" / "GEMINI.md"
        p.write_bytes(p.read_bytes().replace(b"short sentences", b"tiny sentences"))

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--check", "--all", "--home", str(self.home)])

        self.assertEqual(code, 1)

    def test_dry_run_writes_nothing(self) -> None:
        self._touch(".claude/CLAUDE.md")
        before = self.read(".claude/CLAUDE.md")

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--dry-run", "--all", "--home", str(self.home)])

        self.assertEqual(code, 0)
        self.assertEqual(self.read(".claude/CLAUDE.md"), before)


class TestSkillLinks(TempHome):
    """S03: one physical skills tree, linked into each tool."""

    def setUp(self) -> None:
        super().setUp()
        self.hub = self.home / "hub"
        (self.hub / "style").mkdir(parents=True)
        (self.hub / "style" / "WRITING-STYLE.md").write_text(
            B.C.read_text(B.style_path()), encoding="utf-8", newline=""
        )
        for name in ("alpha-skill", "beta-skill"):
            d = self.hub / "skills" / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8", newline="")
        # Detection reads the home, so the tool has to look installed.
        (self.home / ".claude").mkdir()

    def _run(self, *extra: str, capture: io.StringIO | None = None) -> int:
        with contextlib.redirect_stdout(capture or io.StringIO()):
            return B.main(["--yes", "--dir", str(self.hub), "--home", str(self.home), *extra])

    def test_link_creates_one_link_per_skill(self) -> None:
        self._run()

        linked = sorted(p.name for p in (self.home / ".claude" / "skills").iterdir())
        self.assertEqual(linked, ["alpha-skill", "beta-skill"])

    def test_link_resolves_to_the_hub_source(self) -> None:
        """A link, not a copy: the tool's folder points at <hub>/skills."""
        self._run()

        linked = self.home / ".claude" / "skills" / "alpha-skill"
        self.assertTrue((linked / "SKILL.md").is_file())
        self.assertEqual(linked.resolve(), (self.hub / "skills" / "alpha-skill").resolve())

    def test_one_shared_agents_folder_is_written_once(self) -> None:
        """Cursor and Codex share ~/.agents/skills, so it holds one set.

        Both tools are present here; the folder must appear once with two
        entries, not twice with four.
        """
        (self.home / ".cursor").mkdir()

        self._run()

        agents = self.home / ".agents" / "skills"
        self.assertTrue(agents.is_dir())
        self.assertEqual(len(list(agents.iterdir())), 2)
        self.assertEqual(agents.iterdir().__next__().resolve().parent, (self.hub / "skills").resolve())

    def test_shared_folder_not_written_without_cursor_or_codex(self) -> None:
        """Claude alone does not read ~/.agents, so it is not created."""
        self._run()

        self.assertFalse((self.home / ".agents").exists())

    def test_second_run_is_idempotent(self) -> None:
        self._run()
        first = sorted(p.name for p in (self.home / ".claude" / "skills").iterdir())

        code = self._run()

        self.assertEqual(code, 0)
        self.assertEqual(sorted(p.name for p in (self.home / ".claude" / "skills").iterdir()), first)

    def test_existing_real_folder_is_not_replaced(self) -> None:
        """A real skill folder the user made must survive untouched."""
        mine = self.home / ".claude" / "skills" / "alpha-skill"
        mine.mkdir(parents=True)
        (mine / "SKILL.md").write_text("# mine\n", encoding="utf-8", newline="")

        self._run()

        self.assertFalse(mine.is_symlink())
        self.assertEqual(B.C.read_text(mine / "SKILL.md"), "# mine\n")

    def test_second_run_reports_links_not_kept(self) -> None:
        """A junction is not a symlink, so a naive check calls every link "kept".

        On Windows `Path.is_symlink()` is False for a junction. A second run that
        treats the hub's own link as a user folder reports "kept" and never
        repairs a stale one, which is the bug this test pins.
        """
        self._run()

        summary = self._second_run_summary()

        self.assertIn("2 linked", summary)
        self.assertNotIn("kept", summary)

    def _second_run_summary(self) -> str:
        out = io.StringIO()
        self._run(capture=out)
        return out.getvalue()

    def test_stale_link_is_repaired(self) -> None:
        """A link pointing at an old hub is replaced, not reported as kept."""
        stale = self.home / "old-hub" / "skills" / "alpha-skill"
        stale.mkdir(parents=True)
        (stale / "SKILL.md").write_text("# old\n", encoding="utf-8", newline="")
        root = self.home / ".claude" / "skills"
        root.mkdir(parents=True)
        self.assertTrue(B._make_link(stale, root / "alpha-skill"))

        out = io.StringIO()
        self._run(capture=out)

        link = root / "alpha-skill"
        self.assertEqual(link.resolve(), (self.hub / "skills" / "alpha-skill").resolve())
        self.assertIn("repaired", out.getvalue())

    def test_refuses_a_destination_inside_the_source(self) -> None:
        """Copying a folder into itself recurses until the path limit stops it.

        This happened for real: a copy of `<hub>/skills/x` placed inside
        `<hub>/skills/x` produced 1,022 nested files and 2 MB of junk inside the
        hub's own skill tree.
        """
        target = self.hub / "skills" / "alpha-skill" / "alpha-skill"

        results = B.link_skills(self.hub / "skills", target, allow_link=False)

        self.assertIn("refused", results)
        self.assertFalse(target.exists())

    def test_copy_fallback_is_reported(self) -> None:
        """When a link is impossible the result says copied, never silently."""
        results = B.link_skills(self.hub / "skills", self.home / ".claude" / "skills", allow_link=False)

        self.assertEqual(set(results.values()), {"copied"})
        self.assertTrue((self.home / ".claude" / "skills" / "alpha-skill" / "SKILL.md").is_file())

    def test_check_reports_missing_links(self) -> None:
        self._run()
        (self.home / ".claude" / "skills" / "alpha-skill").unlink()

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--check", "--dir", str(self.hub), "--home", str(self.home)])

        self.assertEqual(code, 1)

    def test_check_reports_a_copy_where_a_link_belongs(self) -> None:
        """The spec says a silent copy fallback must not hide. `--check` proves it."""
        self._run("--no-link")

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--check", "--dir", str(self.hub), "--home", str(self.home)])

        self.assertEqual(code, 1)

    def test_check_reports_a_link_into_an_old_hub(self) -> None:
        """A link that exists but points elsewhere gives stale prose."""
        self._run()
        link = self.home / ".claude" / "skills" / "alpha-skill"
        B.os.rmdir(link)
        old = self.home / "old" / "alpha-skill"
        old.mkdir(parents=True)
        (old / "SKILL.md").write_text("# old\n", encoding="utf-8", newline="")
        self.assertTrue(B._make_link(old, link))

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--check", "--dir", str(self.hub), "--home", str(self.home)])

        self.assertEqual(code, 1)

    def test_all_installs_skills_for_a_tool_with_no_style_target(self) -> None:
        """`--all` is the repair switch, so it must reach cursor's skill folders."""
        (self.home / ".cursor").mkdir()

        self._run("--all")

        self.assertTrue((self.home / ".cursor" / "skills" / "alpha-skill").exists())
        self.assertTrue((self.home / ".agents" / "skills" / "alpha-skill").exists())

    def test_dsh_wiring_is_reported_during_a_run(self) -> None:
        (self.home / ".dsh" / "profiles" / "desktop").mkdir(parents=True)
        (self.home / ".dsh" / "profiles" / "desktop" / "cordis.patch.yml").write_text(
            "- id: x\n", encoding="utf-8", newline=""
        )
        out = io.StringIO()

        self._run("--all", capture=out)

        self.assertIn("not wired", out.getvalue())


class TestKiloJson(TempHome):
    """Kilo reads skills.paths from JSON. Merge, never overwrite."""

    def setUp(self) -> None:
        super().setUp()
        self.hub = self.home / "hub"
        (self.hub / "style").mkdir(parents=True)
        (self.hub / "style" / "WRITING-STYLE.md").write_text(
            B.C.read_text(B.style_path()), encoding="utf-8", newline=""
        )
        (self.hub / "skills" / "alpha-skill").mkdir(parents=True)
        (self.hub / "skills" / "alpha-skill" / "SKILL.md").write_text("# a\n", encoding="utf-8", newline="")
        self.kilo = self.home / ".config" / "kilo" / "kilo.json"
        self.kilo.parent.mkdir(parents=True)

    def _run(self) -> int:
        """Run the merge directly: detection is not what this class tests."""
        result, _ = B.merge_kilo_json(self.kilo, self.hub / "skills")
        return 0 if result != "refused" else 1

    def test_adds_skills_paths_and_keeps_other_keys(self) -> None:
        self.kilo.write_text('{"theme": "dark", "skills": {"paths": ["/keep/me"]}}', encoding="utf-8")

        self._run()

        data = json.loads(B.C.read_text(self.kilo))
        self.assertEqual(data["theme"], "dark")
        self.assertIn("/keep/me", data["skills"]["paths"])
        self.assertIn(str((self.hub / "skills").resolve()), data["skills"]["paths"])

    def test_creates_a_missing_file(self) -> None:
        self.assertFalse(self.kilo.exists())

        self._run()

        data = json.loads(B.C.read_text(self.kilo))
        self.assertIn(str((self.hub / "skills").resolve()), data["skills"]["paths"])

    def test_invalid_json_is_refused_and_left_alone(self) -> None:
        """Never destroy a config this tool cannot parse."""
        self.kilo.write_text('{"broken": ', encoding="utf-8")

        code = self._run()

        self.assertEqual(B.C.read_text(self.kilo), '{"broken": ')
        self.assertNotEqual(code, 0)

    def test_refuses_a_wrong_shaped_skills_key(self) -> None:
        """`{"skills": []}` is valid JSON but the wrong shape; do not crash."""
        for body in ('{"skills": []}', '{"skills": {"paths": "a string"}}', "[]"):
            self.kilo.write_text(body, encoding="utf-8")

            code = self._run()

            self.assertNotEqual(code, 0, body)
            self.assertEqual(B.C.read_text(self.kilo), body)

    def test_no_duplicate_path_on_second_run(self) -> None:
        self._run()
        self._run()

        data = json.loads(B.C.read_text(self.kilo))
        paths = data["skills"]["paths"]
        self.assertEqual(len(paths), len(set(paths)))


class TestDshWiring(TempHome):
    """DSH needs `customSkillDirs` in a YAML patch the hub must never edit."""

    def _patch(self, body: str) -> Path:
        p = self.home / ".dsh" / "profiles" / "desktop" / "cordis.patch.yml"
        p.parent.mkdir(parents=True)
        p.write_text(body, encoding="utf-8", newline="")
        return p

    def test_reports_wired_when_the_hub_path_is_listed(self) -> None:
        self._patch(
            "- id: skill-filesystem\n"
            "  config:\n"
            "    customSkillDirs:\n"
            "      - D:/repo/skills-hub/skills\n"
        )

        self.assertEqual(B.dsh_wiring(self.home, Path("D:/repo/skills-hub/skills")), "wired")

    def test_reports_not_wired_when_the_list_is_absent(self) -> None:
        self._patch("- id: llm-pi-ai\n  config:\n    provider: x\n")

        self.assertEqual(B.dsh_wiring(self.home, Path("D:/repo/skills-hub/skills")), "not wired")

    def test_reports_not_wired_when_another_path_is_listed(self) -> None:
        self._patch(
            "- id: skill-filesystem\n"
            "  config:\n"
            "    customSkillDirs:\n"
            "      - D:/other/skills\n"
        )

        self.assertEqual(B.dsh_wiring(self.home, Path("D:/repo/skills-hub/skills")), "not wired")

    def test_never_edits_the_patch(self) -> None:
        """The hub has no YAML parser, and a wrong edit changes every session."""
        body = "- id: skill-filesystem\n  config:\n    provider: x\n"
        p = self._patch(body)

        B.dsh_wiring(self.home, Path("D:/repo/skills-hub/skills"))

        self.assertEqual(B.C.read_text(p), body)

    def test_backslashes_count_as_the_same_path(self) -> None:
        self._patch(
            "- id: skill-filesystem\n"
            "  config:\n"
            "    customSkillDirs:\n"
            "      - D:\\repo\\skills-hub\\skills\n"
        )

        self.assertEqual(B.dsh_wiring(self.home, Path("D:/repo/skills-hub/skills")), "wired")


class TestDocumentsRoot(TempHome):
    """Cline asks the shell where Documents is, and OneDrive can move it.

    A write to `~/Documents` on a redirected profile lands in a folder Cline
    never reads, so the style silently does nothing. The lookup must also never
    run under `--home`: that home is a fixture, so the answer would point at the
    real profile and write outside the sandbox.
    """

    def setUp(self) -> None:
        super().setUp()
        B._DOCUMENTS.clear()

    def test_a_fixture_home_never_asks_the_shell(self) -> None:
        with mock.patch.object(B, "_ask_windows_documents") as ask:
            root = B.documents_root(self.home)
        self.assertEqual(root, self.home / "Documents")
        ask.assert_not_called()

    def test_a_real_home_follows_the_redirect(self) -> None:
        moved = self.home / "OneDrive" / "Documents"
        with mock.patch.object(B.os, "name", "nt"), mock.patch.object(
            B, "_ask_windows_documents", return_value=moved
        ):
            root = B.documents_root(self.home, real_home=True)
        self.assertEqual(root, moved)

    def test_a_failed_ask_keeps_the_literal_path(self) -> None:
        with mock.patch.object(B.os, "name", "nt"), mock.patch.object(
            B, "_ask_windows_documents", return_value=None
        ):
            root = B.documents_root(self.home, real_home=True)
        self.assertEqual(root, self.home / "Documents")

    def test_the_ask_uses_the_known_folder_call(self) -> None:
        done = subprocess.CompletedProcess([], 0, "C:/Users/x/OneDrive/Documents\n", "")
        with mock.patch.object(B.subprocess, "run", return_value=done) as run:
            picked = B._ask_windows_documents()
        self.assertEqual(picked, Path("C:/Users/x/OneDrive/Documents"))
        argv = " ".join(run.call_args.args[0])
        self.assertIn("powershell", argv)
        self.assertIn("[System.Environment]::GetFolderPath", argv)

    def test_a_missing_powershell_is_not_an_error(self) -> None:
        with mock.patch.object(B.subprocess, "run", side_effect=OSError("no powershell")):
            self.assertIsNone(B._ask_windows_documents())

    def test_a_target_path_for_a_real_home_uses_the_redirect(self) -> None:
        """`target_path` resolves the placeholder through the shell answer."""
        moved = self.home / "OneDrive" / "Documents"
        cline = next(t for t in B.TOOLS if t["tool"] == "cline")
        with mock.patch.object(B.os, "name", "nt"), mock.patch.object(
            B, "_ask_windows_documents", return_value=moved
        ):
            path = B.target_path(self.home, cline, real_home=True)
        self.assertEqual(path, moved / "Cline" / "Rules" / "writing-style.md")
        self.assertFalse((self.home / "Documents" / "Cline").exists())

    def test_every_real_run_path_follows_the_shells_documents(self) -> None:
        """Install, check and uninstall must all pass `real_home=True`.

        The helpers are tested above. This pins the call sites that use them:
        drop `real_home` at one, and a real run goes back to the `~/Documents`
        folder Cline never reads.
        """
        moved = self.home / "OneDrive" / "Documents"
        asked: list[bool] = []

        def fake_root(home: Path, real_home: bool = False) -> Path:
            asked.append(real_home)
            return moved if real_home else home / "Documents"

        with mock.patch.object(B.Path, "home", return_value=self.home), mock.patch.object(
            B, "documents_root", side_effect=fake_root
        ):
            install = B.main(["--only", "cline", "--yes"])
            check = B.main(["--only", "cline", "--check"])
            written = (moved / "Cline" / "Rules" / "writing-style.md").is_file()
            uninstall = B.main(["--only", "cline", "--uninstall"])

        self.assertEqual((install, check, uninstall), (0, 0, 0))
        self.assertTrue(written, "the install did not write under the redirected Documents")
        self.assertTrue(asked and all(asked), asked)
        self.assertFalse((moved / "Cline" / "Rules" / "writing-style.md").exists())
        self.assertFalse((self.home / "Documents" / "Cline").exists())


class TestFileTargets(TempHome):
    """S04: four targets where the hub owns the whole file, so no markers.

    A `file` target holds the body and nothing else. That makes ownership the
    hard part: a file at the same path with different text belongs to the user,
    and this tool may not prove it wrote it.
    """

    FILES = {
        "kiro": ".kiro/steering/writing-style.md",
        "kilo": ".kilocode/rules/writing-style.md",
        "cline": "Documents/Cline/Rules/writing-style.md",
        "windsurf": ".codeium/windsurf/memories/writing-style.md",
    }

    def _install(self, *extra: str, capture: io.StringIO | None = None) -> int:
        with contextlib.redirect_stdout(capture or io.StringIO()):
            return B.main(["--all", "--yes", "--home", str(self.home), *extra])

    def test_the_four_file_rows_carry_the_spec_paths(self) -> None:
        """Cline's row carries the Documents placeholder, because the shell
        decides where that folder is. Under `--home` it resolves to the same
        literal path the other three spell out.
        """
        rows = {t["tool"]: t for t in B.TOOLS}
        for tool, rel in self.FILES.items():
            self.assertEqual(rows[tool]["kind"], "file", tool)
            if tool != "cline":
                self.assertEqual(rows[tool]["rel"], rel, tool)
                continue
            self.assertEqual(rows[tool]["rel"], rel.replace("Documents/", f"{B.DOCUMENTS}/", 1))
            self.assertEqual(B.target_path(self.home, rows[tool]), self.home / rel)

    def test_each_file_target_holds_the_body_with_no_markers(self) -> None:
        self._install()

        body = B.style_body()
        for tool, rel in self.FILES.items():
            text = self.read(rel)
            self.assertNotIn(B.START, text, tool)
            self.assertNotIn(B.END, text, tool)
            self.assertEqual(text.strip(), body, tool)

    def test_second_run_is_unchanged(self) -> None:
        self._install()
        for rel in self.FILES.values():
            before = self.read(rel)

            out = io.StringIO()
            code = self._install(capture=out)

            self.assertEqual(code, 0, rel)
            self.assertEqual(self.read(rel), before, rel)
        self.assertIn("unchanged", out.getvalue())

    def test_a_user_file_with_the_same_name_is_kept(self) -> None:
        """The ownership rule: only a file this tool can prove it wrote is ours."""
        mine = self.home / self.FILES["kiro"]
        mine.parent.mkdir(parents=True)
        mine.write_text("# My own steering rules\n\nKEEP ME\n", encoding="utf-8", newline="")

        out = io.StringIO()
        self._install(capture=out)

        self.assertEqual(B.C.read_text(mine), "# My own steering rules\n\nKEEP ME\n")
        self.assertIn("kept", out.getvalue())

    def test_a_user_file_that_merely_mentions_the_style_is_kept(self) -> None:
        """`ASD-STE100` alone is not proof the hub wrote the file.

        A person who writes about the standard in their own steering file would
        otherwise lose it, because a `file` target has no markers and the replace
        drops everything outside the body.
        """
        mine = self.home / self.FILES["kiro"]
        mine.parent.mkdir(parents=True)
        original = "# My own steering\n\nAlways use ASD-STE100 for my notes.\n\nKEEP THIS\n"
        mine.write_text(original, encoding="utf-8", newline="")

        out = io.StringIO()
        self._install(capture=out)

        self.assertEqual(B.C.read_text(mine), original)
        self.assertIn("kept", out.getvalue())

    def test_a_stale_body_is_replaced(self) -> None:
        """A body this tool wrote is replaced when the style text changes."""
        target = self.home / self.FILES["kiro"]
        target.parent.mkdir(parents=True)
        old = B.style_body().replace("short sentences", "tiny sentences") + "\n"
        target.write_text(old, encoding="utf-8", newline="")

        out = io.StringIO()
        self._install(capture=out)

        self.assertEqual(self.read(self.FILES["kiro"]).strip(), B.style_body())
        self.assertIn("replaced", out.getvalue())

    def test_a_user_file_quoting_the_style_is_kept(self) -> None:
        """Quoting the body's own sentence does not make the file ours.

        A person writing about the style can quote it. Only a file laid out as
        the body is proof, so the quote alone must not license an overwrite.
        """
        mine = self.home / self.FILES["kiro"]
        mine.parent.mkdir(parents=True)
        original = (
            "# My house rules\n\n"
            + B._FINGERPRINTS[0]
            + "\n\nKEEP THIS\n"
        )
        mine.write_text(original, encoding="utf-8", newline="")

        out = io.StringIO()
        self._install(capture=out)

        self.assertEqual(B.C.read_text(mine), original)
        self.assertIn("kept", out.getvalue())

    def test_check_calls_a_user_file_kept_not_drift(self) -> None:
        """Drift means "re-run to fix". A file the tool refuses to touch is not that.

        The run prints "Re-run bootstrap.py to fix" after DRIFT, but a user file
        is left alone by design, so the advice would be wrong.
        """
        self._install()
        mine = self.home / self.FILES["kiro"]
        mine.write_text("# My own steering\n\nKEEP ME\n", encoding="utf-8", newline="")

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = B.main(["--check", "--only", "kiro", "--home", str(self.home)])

        text = out.getvalue()
        self.assertIn("kept", text)
        self.assertNotIn("Re-run", text)
        self.assertEqual(code, 0)

    def test_plan_matches_what_all_writes(self) -> None:
        """The gate asks consent for the plan, so the plan must list every write.

        `--all` writes every known tool whether or not it is detected. A plan that
        prints "not detected ... skipped" and then writes eight files asks consent
        for nothing.
        """
        plan = "\n".join(B.plan_lines(self.home, B.C.get_hub_root(), set(B.tool_names())))
        plan = plan.replace("\\", "/")

        for rel in self.FILES.values():
            self.assertIn(rel, plan)

    def test_plan_names_every_path_a_run_writes(self) -> None:
        """Cross-check the plan against the style files a --all run creates."""
        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--all", "--yes", "--home", str(self.home)])
        self.assertEqual(code, 0)

        plan = "\n".join(B.plan_lines(self.home, B.C.get_hub_root(), set(B.tool_names())))
        plan = plan.replace("\\", "/")
        for rel in self.FILES.values():
            self.assertTrue((self.home / rel).is_file(), rel)
            self.assertIn(str(self.home / rel).replace("\\", "/"), plan, rel)

    def test_check_reports_drift_after_a_hand_edit(self) -> None:
        self._install()
        target = self.home / self.FILES["cline"]
        target.write_bytes(target.read_bytes().replace(b"short sentences", b"tiny sentences"))

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--check", "--all", "--home", str(self.home)])

        self.assertEqual(code, 1)

    def test_check_reports_a_missing_file_target(self) -> None:
        self._install()
        (self.home / self.FILES["windsurf"]).unlink()

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--check", "--all", "--home", str(self.home)])

        self.assertEqual(code, 1)

    def test_check_passes_on_the_written_files(self) -> None:
        self._install()
        for rel in self.FILES.values():
            self.assertTrue((self.home / rel).is_file(), rel)

        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--check", "--all", "--home", str(self.home)])

        self.assertEqual(code, 0)

    def test_file_target_follows_a_crlf_file(self) -> None:
        """A CRLF copy of the same body is ours, and is not rewritten."""
        target = self.home / self.FILES["kiro"]
        target.parent.mkdir(parents=True)
        body = B.style_body().replace("\n", "\r\n") + "\r\n"
        target.write_bytes(body.encode("utf-8"))
        before = target.read_bytes()

        out = io.StringIO()
        self._install(capture=out)

        self.assertEqual(target.read_bytes(), before)
        self.assertIn("unchanged", out.getvalue())

    def test_plan_lists_the_file_targets(self) -> None:
        (self.home / ".kiro").mkdir()

        text = "\n".join(B.plan_lines(self.home, B.C.get_hub_root(), {"kiro"})).replace("\\", "/")

        self.assertIn(".kiro/steering/writing-style.md", text)

    def test_dry_run_writes_no_file(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--dry-run", "--all", "--home", str(self.home)])

        self.assertEqual(code, 0)
        for rel in self.FILES.values():
            self.assertFalse((self.home / rel).exists(), rel)


class TestCursorPrint(TempHome):
    """Cursor User Rules are an app setting, so the hub prints one paste."""

    def _install(self, *extra: str, capture: io.StringIO | None = None) -> int:
        with contextlib.redirect_stdout(capture or io.StringIO()):
            return B.main(["--yes", "--all", "--home", str(self.home), *extra])

    def test_run_prints_the_paste_text_and_the_click_path(self) -> None:
        (self.home / ".cursor").mkdir()

        out = io.StringIO()
        self._install(capture=out)

        text = out.getvalue()
        self.assertIn(B.CURSOR_RULES, text)
        self.assertIn(B.CURSOR_PASTE, text)
        self.assertIn("Write all responses and messages", text)

    def test_check_reports_manual_for_cursor(self) -> None:
        (self.home / ".cursor").mkdir()
        self._install()

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = B.main(["--check", "--all", "--home", str(self.home)])

        self.assertIn("manual", out.getvalue())
        self.assertEqual(code, 0)

    def test_cursor_writes_no_file(self) -> None:
        """No documented User Rules path exists, so a guess would break silently."""
        (self.home / ".cursor").mkdir()

        self._install()

        self.assertFalse((self.home / ".cursor" / "rules").exists())
        self.assertFalse((self.home / "Documents" / "Cursor").exists())

    def test_no_paste_text_without_cursor(self) -> None:
        """A machine with no Cursor must not be told to paste anything."""
        (self.home / ".claude").mkdir()

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            B.main(["--only", "claude", "--yes", "--home", str(self.home)])

        self.assertNotIn(B.CURSOR_RULES, out.getvalue())

    def test_cursor_only_run_still_prints_the_paste_text(self) -> None:
        """Cursor has no file to write, so it must not be skipped as nothing to do.

        The early return for an empty write list once swallowed the paste text on
        a Cursor-only run, which is the one thing that run exists to show.
        """
        (self.home / ".cursor").mkdir()

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = B.main(["--only", "cursor", "--yes", "--home", str(self.home)])

        self.assertEqual(code, 0)
        self.assertNotIn("No tool to write", out.getvalue())
        self.assertIn(B.CURSOR_PASTE, out.getvalue())

    def test_dry_run_prints_no_paste_text(self) -> None:
        """--dry-run writes nothing, and the paste is a manual write."""
        (self.home / ".cursor").mkdir()

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = B.main(["--only", "cursor", "--dry-run", "--home", str(self.home)])

        self.assertEqual(code, 0)
        self.assertNotIn(B.CURSOR_PASTE, out.getvalue())
        self.assertIn("paste into", out.getvalue())


class TestUninstall(TempHome):
    """S05: remove only what this tool can prove it created.

    The rule the whole slice turns on: a user file that happens to sit at a
    target path is not ours, and deleting it destroys their work. Nothing on
    disk records which run wrote a file, so the text is the only evidence.
    """

    FILES = TestFileTargets.FILES

    def _run(self, *args: str, capture: io.StringIO | None = None) -> int:
        with contextlib.redirect_stdout(capture or io.StringIO()):
            return B.main([*args, "--yes", "--home", str(self.home)])

    def _install(self) -> None:
        self._run("--all")

    def test_uninstall_removes_the_block_and_keeps_user_text(self) -> None:
        """The managed block goes; the text above and below it stays."""
        target = self.home / ".claude" / "CLAUDE.md"
        target.parent.mkdir(parents=True)
        target.write_text("# My rules\n\nKEEP ABOVE\n", encoding="utf-8", newline="")
        self._install()
        with target.open("a", encoding="utf-8", newline="") as fh:
            fh.write("\nKEEP BELOW\n")

        self._run("--uninstall")

        text = self.read(".claude/CLAUDE.md")
        self.assertNotIn(B.START, text)
        self.assertNotIn(B.END, text)
        self.assertIn("KEEP ABOVE", text)
        self.assertIn("KEEP BELOW", text)

    def test_uninstall_deletes_a_style_file_the_tool_wrote(self) -> None:
        """A `file` target this tool wrote is removed whole."""
        self._install()
        for rel in self.FILES.values():
            self.assertTrue((self.home / rel).is_file(), rel)

        self._run("--uninstall")

        for tool, rel in self.FILES.items():
            self.assertFalse((self.home / rel).exists(), tool)

    def test_uninstall_keeps_a_user_file_with_the_same_name(self) -> None:
        """A person's own `writing-style.md` must survive, byte for byte."""
        mine = self.home / self.FILES["kiro"]
        mine.parent.mkdir(parents=True)
        original = "# My steering\n\nAlways be brief.\n\nKEEP ME\n"
        mine.write_text(original, encoding="utf-8", newline="")

        self._run("--uninstall")

        self.assertEqual(B.C.read_text(mine), original)

    def test_uninstall_keeps_a_file_the_user_added_to(self) -> None:
        """Text added to a copy is not ours to delete, so the file stays."""
        self._install()
        target = self.home / self.FILES["kiro"]
        with target.open("a", encoding="utf-8", newline="") as fh:
            fh.write("\n## MY OWN ADDITION\n")

        self._run("--uninstall")

        self.assertTrue(target.is_file())
        self.assertIn("MY OWN ADDITION", B.C.read_text(target))

    def test_uninstall_removes_only_junctions_into_the_hub(self) -> None:
        """A link into the hub goes; a real folder the user made stays."""
        self._install()
        mine = self.home / ".claude" / "skills" / "my-own-skill"
        mine.mkdir(parents=True)
        (mine / "SKILL.md").write_text("# mine\n", encoding="utf-8", newline="")
        hub_skills = self.home / ".claude" / "skills" / "write-the-spec"
        self.assertTrue(hub_skills.exists())

        self._run("--uninstall")

        self.assertFalse(hub_skills.exists())
        self.assertTrue((mine / "SKILL.md").is_file())

    def test_uninstall_keeps_a_junction_pointing_outside_the_hub(self) -> None:
        """A link to someone else's folder is not this hub's to delete.

        `_is_ours` alone would remove it: it is a junction, so it looks like one
        this tool made. The target is what decides, and this target is outside.
        """
        self._install()
        outside = self.home / "someone-elses-skills" / "their-skill"
        (outside).mkdir(parents=True)
        (outside / "SKILL.md").write_text("# their skill\n", encoding="utf-8", newline="")
        link = self.home / ".claude" / "skills" / "their-skill"
        if not B._make_link(outside, link):
            self.skipTest("this machine cannot make a junction")

        self._run("--uninstall")

        self.assertTrue(link.exists())
        self.assertTrue((outside / "SKILL.md").is_file())

    def test_unlink_skills_never_removes_a_real_directory(self) -> None:
        """A real folder is not a link, even when it resolves inside the source.

        This pins `_is_ours` on its own: `_inside` would accept a real folder that
        sits under the source root, so the link test is what stops the delete.
        """
        src = self.home / "hub" / "skills"
        (src / "a-skill").mkdir(parents=True)
        (src / "a-skill" / "SKILL.md").write_text("# a\n", encoding="utf-8", newline="")
        dst = src / "a-skill"
        self.assertTrue(B._inside(dst, src))
        self.assertFalse(B._is_ours(dst))

        results = B.unlink_skills(src, src)

        self.assertEqual(results.get("a-skill"), "kept")
        self.assertTrue((dst / "SKILL.md").is_file())

    def test_uninstall_leaves_a_real_directory_at_a_skill_name(self) -> None:
        """A real folder where a skill would go is the user's, so it stays."""
        self._install()
        target = self.home / ".claude" / "skills" / "write-the-spec"
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                target.unlink()
            else:
                os.rmdir(target)
        target.mkdir()
        (target / "SKILL.md").write_text("# mine, not the hub's\n", encoding="utf-8", newline="")

        self._run("--uninstall")

        self.assertTrue((target / "SKILL.md").is_file())

    def test_uninstall_leaves_the_hub_folder_alone(self) -> None:
        """Uninstall never touches the checkout it runs from."""
        self._install()
        before = len(B.hub_skills(B.C.get_hub_root()))

        self._run("--uninstall")

        self.assertEqual(len(B.hub_skills(B.C.get_hub_root())), before)
        self.assertTrue(B.style_path().is_file())

    def test_uninstall_keeps_the_kilo_json(self) -> None:
        """The Kilo config is the user's file, so it is not deleted."""
        self._install()
        kilo = self.home / B.KILO_JSON
        self.assertTrue(kilo.is_file())

        self._run("--uninstall")

        self.assertTrue(kilo.is_file())

    def test_uninstall_does_not_grow_the_file(self) -> None:
        """Install then uninstall must not leave extra blank lines behind."""
        target = self.home / ".claude" / "CLAUDE.md"
        target.parent.mkdir(parents=True)
        target.write_text("# My rules\n\nKEEP END\n", encoding="utf-8", newline="")
        before = B.C.read_text(target)

        self._install()
        self._run("--uninstall")

        self.assertEqual(B.C.read_text(target), before)

    def test_uninstall_keeps_a_user_file_with_text_inside_the_body(self) -> None:
        """Their own paragraph between the body's anchor lines is still theirs.

        Checking only the first and last line passed a file with the whole body
        quoted and a user paragraph in the middle, so uninstall deleted it.
        """
        mine = self.home / self.FILES["kiro"]
        mine.parent.mkdir(parents=True)
        body = B.style_body()
        first = body.split("\n", 1)[0]
        last = body.rsplit("\n", 1)[-1]
        original = f"{first}\n\n{body}\n\nMY OWN PARAGRAPH\n\n{last}\n"
        mine.write_text(original, encoding="utf-8", newline="")

        self._run("--uninstall")

        self.assertTrue(mine.is_file())
        self.assertEqual(B.C.read_text(mine), original)

    def test_uninstall_restores_the_exact_bytes(self) -> None:
        """The round trip must return the file to the bytes it had before."""
        for original in (
            "# My rules\n\nKEEP\n",
            "# My rules\n\n\nKEEP\n\n",
            "# My rules\nKEEP",
        ):
            with self.subTest(original=original):
                target = self.home / ".claude" / "CLAUDE.md"
                if target.exists():
                    target.unlink()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(original, encoding="utf-8", newline="")

                self._install()
                self._run("--uninstall")

                self.assertEqual(B.C.read_text(target), original)

    def test_uninstall_is_idempotent(self) -> None:
        """A second uninstall on a clean home reports nothing left and exits 0."""
        self._install()
        self._run("--uninstall")

        out = io.StringIO()
        code = self._run("--uninstall", capture=out)

        self.assertEqual(code, 0)
        self.assertNotIn("Traceback", out.getvalue())

    def test_uninstall_on_a_clean_home_writes_nothing(self) -> None:
        """Nothing installed means nothing to remove, and no directory appears."""
        out = io.StringIO()
        code = self._run("--uninstall", capture=out)

        self.assertEqual(code, 0)
        self.assertEqual([p.name for p in self.home.iterdir()], [])

    def test_dry_run_uninstall_removes_nothing(self) -> None:
        """--dry-run lists the removal and leaves every file in place."""
        self._install()
        before = self.read(".claude/CLAUDE.md")

        out = io.StringIO()
        self._run("--uninstall", "--dry-run", capture=out)

        self.assertEqual(self.read(".claude/CLAUDE.md"), before)
        self.assertTrue((self.home / self.FILES["kiro"]).is_file())
        self.assertIn("uninstall", out.getvalue().lower())


class TestUpdate(TempHome):
    """S05: refresh the hub and re-link, without touching user text."""

    FILES = TestFileTargets.FILES

    def _run(self, *args: str, capture: io.StringIO | None = None) -> int:
        with contextlib.redirect_stdout(capture or io.StringIO()):
            return B.main([*args, "--yes", "--home", str(self.home)])

    def test_update_asks_before_writing(self) -> None:
        """--update is a write path, so it must pass the same confirm gate.

        With no answer it must write nothing. A repair that skips the gate is a
        silent write, which is what the gate exists to stop.
        """
        out = io.StringIO()
        stdin = sys.stdin
        sys.stdin = io.StringIO("")  # EOF: nothing can answer the prompt.
        try:
            with contextlib.redirect_stdout(out):
                code = B.main(["--update", "--home", str(self.home)])
        finally:
            sys.stdin = stdin

        text = out.getvalue()
        self.assertNotEqual(code, 0)
        self.assertIn("No terminal to confirm", text)
        self.assertFalse((self.home / self.FILES["kiro"]).is_file())

    def test_update_carries_a_new_body_to_every_tool(self) -> None:
        """A changed hub body reaches every tool on the next --update.

        The hub body is the one source of truth. A link means --update refreshes
        that folder and every tool sees the new body. This pins that promise.
        """
        style_file = B.style_path()
        original = B.C.read_text(style_file)
        self.addCleanup(B.C.write_text, style_file, original)
        self._run("--all")

        B.C.write_text(style_file, original.replace("Use short sentences.", "Use brief sentences."))

        self._run("--update")

        for rel in (self.FILES["kiro"], self.FILES["kilo"], self.FILES["cline"]):
            text = B.C.read_text(self.home / rel)
            self.assertIn("Use brief sentences.", text)
            self.assertNotIn("Use short sentences.", text)
        block = B.C.read_text(self.home / ".claude" / "CLAUDE.md")
        self.assertIn("Use brief sentences.", block)

    def test_update_writes_a_tool_that_is_not_detected(self) -> None:
        """--update is a repair switch, so it must reach absent tools too.

        On an empty home nothing is detected. A `--update` that only repairs the
        detected tools would write nothing, which is the failure this pins.
        """
        out = io.StringIO()
        self._run("--update", capture=out)

        self.assertTrue((self.home / self.FILES["kiro"]).is_file())
        self.assertTrue((self.home / ".claude" / "CLAUDE.md").is_file())

    def test_update_relinks_a_deleted_skill(self) -> None:
        """A skill link removed by hand comes back."""
        self._run("--all")
        entry = self.home / ".claude" / "skills" / "write-the-spec"
        self.assertTrue(entry.exists())
        if entry.is_symlink():
            entry.unlink()
        else:
            os.rmdir(entry)
        self.assertFalse(entry.exists())

        self._run("--update")

        self.assertTrue(entry.exists())

    def test_update_leaves_a_file_the_user_edited(self) -> None:
        """Text added to a written style file makes it the user's, so it stays.

        A `file` target has no markers, so a repair would have to delete their
        addition. Keeping the file is the only safe answer.
        """
        self._run("--all")
        target = self.home / self.FILES["kiro"]
        target.write_text(B.style_body() + "\nSTALE TAIL\n", encoding="utf-8", newline="")

        out = io.StringIO()
        self._run("--update", capture=out)

        self.assertIn("STALE TAIL", B.C.read_text(target))
        self.assertIn("kept", out.getvalue())

    def test_update_keeps_user_text_around_the_block(self) -> None:
        """The update rewrites only the managed block."""
        target = self.home / ".claude" / "CLAUDE.md"
        target.parent.mkdir(parents=True)
        target.write_text("# Mine\n\nKEEP ABOVE\n", encoding="utf-8", newline="")
        self._run("--all")

        self._run("--update")

        self.assertIn("KEEP ABOVE", self.read(".claude/CLAUDE.md"))

    def test_update_is_idempotent(self) -> None:
        """Two updates leave the same bytes as one."""
        self._run("--all")
        first = self.read(".claude/CLAUDE.md")

        self._run("--update")

        self.assertEqual(first, self.read(".claude/CLAUDE.md"))

    def test_update_without_a_hub_refuses(self) -> None:
        """A hub with no style source cannot update, and exits 2."""
        (self.home / ".claude").mkdir()
        empty = self.home / "not-a-hub"
        empty.mkdir()
        with contextlib.redirect_stdout(io.StringIO()):
            code = B.main(["--update", "--yes", "--home", str(self.home), "--dir", str(empty)])

        self.assertEqual(code, 2)


class TestVerifyStyle(TempHome):
    """S06: verify.py proves the style as well as the skill bodies."""

    def _style(self, hub: Path | None = None) -> int:
        here = Path(__file__).resolve().parent
        spec = importlib.util.spec_from_file_location("verify", here / "verify.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.check_style(hub or B.C.get_hub_root(), self.home)

    def test_a_clean_install_reports_ok(self) -> None:
        """An installed block that matches the style passes."""
        with contextlib.redirect_stdout(io.StringIO()):
            B.main(["--all", "--yes", "--home", str(self.home)])

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self._style()

        self.assertEqual(code, 0)
        self.assertIn("OK    style", out.getvalue())

    def test_an_absent_target_is_skipped_not_failed(self) -> None:
        """A tool that was never installed is not drift."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self._style()

        self.assertEqual(code, 0)
        self.assertIn("SKIP  style", out.getvalue())
        self.assertNotIn("STYLE DRIFT", out.getvalue())

    def test_a_hand_edited_block_is_reported(self) -> None:
        """A block that no longer equals the style body fails the check."""
        with contextlib.redirect_stdout(io.StringIO()):
            B.main(["--all", "--yes", "--home", str(self.home)])
        target = self.home / ".claude" / "CLAUDE.md"
        text = B.C.read_text(target).replace("short sentences", "tiny sentences")
        target.write_text(text, encoding="utf-8", newline="")

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self._style()

        self.assertEqual(code, 1)
        self.assertIn("STYLE DRIFT", out.getvalue())

    def test_a_missing_style_source_fails(self) -> None:
        """No style/ at all is a failure, not a skip."""
        empty = self.home / "empty-hub"
        empty.mkdir()

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self._style(hub=empty)

        self.assertEqual(code, 1)
        self.assertIn("MISSING style", out.getvalue())

    def test_an_empty_style_source_fails(self) -> None:
        """A style file with no text would put an empty block in every tool."""
        empty = self.home / "empty-hub"
        (empty / "style").mkdir(parents=True)
        (empty / "style" / "WRITING-STYLE.md").write_text("\n\n", encoding="utf-8", newline="")

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self._style(hub=empty)

        self.assertEqual(code, 1)
        self.assertIn("EMPTY style", out.getvalue())


class TestNoReposHint(TempHome):
    """S06: a machine with no repos/ is told installing still works."""

    def test_verify_without_sources_exits_2_and_says_install_works(self) -> None:
        """The no-repos message must not read as 'nothing works here'."""
        here = Path(__file__).resolve().parent
        spec = importlib.util.spec_from_file_location("verify_missing", here / "verify.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # A hub copy with a repos.toml pointing at a folder that does not exist.
        fake = self.home / "fake-hub"
        (fake / "style").mkdir(parents=True)
        shutil.copy2(B.style_path(), fake / "style" / "WRITING-STYLE.md")
        (fake / "manifest.yml").write_text(
            '[[skill]]\nname = "ghost"\nstatus = "merged"\nchosen = "ghost"\n',
            encoding="utf-8",
            newline="",
        )
        (fake / "repos.toml").write_text(
            'sources_root = "does-not-exist"\n[[repo]]\nname = "x"\nurl = "u"\n',
            encoding="utf-8",
            newline="",
        )

        out = io.StringIO()
        original = mod.C.get_hub_root
        mod.C.get_hub_root = lambda: fake  # type: ignore[assignment]
        try:
            with contextlib.redirect_stdout(out):
                code = mod.main([])
        finally:
            mod.C.get_hub_root = original  # type: ignore[assignment]

        text = out.getvalue()
        self.assertIn(code, (0, 2), text)
        self.assertIn("Installing does not need this folder", text)
        self.assertIn("refresh.py", text)


class TestInstallers(TempHome):
    """S06: the installers are thin, and they parse.

    The installer writes no style text. Every write belongs to bootstrap.py, so
    the only thing to prove here is that the shell files parse and that they
    hand off to bootstrap.py rather than re-implementing it.
    """

    ROOT = Path(__file__).resolve().parent.parent

    def test_install_sh_parses(self) -> None:
        sh = self.ROOT / "install.sh"
        self.assertTrue(sh.is_file())
        # Git for Windows ships bash outside PATH, so look in the usual places.
        candidates = [
            shutil.which("bash"),
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ]
        bash = next((c for c in candidates if c and Path(c).is_file()), None)
        if not bash:
            self.skipTest("bash is not on this machine")
        proc = subprocess.run([bash, "-n", str(sh)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_install_ps1_parses(self) -> None:
        ps1 = self.ROOT / "install.ps1"
        self.assertTrue(ps1.is_file())
        if os.name != "nt":
            self.skipTest("the PowerShell parser check needs Windows")
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{ps1}', [ref]$null, [ref]$e); if ($e) {{ $e | ForEach-Object {{ $_.Message }}; exit 1 }}",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_installers_hand_off_to_bootstrap(self) -> None:
        """Neither installer may write style text itself."""
        for name in ("install.ps1", "install.sh"):
            text = B.C.read_text(self.ROOT / name)
            self.assertIn("bootstrap.py", text, name)
            self.assertNotIn(B.START, text, name)
            self.assertNotIn(B._FINGERPRINTS[0], text, name)

    def test_installers_never_elevate(self) -> None:
        """No admin step: the spec forbids sudo and RunAs.

        install.sh may print a `sudo apt-get ...` hint when Python is absent, but
        it must never run one. Only a line that starts with the command counts.
        """
        for name in ("install.ps1", "install.sh"):
            text = B.C.read_text(self.ROOT / name)
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("#") or "warn " in stripped or "Write-" in stripped:
                    continue
                self.assertFalse(stripped.startswith("sudo "), f"{name}: {stripped}")
                self.assertNotIn("-Verb RunAs", stripped, name)
                self.assertNotIn("Start-Process -Verb", stripped, name)

    def test_install_ps1_uses_user_scope_only(self) -> None:
        text = B.C.read_text(self.ROOT / "install.ps1")
        self.assertIn("--scope user", text)
        self.assertNotIn("--scope machine", text)


class TestRefresh(TempHome):
    """S06: refresh.py is the maintainer flow, and never runs from install."""

    ROOT = Path(__file__).resolve().parent.parent

    def test_refresh_dry_run_runs_no_step(self) -> None:
        """--dry-run prints the plan and writes nothing."""
        spec = importlib.util.spec_from_file_location(
            "refresh", self.ROOT / "tools" / "refresh.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = mod.main(["--dry-run"])

        text = out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("would run", text)
        self.assertNotIn("Refresh complete", text)

    def test_refresh_lists_every_step_in_order(self) -> None:
        """Verify runs before catalog, because catalog reads verified bodies."""
        spec = importlib.util.spec_from_file_location(
            "refresh_order", self.ROOT / "tools" / "refresh.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        names = [s[0] for s in mod.STEPS]
        self.assertLess(names.index("verify"), names.index("catalog"))
        self.assertLess(names.index("harvest"), names.index("verify"))

    def test_refresh_skip_clone_drops_the_clone_step(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "refresh_skip", self.ROOT / "tools" / "refresh.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = mod.main(["--dry-run", "--skip-clone"])

        self.assertEqual(code, 0)
        self.assertNotIn("clone:", out.getvalue())

    def test_the_installer_never_runs_refresh(self) -> None:
        """The spec forbids refresh.py from the installer."""
        for name in ("install.ps1", "install.sh"):
            self.assertNotIn("refresh.py", B.C.read_text(self.ROOT / name), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
