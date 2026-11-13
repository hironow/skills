"""正解表から 16 問を乱数で選ぶ。使い方: python3 -I sample.py"""
import collections
import pathlib
import random

HERE = pathlib.Path(__file__).parent
SEED = 20261112
PER_VERDICT = 8
MAX_PER_PROPERTY = 4

rows = [line.split("\t") for line in (HERE / "truth.tsv").read_text().splitlines()[1:]]
by_prop = collections.defaultdict(list)
for variant, prop, verdict, _ in rows:
    by_prop[prop].append(verdict)
eligible = {p for p, vs in by_prop.items()
            if min(vs.count("holds"), vs.count("violated")) >= 0.2 * len(vs)}

rng = random.Random(SEED)
pool = [(v, p, verdict) for v, p, verdict, _ in rows if p in eligible]
rng.shuffle(pool)
picked, per_prop, per_verdict = [], collections.Counter(), collections.Counter()
for v, p, verdict in pool:
    if per_verdict[verdict] < PER_VERDICT and per_prop[p] < MAX_PER_PROPERTY:
        picked.append((v, p, verdict))
        per_prop[p] += 1
        per_verdict[verdict] += 1
rng.shuffle(picked)

lines = ["item\tvariant\tproperty\ttruth"]
lines += [f"{i:02d}\t{v}\t{p}\t{t}" for i, (v, p, t) in enumerate(picked, 1)]
(HERE / "items.tsv").write_text("\n".join(lines) + "\n")
print("eligible:", sorted(eligible))
print("\n".join(lines))
