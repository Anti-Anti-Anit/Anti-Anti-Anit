import json
import os
import re
import sys
import urllib.request

START = "<!-- repos:start -->"
END = "<!-- repos:end -->"
README = "README.md"
OWNER = os.environ.get("PROFILE_OWNER", "Anti-Anti-Anit")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"


def fetch(path):
    req = urllib.request.Request(API + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "profile-sync")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def rank(repo):
    return (repo["stargazers_count"], repo["updated_at"])


def build_section():
    repos = [
        r
        for r in fetch(f"/users/{OWNER}/repos?per_page=100&type=owner&sort=updated")
        if not r["fork"] and r["name"].lower() != OWNER.lower()
    ]
    repos.sort(key=rank, reverse=True)

    lines = [START, ""]
    if not repos:
        lines += ["_No public repositories yet._", ""]
    else:
        lines += [
            "| Repo | Description | Language | ★ |",
            "| --- | --- | --- | ---: |",
        ]
        for repo in repos[:10]:
            name = repo["name"]
            desc = (repo["description"] or "").replace("|", "\\|").replace("\n", " ")
            desc = desc[:90] + "…" if len(desc) > 90 else desc
            lang = repo["language"] or "—"
            stars = repo["stargazers_count"]
            lines.append(
                f"| [{name}](https://github.com/{OWNER}/{name}) | {desc} | {lang} | {stars} |"
            )
        lines.append("")

    langs = {}
    for repo in repos:
        if repo["language"]:
            langs[repo["language"]] = langs.get(repo["language"], 0) + 1
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:5]
    if top:
        summary = ", ".join(f"**{name}** ({count})" for name, count in top)
        lines += [f"**Languages:** {summary}", ""]

    lines.append(END)
    return "\n".join(lines)


def main():
    with open(README, "r", encoding="utf-8") as fh:
        text = fh.read()
    if START not in text or END not in text:
        sys.exit("markers not found in README.md")
    section = build_section()
    pattern = r"^" + re.escape(START) + r"$.*?^" + re.escape(END) + r"$"
    updated, count = re.subn(
        pattern,
        lambda _: section,
        text,
        count=1,
        flags=re.DOTALL | re.MULTILINE,
    )
    if count != 1:
        sys.exit("could not locate the generated section in README.md")
    if updated == text:
        print("README already up to date, nothing to commit.")
        return 0
    with open(README, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(updated)
    print("README updated.")
    return 1


if __name__ == "__main__":
    sys.exit(main())