"""
Real-time GitHub telemetry fetcher for `assets/images/github-stats.svg`.

Uses GitHub REST + GraphQL (when `GITHUB_TOKEN` is set) and Streak JSON endpoints
with zero third-party Python dependencies.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import json
import os
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

LANG_COLORS = {
    "JavaScript": "#F7DF1E",
    "Jupyter Notebook": "#F37626",
    "Python": "#3776AB",
    "TypeScript": "#247BFF",
    "HTML": "#E34F26",
    "CSS": "#1572B6",
    "EJS": "#B4CA65",
    "Kotlin": "#A97BFF",
    "Java": "#ED8B00",
    "C++": "#00599C",
    "C": "#A8B9CC",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "Shell": "#89E051",
}


def _http_json(
    url: str,
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    timeout: float = 12.0,
) -> Any:
    req_headers = {"User-Agent": "alokprasad573-profile-svg-sync/1.0"}
    if headers:
        req_headers.update(headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _github_headers(token: str | None) -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _fetch_paginated_repos(username: str, token: str | None) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{urllib.parse.quote(username)}/repos"
            f"?per_page=100&type=owner&page={page}"
        )
        batch = _http_json(url, headers=_github_headers(token))
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def _aggregate_languages(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1

    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    if not ordered:
        return []

    top_four = ordered[:4]
    remainder = ordered[4:]

    result = [
        {
            "name": name,
            "count": count,
            "color": LANG_COLORS.get(name, "#5EA0FF"),
        }
        for name, count in top_four
    ]

    if remainder:
        rem_count = sum(c for _, c in remainder)
        if len(remainder) <= 3:
            rem_label = " / ".join(name for name, _ in remainder)
        else:
            rem_label = " / ".join(name for name, _ in remainder[:2]) + f" +{len(remainder) - 2}"
        result.append(
            {
                "name": rem_label,
                "count": rem_count,
                "color": "#FF6B7F",
            }
        )
    return result


def _fetch_pr_count(username: str, token: str | None) -> int | None:
    q = urllib.parse.quote(f"author:{username} type:pr")
    data = _http_json(f"https://api.github.com/search/issues?q={q}", headers=_github_headers(token))
    if isinstance(data, dict) and "total_count" in data:
        return int(data["total_count"])
    return None


def _fetch_1y_commits_graphql(username: str, token: str) -> int | None:
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          totalCommitContributions
        }
      }
    }
    """
    res = _http_json(
        "https://api.github.com/graphql",
        headers=_github_headers(token),
        payload={"query": query, "variables": {"login": username}},
    )
    user = (res.get("data") or {}).get("user") if isinstance(res, dict) else None
    if user:
        return int(user["contributionsCollection"]["totalCommitContributions"])
    return None


def _fetch_1y_commits_rest(username: str, token: str | None) -> int | None:
    since = (date.today() - timedelta(days=365)).isoformat()
    q = urllib.parse.quote(f"author:{username} committer-date:>={since} merge:false")
    data = _http_json(f"https://api.github.com/search/commits?q={q}", headers=_github_headers(token))
    if isinstance(data, dict) and "total_count" in data:
        return int(data["total_count"])
    return None


def _fetch_streak_json(username: str) -> dict[str, int] | None:
    url = f"https://streak-stats.demolab.com?user={urllib.parse.quote(username)}&type=json"
    data = _http_json(url, timeout=10.0)
    if not isinstance(data, dict) or "totalContributions" not in data:
        return None
    return {
        "contributions": int(data["totalContributions"]),
        "current_streak": int((data.get("currentStreak") or {}).get("length", 0)),
        "longest_streak": int((data.get("longestStreak") or {}).get("length", 0)),
    }


