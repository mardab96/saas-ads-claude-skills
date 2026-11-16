#!/usr/bin/env python3
"""Validate SaaS ads skill structure, routing, and copy safety.

Checks every *-saas-ads/SKILL.md next to this shared folder:
- required sections, frontmatter name equals folder name, at least 5 workflow
  steps, at least 280 words, doubled words, sentences that start with "The",
  em or en dashes, shared paths that exist, threshold IDs that exist;
- description: holds the platform word and "Use when", has at least 3 quoted
  trigger phrases, stays within 1024 characters, ends with a "Not for X; use Y."
  clause that names real skills, and shares no quoted trigger phrase with
  another skill;
- Required input: the missing-input rule (stop that finding, name the missing
  input, return needs_data, do not estimate) and a T01 citation;
- Analysis workflow: reads thresholds.md before step 1;
- Guardrails: the personal-data rule and the not-SaaS stop rule;
- helper command lines use the "<skill-dir>" form with an absolute CSV path.
It also checks the threshold register tags, the copy-paste prompts (one per
skill), and the helper command form in AGENTS.md and the prompts.
Standard library only.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "saas-ads-shared"
REQUIRED = [
    "## Use this skill when",
    "## Required input",
    "## Analysis workflow",
    "## Decision rules",
    "## Output format",
    "## Practical example",
    "## Guardrails",
]
MISSING_RULE = "If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate."
THRESHOLD_LINE = "Read `../saas-ads-shared/references/thresholds.md` before step 1."
PII_RULE = "Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted."
SCOPE_RULE = "If the account is ecommerce or lead-gen rather than SaaS, say so and stop."
NOT_FOR = re.compile(
    r"Not for [^;]+; use ([a-z0-9-]+-saas-ads(?:(?: or |, )[a-z0-9-]+-saas-ads)*)\.$"
)
COMMAND = re.compile(r'python3 "<skill-dir>/\.\./saas-ads-shared/scripts/([a-z_]+)\.py"')


def section(text, heading):
    match = re.search(r"^## " + re.escape(heading) + r"\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def frontmatter(text):
    parts = text.split("---", 2)
    return parts[1] if text.startswith("---") and len(parts) == 3 else ""


def description(text):
    match = re.search(r"^description:\s*(.+?)\s*$", frontmatter(text), re.M)
    return match.group(1) if match else ""


def triggers(desc):
    return [p.strip().lower() for p in re.findall(r'"([^"]+)"', desc)]


def check_command_lines(label, text, errors):
    for line in text.splitlines():
        if "python3" not in line:
            continue
        match = COMMAND.search(line)
        if not match:
            errors.append(f'{label}: helper command must start python3 "<skill-dir>/../saas-ads-shared/scripts/<x>.py": {line.strip()[:60]}')
        elif not (match.group(1) == "cac_recovery" or (match.group(1) == "marginal_cac" and " --design " in line)) and not re.search(r'"<absolute path to (?:your |the )?[A-Za-z ]*CSV>"', line):
            errors.append(f'{label}: helper command needs an "<absolute path to your ... CSV>" placeholder: {line.strip()[:60]}')


def check_text(text, folder, thresholds, folders=()):
    errors = []
    for heading in REQUIRED:
        if heading not in text:
            errors.append("missing " + heading)
    front = frontmatter(text)
    name = re.search(r"^name:\s*(\S+)\s*$", front, re.M)
    if not name or name.group(1) != folder:
        errors.append("frontmatter name must equal folder name")
    desc = description(text)
    if "SaaS" not in front and "saas" not in front:
        errors.append("description missing SaaS")
    if "Use when" not in front:
        errors.append("description missing activation phrase 'Use when'")
    if len(desc) > 1024:
        errors.append(f"description is {len(desc)} characters, limit 1024")
    if ": " in desc:
        errors.append("description contains ': ' which breaks YAML plain scalars")
    if len(triggers(desc)) < 3:
        errors.append("description needs at least 3 quoted trigger phrases")
    not_for = NOT_FOR.search(desc)
    if "Not for" not in desc:
        errors.append("description lacks a 'Not for' clause")
    elif not not_for:
        errors.append("description must end with 'Not for X; use <skill-name>.'")
    elif folders:
        for target in re.split(r", | or ", not_for.group(1)):
            if target not in folders:
                errors.append(f"'Not for' clause names unknown skill {target}")
            elif target == folder:
                errors.append("'Not for' clause points at the skill itself")
    if len(re.findall(r"^\d+\. ", section(text, "Analysis workflow"), re.M)) < 5:
        errors.append("workflow needs 5 steps")
    if len(text.split()) < 280:
        errors.append("under 280 words")
    required_input = section(text, "Required input")
    if MISSING_RULE not in required_input:
        errors.append("required input lacks the missing-input rule (stop that finding, name the missing input, return needs_data, do not estimate)")
    if "mark the assumption" in text:
        errors.append("old 'mark the assumption' wording remains")
    if not re.search(r"\bT01\b", required_input):
        errors.append("required input does not cite T01")
    if THRESHOLD_LINE not in section(text, "Analysis workflow"):
        errors.append("analysis workflow lacks the thresholds read line before step 1")
    guardrails = section(text, "Guardrails")
    if PII_RULE not in guardrails:
        errors.append("guardrails lack the personal-data rule")
    if SCOPE_RULE not in guardrails:
        errors.append("guardrails lack the not-SaaS stop rule")
    if "llustrative" not in section(text, "Practical example"):
        errors.append("practical example is not labeled illustrative")
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    if re.search(r"\b(\w+)\s+\1\b", prose, re.I):
        errors.append("doubled word")
    if re.search(r"(^|[.!?]\s+|\n)The\s", text):
        errors.append("sentence starts with The")
    if "\u2014" in text or "\u2013" in text:
        errors.append("forbidden dash")
    for rel in sorted(set(re.findall(r"\.\./saas-ads-shared/((?:scripts|references)/[A-Za-z0-9_.-]+)", text))):
        if not (SHARED / rel).exists():
            errors.append("missing shared file " + rel)
    for tid in sorted(set(re.findall(r"\bT(\d{2})\b", text))):
        if f"**T{tid}," not in thresholds:
            errors.append(f"unknown threshold T{tid}")
    check_command_lines("skill", text, errors)
    return errors


def check_triggers(descriptions):
    """descriptions maps folder name to description. Returns duplicate-phrase errors."""
    owners = {}
    errors = []
    for folder, desc in sorted(descriptions.items()):
        for phrase in set(triggers(desc)):
            owners.setdefault(phrase, []).append(folder)
    for phrase, folders in sorted(owners.items()):
        if len(folders) > 1:
            errors.append(f'trigger phrase "{phrase}" is claimed by {", ".join(folders)}')
    return errors


def check_register(thresholds):
    errors = []
    for line in thresholds.splitlines():
        if line.startswith("- **T"):
            tid = line[4:7]
            if "[heuristic]" not in line and "[platform guidance]" not in line:
                errors.append(f"{tid} lacks a [heuristic] or [platform guidance] tag")
    return errors


def check_docs(titles, folders):
    errors = []
    prompts = (SHARED / "examples" / "copy-paste-prompts.md").read_text(encoding="utf-8")
    for folder, title in sorted(titles.items()):
        if f"## {title}\n" not in prompts:
            errors.append(f"copy-paste-prompts.md has no prompt headed '## {title}'")
    check_command_lines("copy-paste-prompts.md", prompts, errors)
    agents_path = ROOT / "AGENTS.md"
    if not agents_path.is_file():
        # Installed copy (~/.claude/skills) holds only the skill folders and saas-ads-shared; AGENTS.md stays in the clone.
        print("note: AGENTS.md not found next to the skills (installed copy); its checks run in the cloned pack")
        return errors
    agents = agents_path.read_text(encoding="utf-8")
    check_command_lines("AGENTS.md", agents, errors)
    for target in sorted(set(re.findall(r"`([a-z0-9-]+-saas-ads)`", agents))):
        if target not in folders:
            errors.append(f"AGENTS.md names unknown skill {target}")
    return errors


def selftest(files, thresholds):
    sample = files[0].read_text(encoding="utf-8")
    folder = files[0].parent.name
    folders = {p.parent.name for p in files}
    other = files[1].read_text(encoding="utf-8")
    other_folder = files[1].parent.name
    desc = description(sample)
    phrase = triggers(desc)[0]
    cases = {
        "doubled word": (sample + "\n\nCheck check the file.\n", "doubled word"),
        "missing Not for": (sample.replace("Not for", "Skip", 1), "lacks a 'Not for' clause"),
        "overlong description": (sample.replace(desc, desc + " x" * 600, 1), "limit 1024"),
        "old missing-input wording": (sample.replace("stop that finding", "mark the assumption", 1), "missing-input rule"),
        "missing personal-data rule": (sample.replace("Never request or echo", "Never ask or echo", 1), "personal-data rule"),
        "relative helper command": (sample + '\n    python3 ../saas-ads-shared/scripts/cac.py data.csv\n', "helper command must start"),
    }
    failures = []
    for label, (broken, expected) in cases.items():
        if not any(expected in e for e in check_text(broken, folder, thresholds, folders)):
            failures.append(label)
    dupes = check_triggers({folder: desc, other_folder: description(other) + f' Also "{phrase}".'})
    if not any(phrase in e for e in dupes):
        failures.append("duplicate trigger phrase")
    if failures:
        print("FAIL: selftest missed: " + ", ".join(failures))
        return 1
    print(f"OK: selftest caught {len(cases) + 1} seeded faults")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--expect", type=int, default=None, help="expected skill count")
    args = parser.parse_args()
    thresholds = (SHARED / "references" / "thresholds.md").read_text(encoding="utf-8")
    files = sorted(ROOT.glob("*-saas-ads/SKILL.md"))
    if args.selftest:
        return selftest(files, thresholds)
    folders = {p.parent.name for p in files}
    errors = []
    descriptions = {}
    titles = {}
    for path in files:
        text = path.read_text(encoding="utf-8")
        for error in check_text(text, path.parent.name, thresholds, folders):
            errors.append(f"{path.parent.name}: {error}")
        descriptions[path.parent.name] = description(text)
        heading = re.search(r"^# (.+)$", text, re.M)
        titles[path.parent.name] = heading.group(1).strip() if heading else path.parent.name
    errors.extend(check_triggers(descriptions))
    errors.extend(check_register(thresholds))
    errors.extend(check_docs(titles, folders))
    if args.expect is not None and len(files) != args.expect:
        errors.append(f"expected {args.expect} skills, found {len(files)}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"OK: {len(files)} skills passed validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
