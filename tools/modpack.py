#!/usr/bin/env python3
"""Build tooling for the Alola modpack.

Standard library only (Python 3.11+). Subcommands:

  resolve   Turn modlist.toml into modpack.lock.json using the Modrinth API.
            Pinned mods (e.g. Cobblemon) are resolved first and become
            "anchors": every other mod gets the newest version whose
            fabric.mod.json accepts the anchors, Minecraft and the loader.
  validate  Download every locked jar and check all fabric.mod.json
            depends/breaks for the client and the server separately.
  build     Build the Alola data mod and the .mrpack into dist/.
  docs      Regenerate MODS.md from the lockfile.
  server    Assemble a runnable Fabric server from the lockfile.
  client    Assemble a client game directory (used by the CI client test).
  boot      Start that server, wait for "Done", stop it, and check the log.
  inspect   List files inside a locked jar (handy for finding item ids).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODLIST = ROOT / "modlist.toml"
LOCK = ROOT / "modpack.lock.json"
MODS_MD = ROOT / "MODS.md"
CACHE = ROOT / ".cache" / "downloads"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
ALOLA_SRC = ROOT / "alola"

API = "https://api.modrinth.com/v2"
FABRIC_META = "https://meta.fabricmc.net/v2"
USER_AGENT = "letsgotomcdonaldsnow-creator/Modpack (Alola modpack build tooling)"

KIND_DIRS = {"mod": "mods", "resourcepack": "resourcepacks", "shader": "shaderpacks"}
KIND_LOADERS = {"mod": ["fabric"], "resourcepack": ["minecraft"], "shader": ["iris", "optifine"]}
MAX_CANDIDATES = 15


def log(msg: str = "") -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- http

def http_get(url: str, *, binary: bool = False, retries: int = 5):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
            return data if binary else json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code in (400, 404, 410):
                raise
            last = e
            if e.code == 429:
                time.sleep(int(e.headers.get("X-Ratelimit-Reset", "15")) + 1)
                continue
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
        time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"GET {url} failed: {last}")


def api(path: str, **params):
    query = "&".join(f"{k}={urllib.parse.quote(json.dumps(v) if not isinstance(v, str) else v)}"
                     for k, v in params.items())
    return http_get(f"{API}{path}" + (f"?{query}" if query else ""))


def download(url: str, sha1: str, filename: str) -> Path:
    """Download into the content-addressed cache and verify the sha1."""
    dest = CACHE / sha1[:2] / sha1 / filename
    if dest.exists() and file_sha1(dest) == sha1:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = http_get(url, binary=True)
    got = hashlib.sha1(data).hexdigest()
    if got != sha1:
        raise RuntimeError(f"sha1 mismatch for {filename}: expected {sha1}, got {got}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return dest


def file_sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------ fabric versions

def parse_version(text: str):
    """Parse a Fabric-style semantic version. Returns (numbers, prerelease) or None.

    Build metadata (+...) is ignored, like Fabric Loader does when comparing.
    Components may be the wildcards x/X/* (only meaningful in predicates).
    """
    text = text.strip().split("+", 1)[0]
    pre = None
    if "-" in text:
        text, pre = text.split("-", 1)
    if not text:
        return None
    nums = []
    for part in text.split("."):
        if part in ("x", "X", "*"):
            nums.append("x")
        elif part.isdigit():
            nums.append(int(part))
        else:
            return None
    return nums, pre


def compare_versions(a, b) -> int:
    an, ap = a
    bn, bp = b
    for i in range(max(len(an), len(bn))):
        x = an[i] if i < len(an) else 0
        y = bn[i] if i < len(bn) else 0
        x = 0 if x == "x" else x
        y = 0 if y == "x" else y
        if x != y:
            return -1 if x < y else 1
    if ap is None and bp is None:
        return 0
    if ap is None:
        return 1
    if bp is None:
        return -1
    ai = ap.split(".") if ap else []
    bi = bp.split(".") if bp else []
    for x, y in zip(ai, bi):
        if x == y:
            continue
        if x.isdigit() and y.isdigit():
            return -1 if int(x) < int(y) else 1
        if x.isdigit():
            return -1
        if y.isdigit():
            return 1
        return -1 if x < y else 1
    return (len(ai) > len(bi)) - (len(ai) < len(bi))


def _term_matches(term: str, version: str) -> bool:
    term = term.strip()
    if term in ("", "*"):
        return True
    op = ""
    for candidate in (">=", "<=", ">", "<", "=", "~", "^"):
        if term.startswith(candidate):
            op, term = candidate, term[len(candidate):].strip()
            break
    want = parse_version(term)
    have = parse_version(version)
    if want is None or have is None:
        # Non-semantic versions: Fabric only supports equality there.
        return op in ("", "=") and term == version or op not in ("", "=")
    nums, pre = want
    if "x" in nums:
        idx = nums.index("x")
        lower = ([n if n != "x" else 0 for n in nums], "")
        if idx == 0:
            return True
        upper_nums = [n for n in nums[:idx]]
        upper_nums[-1] += 1
        return compare_versions(have, lower) >= 0 and compare_versions(have, (upper_nums, "")) < 0
    c = compare_versions(have, want)
    if op in ("", "="):
        return c == 0
    if op == ">=":
        return c >= 0
    if op == "<=":
        return c <= 0
    if op == ">":
        return c > 0
    if op == "<":
        return c < 0
    if op == "~":
        upper = list(nums[:2]) if len(nums) >= 2 else [nums[0], 0]
        upper[-1] += 1
        return c >= 0 and compare_versions(have, (upper, "")) < 0
    if op == "^":
        return c >= 0 and compare_versions(have, ([nums[0] + 1], "")) < 0
    return True


def predicate_matches(predicate, version: str) -> bool:
    """Fabric dependency predicate: a string (space separated AND) or a list (OR)."""
    if isinstance(predicate, list):
        return any(predicate_matches(p, version) for p in predicate) if predicate else True
    return all(_term_matches(t, version) for t in str(predicate).split())


# --------------------------------------------------------- fabric.mod.json io

def _strip_json5(text: str) -> str:
    """Remove comments and trailing commas outside of strings (lenient fabric.mod.json)."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        else:
            out.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_fmj(raw: bytes) -> dict:
    text = raw.decode("utf-8-sig", errors="replace")
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        return json.loads(_strip_json5(text), strict=False)


def read_jar_mods(data: bytes, nested: bool = False, depth: int = 0) -> list[dict]:
    """Return fabric.mod.json info for a jar and everything it nests."""
    mods = []
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return mods
    with zf:
        try:
            fmj = load_fmj(zf.read("fabric.mod.json"))
        except KeyError:
            return mods
        except (json.JSONDecodeError, UnicodeDecodeError):
            return mods
        version = str(fmj.get("version", "0"))
        mods.append({
            "id": fmj.get("id"),
            "version": version,
            "provides": list(fmj.get("provides", []) or []),
            "environment": fmj.get("environment", "*"),
            "depends": fmj.get("depends", {}) or {},
            "breaks": fmj.get("breaks", {}) or {},
            "name": fmj.get("name", fmj.get("id")),
            "nested": nested,
        })
        if depth < 4:
            for entry in fmj.get("jars", []) or []:
                path = entry.get("file") if isinstance(entry, dict) else None
                if not path:
                    continue
                try:
                    inner = zf.read(path)
                except KeyError:
                    continue
                mods.extend(read_jar_mods(inner, nested=True, depth=depth + 1))
    return mods


# ------------------------------------------------------------------- modlist

def load_modlist():
    data = tomllib.loads(MODLIST.read_text(encoding="utf-8"))
    pack = data["pack"]
    entries = []
    for key, cat in data.get("category", {}).items():
        for mod in cat.get("mods", []):
            entry = dict(mod)
            entry["category"] = cat.get("title", key)
            entry.setdefault("kind", "mod")
            entries.append(entry)
    return pack, entries


def read_lock() -> dict:
    if LOCK.exists():
        return json.loads(LOCK.read_text(encoding="utf-8"))
    return {}


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def latest_fabric_loader() -> str:
    for loader in http_get(f"{FABRIC_META}/versions/loader"):
        if loader.get("stable"):
            return loader["version"]
    raise RuntimeError("no stable fabric loader found")


def builtin_mods(minecraft: str, loader: str) -> dict[str, list[str]]:
    return {
        "minecraft": [minecraft],
        "java": ["21"],
        "fabricloader": [loader],
        "fabric-loader": [loader],
        "mixinextras": ["0.5.0"],
    }


# --------------------------------------------------------------------- resolve

class Resolver:
    def __init__(self, pack: dict, entries: list[dict], lock: dict, upgrade: bool):
        self.pack = pack
        self.entries = entries
        self.old = {f["project_id"]: f for f in lock.get("files", [])} if not upgrade else {}
        self.minecraft = pack["minecraft"]
        self.game_versions = pack.get("game_versions", [self.minecraft])
        loader = pack.get("fabric_loader", "latest")
        if loader == "latest":
            loader = lock.get("fabric_loader") if (lock and not upgrade) else None
            loader = loader or latest_fabric_loader()
        self.loader = loader
        self.anchors: dict[str, list[str]] = builtin_mods(self.minecraft, self.loader)
        self.projects: dict[str, dict] = {}
        self.chosen: dict[str, dict] = {}
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.incompatible: list[tuple[str, str]] = []

    # -- modrinth lookups
    def fetch_projects(self, keys: list[str]) -> None:
        missing = [k for k in keys if k not in self.projects]
        for i in range(0, len(missing), 80):
            chunk = missing[i:i + 80]
            for proj in api("/projects", ids=chunk):
                self.projects[proj["id"]] = proj
                self.projects[proj["slug"]] = proj

    def versions_for(self, project_id: str, kind: str) -> list[dict]:
        loaders = KIND_LOADERS[kind]
        versions = api(f"/project/{project_id}/version", loaders=loaders, game_versions=self.game_versions)
        versions.sort(key=lambda v: v["date_published"], reverse=True)
        return versions

    # -- candidate selection
    def candidates(self, entry: dict, versions: list[dict]) -> list[dict]:
        pin = entry.get("pin")
        if pin:
            versions = [v for v in versions if v["id"] == pin or v["version_number"] == pin
                        or v["version_number"].split("+")[0] == pin
                        or re.search(rf"(^|[^0-9.]){re.escape(pin)}([^0-9]|$)", v["version_number"])]
        match = entry.get("match")
        if match:
            versions = [v for v in versions if re.search(match, v["version_number"])
                        or any(re.search(match, f["filename"]) for f in v["files"])]
        exact = [v for v in versions if self.minecraft in v["game_versions"]]
        loose = [v for v in versions if self.minecraft not in v["game_versions"]]
        ordered = exact + loose
        allowed = {"release", "beta"} | ({"alpha"} if entry.get("allow_alpha") else set())
        return [v for v in ordered if v["version_type"] in allowed] + \
               [v for v in ordered if v["version_type"] not in allowed]

    @staticmethod
    def primary_file(version: dict) -> dict:
        files = version["files"]
        for f in files:
            if f.get("primary"):
                return f
        jars = [f for f in files if not re.search(r"-(sources|dev|api|javadoc)\.jar$", f["filename"])]
        return (jars or files)[0]

    def check_jar(self, mods: list[dict]) -> str | None:
        """Return a reason string if the jar rejects an anchor, else None."""
        if not mods:
            return "no fabric.mod.json"
        top = mods[0]
        for dep, pred in top["depends"].items():
            if dep in self.anchors and not any(predicate_matches(pred, v) for v in self.anchors[dep]):
                return f"needs {dep} {pred}, pack has {', '.join(self.anchors[dep])}"
        for dep, pred in top["breaks"].items():
            if dep in self.anchors and any(predicate_matches(pred, v) for v in self.anchors[dep]):
                return f"breaks with {dep} {pred}"
        return None

    def choose(self, entry: dict, project: dict) -> dict | None:
        kind = entry["kind"]
        versions = self.versions_for(project["id"], kind)
        cands = self.candidates(entry, versions)
        if not cands:
            where = f"pin {entry['pin']!r}" if entry.get("pin") else f"{'/'.join(KIND_LOADERS[kind])} {self.minecraft}"
            if entry.get("match"):
                where += f" matching {entry['match']!r}"
            self.errors.append(f"{project['slug']}: no version for {where}")
            return None
        if kind != "mod" or entry.get("skip_compat"):
            v = cands[0]
            return {"version": v, "file": self.primary_file(v), "mods": []}
        reasons = []
        for v in cands[:MAX_CANDIDATES]:
            f = self.primary_file(v)
            if not f["filename"].endswith(".jar"):
                reasons.append(f"{v['version_number']}: not a jar")
                continue
            path = download(f["url"], f["hashes"]["sha1"], f["filename"])
            mods = read_jar_mods(path.read_bytes())
            why = self.check_jar(mods)
            if why is None:
                return {"version": v, "file": f, "mods": mods}
            reasons.append(f"{v['version_number']}: {why}")
        self.errors.append(f"{project['slug']}: no compatible version ({'; '.join(reasons[:6])})")
        return None

    def record(self, entry: dict, project: dict, pick: dict, explicit: bool) -> dict:
        v, f, kind = pick["version"], pick["file"], entry["kind"]
        deps = []
        for d in v.get("dependencies", []):
            pid = d.get("project_id")
            if not pid and d.get("version_id"):
                try:
                    pid = api(f"/version/{d['version_id']}")["project_id"]
                except Exception:  # noqa: BLE001 - informational only
                    pid = None
            if not pid:
                continue
            if d["dependency_type"] == "required":
                deps.append(pid)
            elif d["dependency_type"] == "incompatible":
                self.incompatible.append((project["id"], pid))
        top = pick["mods"][0] if pick["mods"] else None
        return {
            "project_id": project["id"],
            "slug": project["slug"],
            "title": project["title"],
            "kind": kind,
            "category": entry.get("category", "Libraries & dependencies"),
            "explicit": explicit,
            "note": entry.get("note", ""),
            "pin": entry.get("pin"),
            "match": entry.get("match"),
            "side": entry.get("side"),
            "optional": bool(entry.get("optional")),
            "project_client_side": project.get("client_side"),
            "project_server_side": project.get("server_side"),
            "version_id": v["id"],
            "version_number": v["version_number"],
            "version_type": v["version_type"],
            "filename": f["filename"],
            "path": f"{KIND_DIRS[kind]}/{f['filename']}",
            "url": f["url"],
            "sha1": f["hashes"]["sha1"],
            "sha512": f["hashes"]["sha512"],
            "size": f["size"],
            "deps": sorted(set(deps)),
            "fabric_id": top["id"] if top else None,
            "fabric_version": top["version"] if top else None,
        }

    def reuse(self, entry: dict, project: dict) -> dict | None:
        old = self.old.get(project["id"])
        if not old or old.get("pin") != entry.get("pin") or old.get("match") != entry.get("match") \
                or old.get("kind") != entry["kind"]:
            return None
        rec = dict(old)
        rec.update(category=entry.get("category", old["category"]), note=entry.get("note", ""),
                   side=entry.get("side"), optional=bool(entry.get("optional")))
        return rec

    def add_anchor(self, rec: dict) -> None:
        if rec["kind"] != "mod":
            return
        path = download(rec["url"], rec["sha1"], rec["filename"])
        for m in read_jar_mods(path.read_bytes()):
            if m["nested"]:
                continue
            for mid in [m["id"], *m["provides"]]:
                self.anchors.setdefault(mid, []).append(m["version"])

    def run(self) -> dict:
        keys = [e["id"] for e in self.entries]
        self.fetch_projects(keys)
        explicit: dict[str, dict] = {}
        for e in self.entries:
            proj = self.projects.get(e["id"])
            if not proj:
                self.errors.append(f"{e['id']}: project not found on Modrinth")
                continue
            if proj["id"] in explicit:
                self.warnings.append(f"{e['id']}: listed twice")
            e["_project"] = proj
            explicit[proj["id"]] = e

        # Anchors (pinned mods) first so everything else is checked against them.
        ordered = sorted(explicit.values(), key=lambda e: 0 if e.get("anchor") else 1)
        queue: list[tuple[dict, dict, bool]] = [(e, e["_project"], True) for e in ordered]
        anchors_done = False
        while queue:
            entry, proj, is_explicit = queue.pop(0)
            if proj["id"] in self.chosen:
                continue
            if not anchors_done and not entry.get("anchor"):
                anchors_done = True
                log(f"anchors: " + ", ".join(f"{k}={'/'.join(v)}" for k, v in self.anchors.items()
                                             if k not in ("java", "fabric-loader", "mixinextras")))
            rec = self.reuse(entry, proj)
            if rec is None:
                pick = self.choose(entry, proj)
                if pick is None:
                    continue
                rec = self.record(entry, proj, pick, is_explicit)
                deps = pick["mods"][0]["depends"] if pick["mods"] else {}
                extra = f"  [cobblemon {deps['cobblemon']}]" if "cobblemon" in deps else ""
                log(f"  + {rec['slug']:<44} {rec['version_number']}{extra}")
            if entry.get("anchor"):
                self.add_anchor(rec)
            self.chosen[proj["id"]] = rec
            new_deps = [d for d in rec["deps"] if d not in self.chosen]
            if new_deps:
                self.fetch_projects(new_deps)
            for dep in new_deps:
                if dep in explicit:
                    continue  # it will be (or was) resolved with its own settings
                dproj = self.projects.get(dep)
                if not dproj:
                    self.errors.append(f"{rec['slug']}: dependency {dep} not found")
                    continue
                kind = "mod" if dproj["project_type"] in ("mod", "plugin") else dproj["project_type"]
                if kind not in KIND_DIRS:
                    self.warnings.append(f"{rec['slug']}: skipping dependency {dproj['slug']} ({kind})")
                    continue
                queue.append(({"id": dep, "kind": kind, "category": "Libraries & dependencies"}, dproj, False))

        files = list(self.chosen.values())
        self.assign_envs(files)
        for a, b in self.incompatible:
            if a in self.chosen and b in self.chosen:
                self.warnings.append(f"Modrinth marks {self.chosen[a]['slug']} incompatible with {self.chosen[b]['slug']}")
        files.sort(key=lambda f: (0 if f["explicit"] else 1, f["path"].lower()))
        return {
            "name": self.pack["name"],
            "version": self.pack["version"],
            "minecraft": self.minecraft,
            "fabric_loader": self.loader,
            "files": files,
        }

    @staticmethod
    def assign_envs(files: list[dict]) -> None:
        by_id = {f["project_id"]: f for f in files}
        for f in files:
            f["env"] = explicit_env(f)
        # Libraries only go where something that needs them goes.
        for _ in range(10):
            changed = False
            for f in files:
                if f["explicit"]:
                    continue
                dependents = [g for g in files if f["project_id"] in g["deps"]]
                if not dependents:
                    continue
                env = dict(f["env"])
                for side in ("client", "server"):
                    wanted = any(g["env"][side] != "unsupported" for g in dependents)
                    base = explicit_env(f)[side]
                    env[side] = base if wanted else "unsupported"
                    if wanted and base == "unsupported":
                        env[side] = "required"
                if env != f["env"]:
                    f["env"], changed = env, True
            if not changed:
                break
        for f in files:
            f["required_by"] = sorted(g["slug"] for g in files if f["project_id"] in g["deps"])
            del_keys = [k for k in f if k.startswith("_")]
            for k in del_keys:
                del f[k]
        _ = by_id


def explicit_env(f: dict) -> dict:
    kind, side = f["kind"], f.get("side")
    if kind in ("resourcepack", "shader"):
        client, server = "required", "unsupported"
    elif side == "client":
        client, server = "required", "unsupported"
    elif side == "server":
        client, server = "unsupported", "required"
    elif side == "both":
        client = server = "required"
    else:
        # Single-player runs an integrated server, so server-side mods belong on the client too.
        client = "required"
        server = "unsupported" if f.get("project_server_side") == "unsupported" else "required"
    if f.get("optional") and client != "unsupported":
        client = "optional"
    return {"client": client, "server": server}


def cmd_resolve(args) -> int:
    pack, entries = load_modlist()
    lock = read_lock()
    resolver = Resolver(pack, entries, lock, args.upgrade)
    log(f"Resolving {len(entries)} listed projects for Minecraft {resolver.minecraft}, Fabric {resolver.loader}")
    new_lock = resolver.run()
    write_json(LOCK, new_lock)
    write_mods_md(new_lock)
    counts = {}
    for f in new_lock["files"]:
        counts[f["kind"]] = counts.get(f["kind"], 0) + 1
    log(f"\nLocked {len(new_lock['files'])} files: " + ", ".join(f"{v} {k}s" for k, v in counts.items()))
    for w in resolver.warnings:
        log(f"WARNING: {w}")
    report = BUILD / "resolve-errors.txt"
    BUILD.mkdir(exist_ok=True)
    if resolver.errors:
        log(f"\n{len(resolver.errors)} RESOLVE ERRORS:")
        for e in resolver.errors:
            log(f"RESOLVE-ERROR: {e}")
        report.write_text("\n".join(resolver.errors) + "\n")
        return 0 if args.keep_going else 1
    report.unlink(missing_ok=True)
    return 0


# -------------------------------------------------------------------- validate

def locked_jar_mods(entry: dict) -> list[dict]:
    path = download(entry["url"], entry["sha1"], entry["filename"])
    return read_jar_mods(path.read_bytes())


def cmd_validate(args) -> int:
    lock = read_lock()
    mods = [f for f in lock["files"] if f["kind"] == "mod"]
    log(f"Validating {len(mods)} mod jars")
    infos = {f["project_id"]: locked_jar_mods(f) for f in mods}
    alola = alola_mod_info(lock)
    errors: list[str] = []
    for side in ("client", "server"):
        present = [f for f in mods if f["env"][side] != "unsupported"]
        provided: dict[str, list[str]] = {k: list(v) for k, v in builtin_mods(lock["minecraft"], lock["fabric_loader"]).items()}
        top_ids: dict[str, str] = {}
        loaded: list[tuple[str, dict]] = []
        for f in present:
            jar_mods = infos[f["project_id"]]
            if not jar_mods:
                errors.append(f"[{side}] {f['slug']}: {f['filename']} has no fabric.mod.json")
                continue
            if jar_mods[0]["environment"] not in ("*", side):
                continue  # Fabric skips mods for the other environment
            for m in jar_mods:
                if m["environment"] not in ("*", side):
                    continue
                if not m["nested"]:
                    if m["id"] in top_ids:
                        errors.append(f"[{side}] duplicate mod id {m['id']}: {top_ids[m['id']]} and {f['slug']}")
                    top_ids[m["id"]] = f["slug"]
                for mid in [m["id"], *m["provides"]]:
                    provided.setdefault(mid, []).append(m["version"])
                loaded.append((f["slug"], m))
        loaded.append(("alola-adventure", alola))
        for mid in [alola["id"]]:
            provided.setdefault(mid, []).append(alola["version"])
        for slug, m in loaded:
            label = f"{slug}" + (f" (nested {m['id']})" if m["nested"] else "")
            for dep, pred in m["depends"].items():
                if dep not in provided:
                    errors.append(f"[{side}] {label} requires {dep} {pred} but nothing provides it")
                elif not any(predicate_matches(pred, v) for v in provided[dep]):
                    errors.append(f"[{side}] {label} requires {dep} {pred}, found {', '.join(sorted(set(provided[dep])))}")
            for dep, pred in m["breaks"].items():
                if dep in provided and any(predicate_matches(pred, v) for v in provided[dep]):
                    errors.append(f"[{side}] {label} breaks with {dep} {pred} (found {', '.join(sorted(set(provided[dep])))})")
        log(f"[{side}] {len(present)} jars, {len(top_ids)} top-level mods")
    log("Declared Cobblemon ranges:")
    for f in mods:
        jar = infos[f["project_id"]]
        if jar and "cobblemon" in jar[0]["depends"]:
            log(f"  {f['slug']:<48} {f['version_number']:<36} cobblemon {jar[0]['depends']['cobblemon']}")
    errors += check_alola_ids(lock)
    for w in check_spawn_presets(lock):
        log(f"VALIDATE-WARNING: {w}")
    for e in sorted(set(errors)):
        log(f"VALIDATE-ERROR: {e}")
    if errors:
        log(f"{len(set(errors))} validation errors")
        return 1
    log("All dependencies satisfied on client and server.")
    return 0


# --------------------------------------------------------- reproducible zips

ZIP_DATE = (2024, 1, 1, 0, 0, 0)


def zip_add_bytes(zf: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, data)


def zip_add_file(zf: zipfile.ZipFile, name: str, path: Path) -> None:
    zip_add_bytes(zf, name, path.read_bytes())


# ----------------------------------------------------------------- alola jar

ID_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")


def alola_ids() -> tuple[set[str], set[str]]:
    """Item and species ids referenced by the Alola data mod."""
    items, species = set(), set()

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("id"), str) and ID_RE.match(node["id"]) and "components" in node or \
                    set(node) <= {"id", "count", "components"} and isinstance(node.get("id"), str):
                items.add(node["id"])
            pi = node.get("cobblemon:pokemon_item")
            if isinstance(pi, dict) and pi.get("species"):
                species.add(pi["species"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for path in (ALOLA_SRC / "data").rglob("advancement/**/*.json"):
        walk(json.loads(path.read_text(encoding="utf-8")))
    for path in (ALOLA_SRC / "data").rglob("*.mcfunction"):
        for m in re.finditer(r"^\s*give\s+\S+\s+([a-z0-9_.-]+:[a-z0-9_./-]+)", path.read_text(encoding="utf-8"), re.M):
            items.add(m.group(1))
    return items, species