def _fetch_calendar_graphql(username: str, token: str) -> dict[str, int] | None:
    """Fallback contribution calendar aggregation via GitHub GraphQL if streak endpoint is unavailable."""
    years_q = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection { contributionYears }
      }
    }
    """
    res = _http_json(
        "https://api.github.com/graphql",
        headers=_github_headers(token),
        payload={"query": years_q, "variables": {"login": username}},
    )
    years = (((res.get("data") or {}).get("user") or {}).get("contributionsCollection") or {}).get(
        "contributionYears", []
    )
    if not years:
        return None

    cal_q = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }
    """
    total_contribs = 0
    days: dict[str, int] = {}
    for yr in years:
        r = _http_json(
            "https://api.github.com/graphql",
            headers=_github_headers(token),
            payload={
                "query": cal_q,
                "variables": {
                    "login": username,
                    "from": f"{yr}-01-01T00:00:00Z",
                    "to": f"{yr}-12-31T23:59:59Z",
                },
            },
        )
        cal = (((r.get("data") or {}).get("user") or {}).get("contributionsCollection") or {}).get(
            "contributionCalendar"
        )
        if not cal:
            continue
        total_contribs += int(cal["totalContributions"])
        for wk in cal.get("weeks", []):
            for d in wk.get("contributionDays", []):
                days[d["date"]] = int(d["contributionCount"])

    if not days:
        return None

    sorted_dates = sorted(days.keys())
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    longest = 0
    run = 0
    for dt in sorted_dates:
        if dt > today_str:
            continue
        if days[dt] > 0:
            run += 1
            if run > longest:
                longest = run
        else:
            run = 0

    cur = 0
    cursor = date.fromisoformat(today_str)
    if days.get(today_str, 0) == 0:
        cursor -= timedelta(days=1)
    while days.get(cursor.isoformat(), 0) > 0:
        cur += 1
        cursor -= timedelta(days=1)

    return {
        "contributions": total_contribs,
        "current_streak": cur,
        "longest_streak": longest,
    }


def fetch_live_github_stats(base_cfg: dict[str, Any], username_override: str | None = None) -> tuple[dict[str, Any], bool]:
    """
    Return a copy of `GITHUB_STATS` updated with live GitHub metrics, plus `synced` boolean.
    Falls back cleanly to `base_cfg` defaults if offline or an API limit occurs.
    """
    merged = deepcopy(base_cfg)
    handle = username_override or merged["profile"]["handle"]
    username = handle.lstrip("@").strip()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    any_updated = False
    errors: list[str] = []

    try:
        repos = _fetch_paginated_repos(username, token)
        if repos:
            total_repos = len(repos)
            original_repos = sum(1 for r in repos if not r.get("fork"))
            total_stars = sum(int(r.get("stargazers_count", 0)) for r in repos)
            merged["total_repos"] = total_repos
            merged["repo_totals"][0]["value"] = str(total_repos)
            merged["repo_totals"][1]["value"] = str(original_repos)
            merged["repo_totals"][2]["value"] = f"{total_stars:,}"

            live_langs = _aggregate_languages(repos)
            if live_langs:
                merged["languages"] = live_langs
            any_updated = True
    except Exception as exc:  # noqa: BLE001
        errors.append(f"repos: {exc}")

    try:
        pr_total = _fetch_pr_count(username, token)
        if pr_total is not None:
            merged["kpis"][2]["value"] = f"{pr_total:,}"
            any_updated = True
    except Exception as exc:  # noqa: BLE001
        errors.append(f"prs: {exc}")

    try:
        commits_1y = _fetch_1y_commits_graphql(username, token) if token else None
        if commits_1y is None:
            commits_1y = _fetch_1y_commits_rest(username, token)
        if commits_1y is not None:
            merged["kpis"][1]["value"] = f"{commits_1y:,}"
            any_updated = True
    except Exception as exc:  # noqa: BLE001
        errors.append(f"commits: {exc}")

    streak_data = None
    try:
        streak_data = _fetch_streak_json(username)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"streak: {exc}")

    if streak_data is None and token:
        try:
            streak_data = _fetch_calendar_graphql(username, token)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"calendar_gql: {exc}")

    if streak_data is not None:
        merged["kpis"][0]["value"] = f"{streak_data['contributions']:,}"
        merged["kpis"][3]["value"] = f"{streak_data['current_streak']}d"
        merged["kpis"][4]["value"] = f"{streak_data['longest_streak']}d"
        any_updated = True

    if any_updated:
        today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        merged["profile"]["snapshot_label"] = f"LIVE SYNC · {today_utc}"

    if errors:
        print(f"[live-stats] Partial/fallback notes for @{username}: {'; '.join(errors)}")

    return merged, any_updated
