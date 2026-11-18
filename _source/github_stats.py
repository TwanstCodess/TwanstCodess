#!/usr/bin/env python3
"""
Builds assets/github-stats.svg from your public GitHub data, in the same
design as the rest of the profile. Runs inside GitHub Actions
(.github/workflows/github-stats.yml) with the built-in GITHUB_TOKEN, so it
does not depend on any third-party server.

Local test without the API:   python3 github_stats.py --placeholder
"""
import datetime as dt
import json
import os
import sys
import urllib.request

from generate import (BUILD, INK, MIST, OUT, PAPER, RULE, Doc, load_fonts,
                      measure)

API = "https://api.github.com/graphql"
TOP_N = 5


def gql(query, variables):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                 "Content-Type": "application/json",
                 "User-Agent": "twanst-profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if data.get("errors"):
        raise SystemExit(f"GitHub API error: {data['errors']}")
    return data["data"]


Q_USER = """
query($login:String!, $cursor:String){
  user(login:$login){
    followers{totalCount}
    pullRequests{totalCount}
    issues{totalCount}
    contributionsCollection{contributionYears}
    repositories(first:100, after:$cursor, ownerAffiliations:OWNER,
                 privacy:PUBLIC, isFork:false){
      totalCount
      pageInfo{hasNextPage endCursor}
      nodes{stargazerCount}
    }
  }
}"""

Q_YEAR = """
query($login:String!, $from:DateTime!, $to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from, to:$to){
      totalCommitContributions
      commitContributionsByRepository(maxRepositories:25){
        repository{nameWithOwner name owner{login} isPrivate
                   primaryLanguage{name color}}
        contributions{totalCount}
      }
    }
  }
}"""


def fetch(login):
    stars, cursor, first = 0, None, None
    while True:
        u = gql(Q_USER, {"login": login, "cursor": cursor})["user"]
        first = first or u
        repos = u["repositories"]
        stars += sum(n["stargazerCount"] for n in repos["nodes"])
        if not repos["pageInfo"]["hasNextPage"]:
            break
        cursor = repos["pageInfo"]["endCursor"]

    commits, per_repo = 0, {}
    for year in first["contributionsCollection"]["contributionYears"]:
        c = gql(Q_YEAR, {"login": login,
                         "from": f"{year}-01-01T00:00:00Z",
                         "to": f"{year}-12-31T23:59:59Z"})["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"]
        for item in c["commitContributionsByRepository"]:
            repo = item["repository"]
            if repo["isPrivate"]:
                continue
            key = repo["nameWithOwner"]
            entry = per_repo.setdefault(key, {
                "name": repo["name"] if repo["owner"]["login"].lower() == login.lower() else key,
                "lang": (repo["primaryLanguage"] or {}).get("name"),
                "color": (repo["primaryLanguage"] or {}).get("color"),
                "commits": 0,
            })
            entry["commits"] += item["contributions"]["totalCount"]

    top = sorted(per_repo.values(), key=lambda r: -r["commits"])[:TOP_N]
    return {
        "commits": commits,
        "prs": first["pullRequests"]["totalCount"],
        "issues": first["issues"]["totalCount"],
        "stars": stars,
        "repos": first["repositories"]["totalCount"],
        "followers": first["followers"]["totalCount"],
        "top": top,
    }


def fit(font, s, size, width):
    if measure(font, s, size) <= width:
        return s
    while s and measure(font, s + "…", size) > width:
        s = s[:-1]
    return s + "…"


def render(data, login):
    W, H = 1200, 440
    d = Doc(W, H, f"GitHub stats for {login}")
    d.add(f'<rect width="{W}" height="{H}" rx="24" fill="{INK}"/>')

    # Left: numbers
    stats = [("commits", "Commits"), ("prs", "Pull requests"), ("issues", "Issues"),
             ("stars", "Stars earned"), ("repos", "Public repos"), ("followers", "Followers")]
    for i, (key, label) in enumerate(stats):
        x, y = 72 + (i % 3) * 172, 158 + (i // 3) * 132
        value = f"{data[key]:,}" if data else "–"
        d.text(x, y, value, "display", 58, PAPER)
        d.text(x, y + 32, label, "semi", 17, MIST)
    when = dt.datetime.now(dt.timezone.utc).strftime("%-d %b %Y")
    d.text(72, 392, f"Updated {when}" if data else "Waiting for the first update",
           "text", 15, MIST)

    d.add(f'<line x1="610" y1="64" x2="610" y2="{H - 64}" stroke="{RULE}" stroke-width="1"/>')

    # Right: most contributed repositories
    x0, x1 = 658, 1128
    d.text(x0, 96, "Most contributed repositories", "semi", 19, PAPER)
    top = (data or {}).get("top") or []
    if not top:
        msg = ("Stats appear here after the first run of the" if not data
               else "No public commits yet.")
        d.text(x0, 150, msg, "text", 17, MIST)
        if not data:
            d.text(x0, 176, "GitHub stats workflow.", "text", 17, MIST)
    peak = max([r["commits"] for r in top] or [1])
    for i, repo in enumerate(top):
        y = 150 + i * 56
        count = f"{repo['commits']:,} commit" + ("" if repo["commits"] == 1 else "s")
        cw = measure("semi", count, 15)
        lang_w = (measure("text", repo["lang"], 14) + 34) if repo["lang"] else 0
        name = fit("semi", repo["name"], 18, x1 - x0 - cw - lang_w - 24)
        d.text(x0, y, name, "semi", 18, PAPER)
        if repo["lang"]:
            lx = x0 + measure("semi", name, 18) + 18
            d.add(f'<circle cx="{lx + 5:.1f}" cy="{y - 5:.1f}" r="5" '
                  f'fill="{repo["color"] or MIST}"/>')
            d.text(lx + 16, y, repo["lang"], "text", 14, MIST)
        d.text(x1, y, count, "semi", 15, MIST, "end")
        bw = max(6, (x1 - x0) * repo["commits"] / peak)
        d.add(f'<rect x="{x0}" y="{y + 13}" width="{x1 - x0}" height="6" rx="3" fill="{RULE}"/>')
        d.add(f'<rect x="{x0}" y="{y + 13}" width="{bw:.1f}" height="6" rx="3" fill="{BUILD}"/>')
    d.render(OUT / "github-stats.svg")


def main():
    login = os.environ.get("GH_LOGIN", "TwanstCodess")
    OUT.mkdir(exist_ok=True)
    load_fonts()
    if "--placeholder" in sys.argv:
        render(None, login)
    elif "--sample" in sys.argv:
        render(json.loads(open(sys.argv[-1]).read()), login)
    else:
        render(fetch(login), login)


if __name__ == "__main__":
    main()