def check_spawn_presets(lock: dict) -> list[str]:
    """Warn about Cobblemon spawn entries that use presets no installed mod defines."""
    defined: set[str] = set()
    used: dict[str, set[str]] = {}
    sources = [(f["slug"], download(f["url"], f["sha1"], f["filename"]).read_bytes())
               for f in lock["files"] if f["kind"] == "mod"]
    alola_zip = io.BytesIO()
    with zipfile.ZipFile(alola_zip, "w") as zf:
        for path in ALOLA_SRC.rglob("*.json"):
            zf.write(path, path.relative_to(ALOLA_SRC).as_posix())
    sources.append(("alola-adventure", alola_zip.getvalue()))
    for slug, data in sources:
        try:
            zf = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile:
            continue
        with zf:
            for n in zf.namelist():
                m = re.match(r"data/[^/]+/spawn_detail_presets/(.+)\.json$", n)
                if m:
                    defined.add(m.group(1))
                elif re.match(r"data/[^/]+/spawn_pool_world/.+\.json$", n):
                    try:
                        spawns = load_fmj(zf.read(n)).get("spawns", [])
                    except (json.JSONDecodeError, AttributeError):
                        continue
                    for sp in spawns:
                        for preset in sp.get("presets", []) or []:
                            used.setdefault(preset, set()).add(slug)
    return [f"spawn preset '{preset}' is not defined by any installed mod; used by {', '.join(sorted(slugs))}"
            for preset, slugs in sorted(used.items()) if preset not in defined]


