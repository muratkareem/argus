"""Reject common credential patterns in staged UTF-8 files without printing secrets."""

import re
import subprocess

patterns = [
    r"gh[pousr]_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{30,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
]
files = (
    subprocess.check_output(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"])
    .decode()
    .split("\0")
)
failed = []
for name in filter(None, files):
    blob = subprocess.check_output(["git", "show", f":{name}"])
    text = blob.decode("utf-8", errors="ignore")
    if any(re.search(pattern, text) for pattern in patterns):
        failed.append(name)
if failed:
    raise SystemExit("Potential credential found in staged files: " + ", ".join(failed))
print("Staged credential-pattern scan passed")
