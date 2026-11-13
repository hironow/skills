"""正解表から 24 問を乱数で選ぶ。使い方: python3 -I sample.py"""
import collections
import pathlib
import random

HERE = pathlib.Path(__file__).parent
SEED = 20261112
PER_GROUP = 6
MAX_PER_PROPERTY = 9
LIMITS = [(1, 2), (0, 3), (1, 3), (0, 2), (0, 1), (0, 1)]  # TTL EXT LAT MAINT FREEZE REACQUIRE

rows = [l.split("\t") for l in (HERE / "truth.tsv").read_text().splitlines()[1:]]
truth = {(v, p): verdict for v, p, verdict, _, _ in rows}
extra = {(v, p): (steps, states) for v, p, _, steps, states in rows}


def neighbors(tag):
    digits = [int(ch) for ch in tag]
    for i, (lo, hi) in enumerate(LIMITS):
        for d in (-1, 1):
            x = digits[i] + d
            if lo <= x <= hi:
                yield "".join(map(str, digits[:i] + [x] + digits[i + 1:]))


def near(tag, prop):
    return any(truth[(n, prop)] != truth[(tag, prop)] for n in neighbors(tag))


by_prop = collections.defaultdict(list)
for (v, p), verdict in truth.items():
    by_prop[p].append(verdict)
eligible = {p for p, vs in by_prop.items()
            if min(vs.count("holds"), vs.count("violated")) >= 0.1 * len(vs)}

rng = random.Random(SEED)
pool = sorted((v, p) for (v, p) in truth if p in eligible)
rng.shuffle(pool)
picked, per_prop, per_group = [], collections.Counter(), collections.Counter()
for v, p in pool:
    group = (truth[(v, p)], "near" if near(v, p) else "far")
    if per_group[group] < PER_GROUP and per_prop[p] < MAX_PER_PROPERTY:
        picked.append((v, p, group))
        per_prop[p] += 1
        per_group[group] += 1
rng.shuffle(picked)

lines = ["item\tvariant\tproperty\ttruth\tboundary\tcounterexample_steps\tdistinct_states"]
for i, (v, p, (verdict, dist)) in enumerate(picked, 1):
    steps, states = extra[(v, p)]
    lines.append(f"{i:02d}\t{v}\t{p}\t{verdict}\t{dist}\t{steps}\t{states}")
(HERE / "items.tsv").write_text("\n".join(lines) + "\n")
print("eligible:", sorted(eligible), "groups:", dict(per_group))
print("\n".join(lines))