def check_alola_ids(lock: dict) -> list[str]:
    items, species = alola_ids()
    known_items: set[str] = set()
    known_species: set[str] = set()
    for f in lock["files"]:
        if f["kind"] != "mod":
            continue
        path = download(f["url"], f["sha1"], f["filename"])
        with zipfile.ZipFile(path) as zf:
            for n in zf.namelist():
                m = re.match(r"assets/([^/]+)/models/item/(.+)\.json$", n)
                if m:
                    known_items.add(f"{m.group(1)}:{m.group(2)}")
                m = re.match(r"data/([^/]+)/species/(?:[^/]+/)*([^/]+)\.json$", n)
                if m:
                    known_species.add(f"{m.group(1)}:{m.group(2)}")
    errors = [f"alola data uses unknown item {i}" for i in sorted(items)
              if not i.startswith("minecraft:") and i not in known_items]
    errors += [f"alola data uses unknown species {s}" for s in sorted(species) if s not in known_species]
    log(f"Checked {len(items)} item ids and {len(species)} species ids used by the Alola data mod")
    return errors


def alola_mod_info(lock: dict | None = None) -> dict:
    fmj = json.loads((ALOLA_SRC / "fabric.mod.json").read_text(encoding="utf-8"))
    return {"id": fmj["id"], "version": fmj["version"], "provides": [], "environment": "*",
            "depends": fmj.get("depends", {}), "breaks": {}, "name": fmj["name"], "nested": False}


