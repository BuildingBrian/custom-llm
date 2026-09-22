"""Generate synthetic teaching files for Experiment 2 (corpus extension).

Targets three extension-eval categories: opposites, categories_and_analogies, negation.
Design rules (see README, "Leakage policy"):
  * No sentence may contain any of the 48 eval prompts (checked with run_evals.matching_cases,
    the same normalized substring test the notebook applies to every passage).
  * No "paired reference answer": the exact eval frame is never combined with an eval answer.
    Eval word associations (hot/cold, salmon/fish, ...) are taught only through *other* frames.
  * The eval correction pairs (red->blue, open->closed, tea->milk) and the eval story subjects
    (box, door, ava-buys) never appear together, so negation is a transfer test, not recall.
  * Multi-sentence stories are written as "red .it is" (period attached to the next word) so the
    notebook's chunker keeps the story in ONE passage; word_tokens() normalizes this to " . ".
Deterministic: same seed -> same files.
"""
import random, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run_evals import load_suite, matching_cases, word_tokens  # noqa: E402

SUITE = load_suite(str(ROOT / "evals" / "language_evals.json"))
OUT = ROOT / "corpus"
rng = random.Random(2026)

def an(word):
    return ("an " if word[0] in "aeiou" else "a ") + word

# ---------------------------------------------------------------- opposites
PAIRS = [("hot","cold"),("empty","full"),("noisy","quiet"),("loud","quiet"),("fast","slow"),
         ("warm","cool"),("heavy","light"),("early","late"),("soft","hard"),("round","flat"),
         ("big","small"),("tall","short"),("wet","dry"),("up","down"),("happy","sad"),
         ("clean","dirty"),("dark","bright"),("rich","poor"),("young","old"),("strong","weak"),
         ("thick","thin"),("wide","narrow"),("sweet","sour"),("high","low"),("near","far"),
         ("cheap","expensive"),("open","closed")]
EVAL_OPPOSITE_X = {"hot", "empty", "noisy"}          # eval frame "the opposite of X is" never uses these X
NOUNS = ["water","soup","room","street","road","box","cup","glass","bag","song","voice","coat",
         "river","hill","tea","milk","bread","cake","wall","floor","train","bus","store","school"]
COUNTABLE = ["room","street","road","box","cup","glass","bag","song","voice","coat","river","hill",
             "cake","wall","floor","train","bus","store","school"]

def opposites():
    out = set()
    for x, y in PAIRS:
        for a, b in ((x, y), (y, x)):
            if a not in EVAL_OPPOSITE_X:
                out.add(f"the opposite of {a} is {b} .")
            out.add(f"{a} is the opposite of {b} .")
            out.add(f"{a} and {b} are opposites .")
            out.add(f"if something is not {a} , it is {b} .")
            out.add(f"{a} means the opposite of {b} .")
            out.add(f"something {a} is never {b} .")
            for n in rng.sample(NOUNS, 4):
                out.add(f"the {n} is {a} , not {b} .")
            for n in rng.sample(COUNTABLE, 3):
                out.add(f"{an(a)} {n} is the opposite of {an(b)} {n} .")
    return sorted(out)

# ------------------------------------------------------ categories & analogies
CATEGORIES = {
    "bird": ["robin","sparrow","crow","eagle","owl","duck","hen","parrot"],
    "fish": ["salmon","trout","shark","tuna","cod","goldfish"],
    "dog": ["beagle","poodle","husky","collie"],
    "cat": ["tabby","siamese","lion","tiger"],
    "flower": ["rose","tulip","daisy","lily"],
    "tree": ["oak","pine","maple","palm"],
    "tool": ["hammer","saw","drill","wrench"],
    "vehicle": ["truck","bus","car","taxi","bicycle","train"],
    "metal": ["iron","gold","silver","copper"],
    "fabric": ["cotton","wool","silk","linen"],
    "vegetable": ["carrot","onion","potato","cabbage","bean"],
    "fruit": ["apple","banana","orange","pear","peach","mango","plum","grape"],
}
EVAL_ISA = {("robin","bird"),("salmon","fish"),("carrot","vegetable"),("apple","fruit")}
GROWS = [("puppy","dog"),("kitten","cat"),("calf","cow"),("lamb","sheep"),("chick","hen"),
         ("foal","horse"),("kid","goat"),("duckling","duck"),("cub","bear"),("tadpole","frog"),
         ("piglet","pig")]
EVAL_GROWS = {("puppy","dog"),("kitten","cat")}

