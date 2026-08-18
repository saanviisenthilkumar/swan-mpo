from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
me = Path(__file__).resolve()
bad = []

# Source/release audit, not a scan of locally generated result directories.  Runtime
# artifacts are separately designed to redact the user's home directory.
ignored_parts = {
    ".git", ".venv", ".pytest_cache", "__pycache__",
    "demo_results", "real_vina_verification", "dist", "build",
}
ignored_names = {
    "real_vina_verification_report.json", "my_real_vina_target.json",
    "my_real_vina_mtor.json",
}

# Patterns are assembled to keep this audit file from flagging itself.
import re
patterns = [
    re.compile(re.escape("/" + "Users" + "/")),
    re.compile(re.escape("/" + "home" + "/")),
    re.compile(r"[A-Za-z]:\\" + "Users" + r"\\"),
    re.compile(re.escape("MacBook" + "-Pro")),
    re.compile(re.escape(".attlocal" + ".net")),
    re.compile(re.escape("REPLACE_WITH_PUBLIC_" + "GITHUB_URL")),
]
for p in root.rglob("*"):
    if not p.is_file() or p.resolve() == me:
        continue
    rel = p.relative_to(root)
    if any(part in ignored_parts for part in rel.parts) or p.name in ignored_names:
        continue
    if p.suffix.lower() in {".png", ".pdf", ".zip", ".pyc"}:
        continue
    text = p.read_text(errors="ignore")
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            bad.append((str(rel), match.group(0)))
print("RELEASE AUDIT:", "PASS" if not bad else "FAIL")
for item in bad:
    print(item)
sys.exit(1 if bad else 0)
