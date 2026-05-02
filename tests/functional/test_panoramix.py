#!/usr/bin/env python3

import re
import os
import sys
import subprocess

BIN = os.environ.get("PANORAMIX_BIN", "./panoramix")
TIMEOUT = 10
_passed = 0
_failed = 0
_failures = []

GRN = "\033[92m"
RED = "\033[91m"
CYN = "\033[96m"
RST = "\033[0m"
BLD = "\033[1m"


def run(*args):
    try:
        r = subprocess.run(
            [BIN] + [str(a) for a in args],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        return r.returncode, r.stdout.splitlines(), r.stderr
    except subprocess.TimeoutExpired:
        return -1, [], "TIMEOUT"


def ok(name):
    global _passed
    _passed += 1
    print(f"  {GRN}✓{RST} {name}")


def fail(name, detail=""):
    global _failed
    _failed += 1
    _failures.append((name, detail))
    print(f"  {RED}✗{RST} {name}" + (f"  [{detail}]" if detail else ""))


def chk(name, condition, detail=""):
    if condition:
        ok(name)
    else:
        fail(name, detail)


def section(title):
    print(f"\n{CYN}{BLD}── {title} ──{RST}")


USAGE_RE = re.compile(
    r"USAGE: \S+ <nb_villagers> <pot_size> <nb_fights> <nb_refills>"
)

section("1. Wrong argument count")

for n, args in [
    ("no args", []),
    ("1 arg", [1]),
    ("2 args", [1, 2]),
    ("3 args", [1, 2, 3]),
    ("5 args", [1, 2, 3, 4, 5]),
    ("6 args", [1, 2, 3, 4, 5, 6]),
]:
    code, lines, _ = run(*args)
    chk(f"exit 84 with {n}", code == 84, f"got {code}")
    chk(f"USAGE printed with {n}", any(USAGE_RE.search(l) for l in lines),
        str(lines[:2]))

section("2. Zero values exit")

for label, args in [
    ("villagers=0", [0, 5, 3, 1]),
    ("pot_size=0", [3, 0, 3, 1]),
    ("nb_fights=0", [3, 5, 0, 1]),
    ("nb_refills=0", [3, 5, 3, 0]),
]:
    code, lines, _ = run(*args)
    out = "\n".join(lines)
    chk(f"exit 84 with {label}", code == 84, f"got {code}")
    chk(f"Values msg with {label}", "Values must be >0." in out, out[:80])

section("3. Negative values")

for param_idx, label in [(0, "villagers"), (1, "pot_size"),
                          (2, "nb_fights"), (3, "nb_refills")]:
    for val in [-1, -100]:
        args = [3, 5, 3, 1]
        args[param_idx] = val
        code, lines, _ = run(*args)
        chk(f"exit 84 with {label}={val}", code == 84, f"got {code}")

section("4. Non-numeric args")

for param_idx, label in [(0, "villagers"), (1, "pot_size"),
                          (2, "nb_fights"), (3, "nb_refills")]:
    args = [3, 5, 3, 1]
    args[param_idx] = "abc"
    code, lines, _ = run(*args)
    chk(f"exit 84 with {label}=abc", code == 84, f"got {code}")


section("5. Valid params ")

for label, args in [
    ("minimal", [1, 1, 1, 1]),
    ("1v 5p 3f 1r", [1, 5, 3, 1]),
    ("3v 5p 3f 1r", [3, 5, 3, 1]),
    ("5v 10p 5f 2r", [5, 10, 5, 2]),
    ("2v 3p 2f 1r", [2, 3, 2, 1]),
    ("1v 3p 5f 3r", [1, 3, 5, 3]),
    ("10v 5p 1f 1r", [10, 5, 1, 1]),
    ("1v 1p 5f 5r", [1, 1, 5, 5]),
]:
    code, _, _ = run(*args)
    chk(f"exit 0 with {label}", code == 0, f"got {code}")

section("6. USAGE / error message format")

code, lines, _ = run()
chk("USAGE contains <nb_villagers>", any("<nb_villagers>" in l for l in lines))
chk("USAGE contains <pot_size>", any("<pot_size>" in l for l in lines))
chk("USAGE contains <nb_fights>", any("<nb_fights>" in l for l in lines))
chk("USAGE contains <nb_refills>", any("<nb_refills>" in l for l in lines))

code, lines, _ = run(-1, 5, 3, 1)
out = "\n".join(lines)
chk("Values msg exact text", "Values must be >0." in out, out[:80])
chk("Values msg only once", out.count("Values must be >0.") == 1,
    str(out.count("Values must be >0.")))

code, lines, _ = run()
chk("No Values msg for missing args",
    "Values must be >0." not in "\n".join(lines))

section("7. Druid start message")

DRUID_READY = "Druid: I'm ready... but sleepy..."

for label, args in [("1v", [1, 5, 3, 1]), ("3v", [3, 5, 3, 1])]:
    code, lines, _ = run(*args)
    chk(f"druid ready present ({label})",
        any(DRUID_READY == l for l in lines), str(lines[:3]))
    chk(f"druid ready exactly once ({label})",
        lines.count(DRUID_READY) == 1, str(lines.count(DRUID_READY)))

section("8. Villager start/finish counts")

for label, nv, args in [
    ("1v", 1, [1, 5, 3, 1]),
    ("3v", 3, [3, 5, 3, 1]),
    ("5v", 5, [5, 10, 5, 2]),
    ("2v", 2, [2, 3, 2, 1]),
]:
    code, lines, _ = run(*args)
    battles = sum(1 for l in lines if "Going into battle!" in l)
    sleeps = sum(1 for l in lines if "I'm going to sleep now." in l)
    chk(f"Going into battle count={nv} ({label})", battles == nv,
        f"got {battles}")
    chk(f"Going to sleep count={nv} ({label})", sleeps == nv,
        f"got {sleeps}")

section("9. valid Villager IDs")

for nv in [1, 3, 5]:
    args = [nv, 10, 2, 1]
    code, lines, _ = run(*args)
    battle_ids = set()
    for l in lines:
        m = re.match(r"Villager (\d+): Going into battle!", l)
        if m:
            battle_ids.add(int(m.group(1)))
    chk(f"IDs are {{0..{nv - 1}}} for nv={nv}",
        battle_ids == set(range(nv)), str(battle_ids))

section("10. Fight counts")

for label, nv, nf, args in [
    ("1v1f", 1, 1, [1, 5, 1, 1]),
    ("1v3f", 1, 3, [1, 5, 3, 1]),
    ("3v1f", 3, 1, [3, 10, 1, 1]),
    ("3v3f", 3, 3, [3, 20, 3, 1]),
    ("5v2f", 5, 2, [5, 20, 2, 1]),
]:
    code, lines, _ = run(*args)
    fights = sum(1 for l in lines if "Take that roman scum!" in l)
    chk(f"fights={nv * nf} for {label}", fights == nv * nf,
        f"got {fights}")

section("11. Fight counter values")

code, lines, _ = run(1, 10, 3, 1)
counters = [int(m.group(1)) for l in lines
            for m in [re.search(r"Only (\d+) left\.", l)] if m]
chk("fight counter starts at nb_fights-1 (=2)",
    max(counters, default=-1) == 2, str(counters))
chk("fight counter reaches 0",
    0 in counters, str(counters))
chk("fight counter has no negatives",
    all(c >= 0 for c in counters), str(counters))

code, lines, _ = run(1, 10, 5, 1)
counters5 = [int(m.group(1)) for l in lines
             for m in [re.search(r"Only (\d+) left\.", l)] if m]
chk("fight counter max=4 for nb_fights=5",
    max(counters5, default=-1) == 4, str(counters5))

section("12. Drink messages")

for label, nv, nf, args in [
    ("1v1f", 1, 1, [1, 10, 1, 1]),
    ("1v3f", 1, 3, [1, 10, 3, 1]),
    ("3v3f", 3, 3, [3, 20, 3, 1]),
]:
    code, lines, _ = run(*args)
    drinks = sum(1 for l in lines if "I need a drink" in l)
    chk(f"drinks >= fights ({nv * nf}) for {label}",
        drinks >= nv * nf, f"got {drinks}")

code, lines, _ = run(1, 10, 3, 1)
for l in lines:
    m = re.search(r"I see (\d+) servings left", l)
    if m:
        chk("serving count >= 0 in drink msg",
            int(m.group(1)) >= 0, m.group(1))
        break

section("13. Serving counts bounded by pot size")

code, lines, _ = run(1, 5, 3, 1)
for l in lines:
    m = re.search(r"I see (\d+) servings left", l)
    if m:
        chk("serving count <= pot_size (5)",
            int(m.group(1)) <= 5, m.group(1))

section("14. First drink sees pot_size servings")

code, lines, _ = run(1, 7, 3, 1)
first_drink = next(
    (l for l in lines if "I need a drink" in l), None
)
if first_drink:
    m = re.search(r"I see (\d+) servings left", first_drink)
    chk("first drink sees pot_size=7",
        m and int(m.group(1)) == 7, first_drink)
else:
    fail("first drink line found")

section("15.  Pano wake up")

code, lines, _ = run(1, 100, 1, 1)
chk("no Hey Pano when pot never empties",
    not any("Hey Pano" in l for l in lines), str(lines))

code, lines, _ = run(1, 1, 3, 3)
chk("Hey Pano present when pot empties",
    any("Hey Pano wake up!" in l for l in lines), str(lines[:5]))

code, lines, _ = run(3, 5, 3, 1)
hey_count = sum(1 for l in lines if "Hey Pano" in l)
chk("Hey Pano count >= 1 when refill needed", hey_count >= 1,
    f"got {hey_count}")

section("16. Druid refill message format")

REFILL_RE = re.compile(
    r"Druid: Ah! Yes, yes, I'm awake! Working on it!"
    r" Beware I can only make \d+ more refills after this one\."
)

code, lines, _ = run(1, 1, 3, 3)
chk("druid refill message format",
    any(REFILL_RE.match(l) for l in lines), str(lines))

code, lines, _ = run(1, 1, 2, 1)
refill_lines = [l for l in lines if "Beware I can only make" in l]
chk("last refill shows 0 more refills",
    any("make 0 more refills" in l for l in refill_lines),
    str(refill_lines))

code, lines, _ = run(1, 1, 4, 3)
refill_counters = [int(m.group(1)) for l in lines
                   for m in [re.search(r"make (\d+) more refills", l)] if m]
chk("refill counters decrement to 0",
    0 in refill_counters, str(refill_counters))

code, lines, _ = run(1, 1, 4, 3)
chk("3 refills  3 refill messages",
    sum(1 for l in lines if "I'm awake!" in l) == 3,
    str(sum(1 for l in lines if "I'm awake!" in l)))

section("17. Druid: I'm out of viscum.")

VISCUM = "Druid: I'm out of viscum. I'm going back to... zZz"

code, lines, _ = run(1, 1, 3, 2)
chk("viscum msg present when refills exhausted",
    any(VISCUM == l for l in lines), str(lines))
chk("viscum msg exactly once",
    lines.count(VISCUM) == 1, str(lines.count(VISCUM)))

code, lines, _ = run(1, 100, 1, 1)
chk("viscum msg absent when refill not needed",
    VISCUM not in lines, str(lines))


section("18. Per villager message ordering")

code, lines, _ = run(1, 10, 3, 1)
by_v = {}
for l in lines:
    m = re.match(r"Villager (\d+): (.+)", l)
    if m:
        vid = int(m.group(1))
        by_v.setdefault(vid, []).append(m.group(2))

for vid, msgs in by_v.items():
    chk(f"villager {vid}: battle first",
        msgs[0] == "Going into battle!", str(msgs[:3]))
    chk(f"villager {vid}: sleep last",
        msgs[-1] == "I'm going to sleep now.", str(msgs[-3:]))

section("19. No stderr output for valid params")

for label, args in [("minimal", [1, 1, 1, 1]), ("3v5p3f1r", [3, 5, 3, 1])]:
    code, lines, stderr = run(*args)
    chk(f"no stderr for {label}", stderr == "", repr(stderr[:80]))

section("20. All output lines match Villager or Druid prefix")

code, lines, _ = run(3, 5, 3, 1)
for l in lines:
    if l:
        chk(f"line starts with Villager or Druid",
            l.startswith("Villager ") or l.startswith("Druid: "),
            repr(l[:60]))
        break

code, lines, _ = run(1, 5, 3, 1)
chk("no empty lines in output",
    all(l.strip() for l in lines if l), str(lines))

section("21. Specific parameter combos")

code, lines, _ = run(1, 1, 1, 1)
chk("1v1p1f1r: only 0 'Only X left.' = 0",
    any("Only 0 left." in l for l in lines))

code, lines, _ = run(2, 5, 2, 1)
fights = sum(1 for l in lines if "Take that roman scum!" in l)
chk("2v5p2f1r: 4 fights total", fights == 4, f"got {fights}")

code, lines, _ = run(1, 3, 3, 1)
chk("1v3p3f1r: no refill (exact fit)",
    not any("Hey Pano" in l for l in lines))

code, lines, _ = run(1, 3, 4, 1)
chk("1v3p4f1r: refill needed",
    any("Hey Pano" in l for l in lines))

code, lines, _ = run(1, 5, 5, 5)
chk("1v5p5f5r: no refill needed", not any("Hey Pano" in l for l in lines))

code, lines, _ = run(1, 4, 5, 5)
chk("1v4p5f5r: exactly 1 refill",
    sum(1 for l in lines if "I'm awake!" in l) == 1,
    str(sum(1 for l in lines if "I'm awake!" in l)))

code, lines, _ = run(1, 1, 6, 5)
chk("1v1p6f5r: 5 refills all used",
    sum(1 for l in lines if "I'm awake!" in l) == 5,
    str(sum(1 for l in lines if "I'm awake!" in l)))

section("22. Speedtest")

for label, args in [
    ("1v1p1f1r", [1, 1, 1, 1]),
    ("10v10p10f5r", [10, 10, 10, 5]),
]:
    code, _, _ = run(*args)
    chk(f"terminates in {TIMEOUT}s: {label}", code != -1, "TIMEOUT")

total = _passed + _failed
print(f"\n{BLD}{'=' * 55}{RST}")
print(f"{BLD}Results: {_passed}/{total} passed{RST}")
if _failures:
    print(f"{RED}{_failed} FAILED:{RST}")
    for name, detail in _failures:
        print(f"  - {name}" + (f"  [{detail}]" if detail else ""))
else:
    print(f"{GRN}All tests passed!{RST}")
sys.exit(0 if _failed == 0 else 1)