def build_alola_jar() -> Path:
    fmj = json.loads((ALOLA_SRC / "fabric.mod.json").read_text(encoding="utf-8"))
    BUILD.mkdir(exist_ok=True)
    out = BUILD / f"alola-adventure-{fmj['version']}.jar"
    # Validate every JSON file so a typo fails the build, not the game.
    for path in sorted(ALOLA_SRC.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SystemExit(f"invalid JSON in {path.relative_to(ROOT)}: {e}")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ALOLA_SRC.rglob("*")):
            if path.is_file():
                zip_add_file(zf, path.relative_to(ALOLA_SRC).as_posix(), path)
    return out


# ----------------------------------------------------------------------- build

def default_options(lock: dict) -> str:
    packs = ["vanilla", "fabric"]
    for f in lock["files"]:
        if f["kind"] == "resourcepack" and f["env"]["client"] != "unsupported":
            packs.append(f"file/{f['filename']}")
    base = ROOT / "defaults" / "options.txt"
    lines = base.read_text(encoding="utf-8").splitlines() if base.exists() else []
    lines = [ln for ln in lines if not ln.startswith("resourcePacks:")]
    lines.append("resourcePacks:" + json.dumps(packs, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def iris_properties(lock: dict) -> str | None:
    shaders = [f for f in lock["files"] if f["kind"] == "shader"]
    if not shaders:
        return None
    return (f"shaderPack={shaders[0]['filename']}\n"
            "enableShaders=false\n")


def cmd_build(args) -> int:
    pack, _ = load_modlist()
    lock = read_lock()
    DIST.mkdir(exist_ok=True)
    alola_jar = build_alola_jar()
    index = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": pack["version"],
        "name": pack["name"],
        "summary": pack.get("summary", ""),
        "files": [{
            "path": f["path"],
            "hashes": {"sha1": f["sha1"], "sha512": f["sha512"]},
            "env": f["env"],
            "downloads": [f["url"]],
            "fileSize": f["size"],
        } for f in lock["files"]],
        "dependencies": {"minecraft": lock["minecraft"], "fabric-loader": lock["fabric_loader"]},
    }
    name = re.sub(r"[^A-Za-z0-9]+", "-", pack["name"]).strip("-")
    out = DIST / f"{name}-{pack['version']}.mrpack"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zip_add_bytes(zf, "modrinth.index.json", json.dumps(index, indent=2, ensure_ascii=False).encode())
        for folder in ("overrides", "client-overrides", "server-overrides"):
            base = ROOT / folder
            if base.exists():
                for path in sorted(base.rglob("*")):
                    if path.is_file() and path.name != ".gitkeep":
                        zip_add_file(zf, f"{folder}/{path.relative_to(base).as_posix()}", path)
        zip_add_file(zf, f"overrides/mods/{alola_jar.name}", alola_jar)
        zip_add_bytes(zf, "client-overrides/config/yosbr/options.txt", default_options(lock).encode())
        iris = iris_properties(lock)
        if iris:
            zip_add_bytes(zf, "client-overrides/config/yosbr/config/iris.properties", iris.encode())
    log(f"Wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KiB, {len(index['files'])} files)")
    if args.publish:
        published = ROOT / f"{name}.mrpack"
        shutil.copy2(out, published)
        log(f"Copied to {published.relative_to(ROOT)}")
    return 0


# ------------------------------------------------------------------------ docs

SIDE_LABEL = {("required", "required"): "both", ("required", "unsupported"): "client",
              ("optional", "unsupported"): "client (optional)", ("optional", "required"): "both (client optional)",
              ("unsupported", "required"): "server"}


def write_mods_md(lock: dict) -> None:
    files = lock["files"]
    cats: dict[str, list[dict]] = {}
    for f in files:
        cats.setdefault(f["category"], []).append(f)
    lines = [f"# {lock['name']} {lock['version']}: full mod list", "",
             "Generated from `modpack.lock.json` by `tools/modpack.py`. Do not edit by hand.", "",
             f"Minecraft **{lock['minecraft']}**, Fabric Loader **{lock['fabric_loader']}**, "
             f"**{len(files)}** files ({sum(1 for f in files if f['kind'] == 'mod')} mods).", ""]
    try:
        _, entries = load_modlist()
        order = list(dict.fromkeys(e["category"] for e in entries))
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        order = []
    order = [c for c in order if c in cats] + [c for c in cats if c not in order]
    for cat in order:
        lines += [f"## {cat}", "", "| Project | Version | Side | Why |", "| --- | --- | --- | --- |"]
        for f in sorted(cats[cat], key=lambda f: f["title"].lower()):
            kind = {"mod": "mod", "resourcepack": "resourcepack", "shader": "shader"}[f["kind"]]
            url = f"https://modrinth.com/{kind}/{f['slug']}"
            side = SIDE_LABEL.get((f["env"]["client"], f["env"]["server"]), f"{f['env']['client']}/{f['env']['server']}")
            why = f["note"] or ("needed by " + ", ".join(f["required_by"]) if f["required_by"] else "")
            title = f["title"].replace("|", "\\|")
            lines.append(f"| [{title}]({url}) | `{f['version_number']}` | {side} | {why.replace('|', '/')} |")
        lines.append("")
    MODS_MD.write_text("\n".join(lines), encoding="utf-8")


def cmd_docs(args) -> int:
    write_mods_md(read_lock())
    log(f"Wrote {MODS_MD.relative_to(ROOT)}")
    return 0


# ---------------------------------------------------------------------- server

def cmd_server(args) -> int:
    lock = read_lock()
    target = Path(args.dir).resolve()
    (target / "mods").mkdir(parents=True, exist_ok=True)
    installer = next(i["version"] for i in http_get(f"{FABRIC_META}/versions/installer") if i.get("stable"))
    launcher = http_get(f"{FABRIC_META}/versions/loader/{lock['minecraft']}/{lock['fabric_loader']}/{installer}/server/jar",
                        binary=True)
    (target / "fabric-server-launch.jar").write_bytes(launcher)
    count = 0
    for f in lock["files"]:
        if f["env"]["server"] == "unsupported":
            continue
        src = download(f["url"], f["sha1"], f["filename"])
        dest = target / f["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        count += 1
    jar = build_alola_jar()
    shutil.copy2(jar, target / "mods" / jar.name)
    for folder in ("overrides", "server-overrides"):
        base = ROOT / folder
        if base.exists():
            shutil.copytree(base, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".gitkeep"))
    if args.accept_eula:
        (target / "eula.txt").write_text("eula=true\n")
    log(f"Server assembled in {target} with {count + 1} files (Fabric {lock['fabric_loader']}, installer {installer})")
    log(f"Start it with: java -Xmx6G -jar fabric-server-launch.jar nogui")
    return 0


# ---------------------------------------------------------------------- client

def cmd_client(args) -> int:
    """Assemble a client game directory (what a launcher would install from the .mrpack)."""
    lock = read_lock()
    target = Path(args.dir).resolve()
    count = 0
    for f in lock["files"]:
        if f["env"]["client"] == "unsupported":
            continue
        if args.skip and any(re.search(rx, f["slug"]) for rx in args.skip):
            log(f"  skipping {f['slug']}")
            continue
        src = download(f["url"], f["sha1"], f["filename"])
        dest = target / f["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        count += 1
    jar = build_alola_jar()
    (target / "mods").mkdir(parents=True, exist_ok=True)
    shutil.copy2(jar, target / "mods" / jar.name)
    for folder in ("overrides", "client-overrides"):
        base = ROOT / folder
        if base.exists():
            shutil.copytree(base, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".gitkeep"))
    yosbr = target / "config" / "yosbr"
    yosbr.mkdir(parents=True, exist_ok=True)
    (yosbr / "options.txt").write_text(default_options(lock), encoding="utf-8")
    iris = iris_properties(lock)
    if iris:
        (yosbr / "config").mkdir(exist_ok=True)
        (yosbr / "config" / "iris.properties").write_text(iris, encoding="utf-8")
    log(f"Client assembled in {target} with {count + 1} files")
    return 0


# ------------------------------------------------------------------------ boot

BAD_LOG = re.compile(r"(Exception|Error|Failed|Couldn't|Could not|Unable|Unknown|Invalid|Missing)", re.I)


def cmd_boot(args) -> int:
    target = Path(args.dir).resolve()
    cmd = ["java", f"-Xmx{args.memory}", "-jar", "fabric-server-launch.jar", "nogui"]
    log(f"Booting server: {' '.join(cmd)}")
    start = time.time()
    proc = subprocess.Popen(cmd, cwd=target, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors="replace")
    lines: list[str] = []
    done = threading.Event()

    def reader():
        for line in proc.stdout:
            lines.append(line.rstrip("\n"))
            if "Done (" in line and "For help, type" in line:
                done.set()

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    while not done.is_set() and proc.poll() is None and time.time() - start < args.timeout:
        time.sleep(1)
    booted = done.is_set()
    if booted:
        log(f"Server reached Done after {time.time() - start:.0f}s; running checks and stopping")
        for command in args.command or []:
            proc.stdin.write(command + "\n")
            proc.stdin.flush()
            time.sleep(2)
        proc.stdin.write("stop\n")
        proc.stdin.flush()
    try:
        proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        proc.kill()
    t.join(timeout=10)
    log_path = BUILD / "server-boot.log"
    BUILD.mkdir(exist_ok=True)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    problems = []
    for ln in lines:
        if re.search(r"Unknown function|Unknown or incomplete command|Incorrect argument for command", ln):
            problems.append(f"console command failed: {ln}")
    if args.command and not any("Alola self-test" in ln for ln in lines):
        problems.append("the Alola self-test function did not run")
    ours = [ln for ln in lines if re.search(r"\balola[_:]", ln, re.I) and BAD_LOG.search(ln)]
    for ln in ours:
        problems.append(f"alola content: {ln}")
    errors = [ln for ln in lines if re.search(r"/(ERROR|FATAL)\]", ln)]
    log(f"\n--- {len(errors)} ERROR lines in server log (first 60) ---")
    for ln in errors[:60]:
        log(ln[:400])
    log("--- lines mentioning cobblemon/alola problems (first 60) ---")
    for ln in [ln for ln in lines if re.search(r"cobblemon|alola", ln, re.I) and BAD_LOG.search(ln)][:60]:
        log(ln[:400])
    if not booted:
        log("\n--- last 150 log lines ---")
        for ln in lines[-150:]:
            log(ln[:500])
        crash = sorted((target / "crash-reports").glob("*.txt")) if (target / "crash-reports").exists() else []
        if crash:
            log(f"\n--- {crash[-1].name} (first 120 lines) ---")
            log("\n".join(crash[-1].read_text(errors="replace").splitlines()[:120]))
        problems.append("server did not finish starting")
    for p in problems:
        log(f"BOOT-ERROR: {p[:500]}")
    if args.dump:
        for pattern in args.dump:
            for path in sorted(target.glob(pattern)):
                if path.is_file() and path.stat().st_size < 60_000:
                    log(f"\n===== {path.relative_to(target)} =====")
                    log(path.read_text(errors="replace"))
    log(f"\nBoot {'OK' if not problems else 'FAILED'} in {time.time() - start:.0f}s")
    return 1 if problems else 0


# --------------------------------------------------------------------- inspect

def cmd_inspect(args) -> int:
    lock = read_lock()
    rx = re.compile(args.pattern)
    for f in lock["files"]:
        if f["slug"] != args.slug:
            continue
        path = download(f["url"], f["sha1"], f["filename"])
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if rx.search(n)]
        log(f"{f['slug']} {f['version_number']}: {len(names)} matches for {args.pattern}")
        for n in names[: args.limit]:
            log(f"  {n}")
        return 0
    log(f"{args.slug} is not in the lockfile")
    return 1