def categories():
    out = set()
    isa_pairs = [(m, c) for c, ms in CATEGORIES.items() for m in ms]
    for m, c in isa_pairs:
        if (m, c) not in EVAL_ISA:
            out.add(f"{an(m)} is {an(c)} .")
            out.add(f"every {m} is {an(c)} .")
        out.add(f"the {m} is a kind of {c} .")
        out.add(f"we saw {an(m)} , which is a type of {c} .")
        out.add(f"the {m} belongs with the other {c} kinds .")
        others = [o for o in CATEGORIES[c] if o != m]
        for o in rng.sample(others, min(2, len(others))):
            out.add(f"the {m} and the {o} are two kinds of {c} .")
    # two-sentence analogies, non-eval pairs only, kept in one passage
    safe = [p for p in isa_pairs if p not in EVAL_ISA]
    for _ in range(140):
        (m1, c1), (m2, c2) = rng.sample(safe, 2)
        if c1 != c2:
            out.add(f"{an(m1)} is {an(c1)} .{an(m2)} is {an(c2)} .")
    for y, a in GROWS:
        if (y, a) not in EVAL_GROWS:
            out.add(f"{an(y)} grows into {an(a)} .")
            out.add(f"every {y} grows into {an(a)} .")
        out.add(f"a young {a} is called {an(y)} .")
        out.add(f"the {y} will become {an(a)} one day .")
        out.add(f"the {y} played next to the older {a} .")
        out.add(f"first it is {an(y)} , later it is {an(a)} .")
    safe_g = [p for p in GROWS if p not in EVAL_GROWS]
    for _ in range(60):
        (y1, a1), (y2, a2) = rng.sample(safe_g, 2)
        out.add(f"{an(y1)} grows into {an(a1)} .{an(y2)} grows into {an(a2)} .")
    return sorted(out)

# ------------------------------------------------------------------ negation
OBJECTS = ["cup","hat","car","bag","shirt","wall","ball","book","chair","table","flag","coat",
           "sock","lamp","box","door","window","gate","bottle","plate","key","pen"]
COLORS = ["red","blue","green","yellow","black","white","brown","pink","grey"]
STATES = [("open","closed"),("big","small"),("hot","cold"),("wet","dry"),("clean","dirty"),
          ("full","empty"),("wide","narrow"),("here","missing"),("new","old"),("soft","hard")]
FORBID_PAIRS = {("red","blue"),("open","closed"),("tea","milk")}   # eval correction pairs, never taught
FORBID_SUBJECT = {"box": {"red","blue"}, "door": {"open","closed"}}  # eval story subjects
NAMES = [("ava","she"),("ben","he"),("cara","she"),("dan","he"),("eli","he"),("fay","she"),
         ("gus","he"),("hana","she"),("ivan","he"),("jade","she"),("kai","he"),("lena","she"),
         ("mia","she"),("theo","he")]
VERBS = [("buy","bought"),("want","wanted"),("pick","picked"),("take","took"),("choose","chose"),
         ("order","ordered"),("eat","ate"),("drink","drank")]
DRINKS = ["tea","milk","coffee","water","juice"]
FOODS = ["rice","bread","soup","cake","jam","honey","cheese","butter","fish","meat","salad","pasta"]
ITEMS = DRINKS + FOODS

def negation():
    out = set()
    props = [(c1, c2) for c1 in COLORS for c2 in COLORS if c1 != c2] \
            + [p for s in STATES for p in (s, s[::-1])]
    props = [p for p in props if p not in FORBID_PAIRS]
    while len(out) < 330:
        obj = rng.choice(OBJECTS); a, b = rng.choice(props)
        if obj in FORBID_SUBJECT and (a in FORBID_SUBJECT[obj] or b in FORBID_SUBJECT[obj]):
            continue
        form = rng.randrange(4)
        if form == 0:   out.add(f"the {obj} is not {a} .it is {b} .the {obj} is {b} .")
        elif form == 1: out.add(f"the {obj} is not {a} .it is {b} .so the {obj} is {b} .")
        elif form == 2: out.add(f"the {obj} is not {a} .it is {b} .")
        else:           out.add(f"the {obj} is {b} , not {a} .")
    pairs = [(i, j) for i in ITEMS for j in ITEMS if i != j and (i, j) not in FORBID_PAIRS]
    while len(out) < 620:
        name, pron = rng.choice(NAMES); v, vp = rng.choice(VERBS); i, j = rng.choice(pairs)
        if name == "ava" and (v == "buy" or "tea" in (i, j) or "milk" in (i, j)):
            continue
        if v == "eat" and (i in DRINKS or j in DRINKS):
            continue
        if v == "drink" and (i in FOODS or j in FOODS):
            continue
        form = rng.randrange(3)
        if form == 0:   out.add(f"{name} did not {v} {i} .{pron} {vp} {j} .{name} {vp} {j} .")
        elif form == 1: out.add(f"{name} did not {v} the {i} .{pron} {vp} the {j} .{name} {vp} the {j} .")
        else:           out.add(f"{name} did not {v} {i} .{pron} {vp} {j} .")
    return sorted(out)

# --------------------------------------------------------------- write+check
def chunks_like_notebook(text, max_tokens=47):
    out = []
    for unit in re.split(r"(?<=[.!?])\s+|\n+", text):
        toks = word_tokens(unit)
        out.extend(" ".join(toks[i:i+max_tokens]) for i in range(0, len(toks), max_tokens))
    return [c for c in out if c]

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    files = {"opposites.txt": opposites(), "categories_and_analogies.txt": categories(), "negation.txt": negation()}
    all_tokens = set()
    for name, lines in files.items():
        text = "\n".join(lines) + "\n"
        leaks = [(c, matching_cases(c, SUITE)) for c in chunks_like_notebook(text)]
        leaks = [l for l in leaks if l[1]]
        assert not leaks, f"eval leakage in {name}: {leaks[:3]}"
        (OUT / name).write_text(text, encoding="utf-8")
        toks = {t for c in chunks_like_notebook(text) for t in c.split()}
        all_tokens |= toks
        print(f"{name}: {len(lines)} lines, {len(chunks_like_notebook(text))} passages, {len(toks)} distinct tokens")
    print("distinct tokens across teaching files:", len(all_tokens))