# -------------------------------------------------------------------- versions

def cmd_versions(args) -> int:
    pack, _ = load_modlist()
    for slug in args.slugs:
        try:
            versions = api(f"/project/{slug}/version", loaders=["fabric"],
                           game_versions=pack.get("game_versions", [pack["minecraft"]]))
        except urllib.error.HTTPError as e:
            log(f"{slug}: HTTP {e.code}")
            continue
        versions.sort(key=lambda v: v["date_published"], reverse=True)
        log(f"== {slug}: {len(versions)} fabric versions")
        for v in versions[: args.limit]:
            f = Resolver.primary_file(v)
            log(f"  {v['date_published'][:10]} {v['version_type']:<7} {v['version_number']:<40} {f['filename']}")
    return 0


# ------------------------------------------------------------------------ main

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve")
    r.add_argument("--upgrade", action="store_true", help="re-resolve every mod instead of keeping locked versions")
    r.add_argument("--keep-going", action="store_true", help="exit 0 even if some mods could not be resolved")
    sub.add_parser("validate")
    bd = sub.add_parser("build")
    bd.add_argument("--publish", action="store_true", help="also copy the .mrpack to the repository root")
    sub.add_parser("docs")
    s = sub.add_parser("server")
    s.add_argument("--dir", default="build/server")
    s.add_argument("--accept-eula", action="store_true", help="write eula.txt (you must agree to the Minecraft EULA)")
    c = sub.add_parser("client")
    c.add_argument("--dir", default="build/client")
    c.add_argument("--skip", action="append", help="regex of slugs to leave out")
    b = sub.add_parser("boot")
    b.add_argument("--dir", default="build/server")
    b.add_argument("--memory", default="6G")
    b.add_argument("--timeout", type=int, default=900)
    b.add_argument("--command", action="append", help="console command to run once the server is up")
    b.add_argument("--dump", action="append", help="glob of generated files to print after boot")
    v = sub.add_parser("versions", help="list a project's Fabric versions (diagnostics)")
    v.add_argument("slugs", nargs="+")
    v.add_argument("--limit", type=int, default=12)
    i = sub.add_parser("inspect")
    i.add_argument("slug")
    i.add_argument("pattern")
    i.add_argument("--limit", type=int, default=200)
    args = p.parse_args()
    return {"resolve": cmd_resolve, "validate": cmd_validate, "build": cmd_build, "docs": cmd_docs,
            "server": cmd_server, "client": cmd_client, "boot": cmd_boot, "inspect": cmd_inspect,
            "versions": cmd_versions}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
