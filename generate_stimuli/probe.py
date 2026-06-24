import argparse
import csv
import random
from pathlib import Path

import generator as gen
import french_lexicon as lex_fr
import english_lexicon as lex_en
from generator import generate_stimuli


# simple verb-replacement mapping (French examples from your request)
FRENCH_VERB_REPLACEMENTS = {
    "lit un livre": "écrit un livre",
    "apprend une leçon": "donne une leçon",
    "est fatiguée": "est en forme",
    "est fatigué": "est en forme",
    "sont fatigués": "sont en forme",
    "sont fatiguées": "sont en forme",
    "est en retard": "est en avance",
    "sont en retard": "sont en avance",
}

# English fallback replacements (small / optional)
ENGLISH_VERB_REPLACEMENTS = {
    "reads a book": "writes a book",
    "learns a lesson": "gives a lesson",
    "is tired": "is energetic",
    "are tired": "are energetic",
}


def _pick_wrong_prep(correct_label, lexicon):
    labels = [p["label"] for p in lexicon.PREPOSITIONS]
    choices = [l for l in labels if l != correct_label]
    return random.choice(choices) if choices else correct_label


def _build_pp_text(prep_label, lemma):
    # simple reconstruction: "prep_label lemma"
    return f"{prep_label} {lemma}"


def generate_probes_for_stimulus(stim, lexicon, language="french", rng=None):
    if rng is None:
        rng = random.Random()
    probes = []
    sid = stim.get("Stimulus_Code", "")
    # True probes (easy):
    # q1: subject - PP1 (use existing scene_probe_1 if present)
    q1_true = stim.get("scene_probe_1") or gen._scene_probe_for_pp(
        stim.get("Subject_Lemma", ""),
        stim.get("Subject_Number", "").lower(),
        _build_pp_text(stim.get("PP1_Preposition", ""), stim.get("PP1_Lemma", "")),
        language=language,
    )
    # q2: subject - PP2
    q2_true = stim.get("scene_probe_2") or gen._scene_probe_for_pp(
        stim.get("Subject_Lemma", ""),
        stim.get("Subject_Number", "").lower(),
        _build_pp_text(stim.get("PP2_Preposition", ""), stim.get("PP2_Lemma", "")),
        language=language,
    )
    # q3: PP1 - PP2 (treat PP1 as subject)
    q3_true = gen._scene_probe_for_pp(
        stim.get("PP1_Lemma", ""),
        stim.get("PP1_Number", "").lower(),
        _build_pp_text(stim.get("PP2_Preposition", ""), stim.get("PP2_Lemma", "")),
        language=language,
    )
    # q4: subject-verb (use existing subject_probe if present)
    q4_true = stim.get("subject_probe") or gen._subject_probe_from_row(
        {
            "subject": stim.get("Subject_Lemma", ""),
            "subject_number": stim.get("Subject_Number", "").lower(),
            "verb_phrase": stim.get("Verb_Phrase", ""),
        },
        language=language,
    )

    true_list = [
        ("scene", "subject_pp1", "easy", q1_true),
        ("scene", "subject_pp2", "easy", q2_true),
        ("scene", "pp1_pp2", "easy", q3_true),
        ("sv", "subject_verb", "easy", q4_true),
    ]

    # False probes: wrong prepositions for scene, wrong verb for subject-verb
    # sample wrong preposition from lexicon
    wrong_p1 = _pick_wrong_prep(stim.get("PP1_Preposition", ""), lexicon)
    wrong_p2 = _pick_wrong_prep(stim.get("PP2_Preposition", ""), lexicon)
    # For simplicity, use the same wrong preposition for PP1-PP2 probe (or sample another)
    wrong_p3 = _pick_wrong_prep(stim.get("PP2_Preposition", ""), lexicon)

    q1_false = gen._scene_probe_for_pp(
        stim.get("Subject_Lemma", ""),
        stim.get("Subject_Number", "").lower(),
        _build_pp_text(wrong_p1, stim.get("PP1_Lemma", "")),
        language=language,
    )
    q2_false = gen._scene_probe_for_pp(
        stim.get("Subject_Lemma", ""),
        stim.get("Subject_Number", "").lower(),
        _build_pp_text(wrong_p2, stim.get("PP2_Lemma", "")),
        language=language,
    )
    q3_false = gen._scene_probe_for_pp(
        stim.get("PP1_Lemma", ""),
        stim.get("PP1_Number", "").lower(),
        _build_pp_text(wrong_p3, stim.get("PP2_Lemma", "")),
        language=language,
    )

    # verb false: apply mapping (prefer language-specific map), fallback to simple replacement
    vp = stim.get("Verb_Phrase", "")
    if language and language.lower().startswith("fr"):
        replace_map = FRENCH_VERB_REPLACEMENTS
        aux_true = "Est-ce que"
    else:
        replace_map = ENGLISH_VERB_REPLACEMENTS
        aux_true = "Is"

    vp_false = replace_map.get(vp, None)
    if vp_false is None:
        # fallback: pick a different verb phrase by simple negation or append "not"
        if language and language.lower().startswith("fr"):
            vp_false = "ne " + vp  # naive, may be ungrammatical
        else:
            vp_false = "does not " + vp

    # build a simple subject-verb question for the false verb
    subj_display = stim.get("Subject_Lemma", "")
    if language and language.lower().startswith("fr"):
        q4_false = f"{aux_true} {subj_display} {vp_false} ?"
    else:
        q4_false = f"{aux_true} {subj_display} {vp_false}?"

    false_list = [
        ("scene", "subject_pp1_wrong_prep", "easy", q1_false),
        ("scene", "subject_pp2_wrong_prep", "easy", q2_false),
        ("scene", "pp1_pp2_wrong_prep", "easy", q3_false),
        ("sv", "subject_verb_wrong", "easy", q4_false),
    ]

    pid_base = stim.get("Stimulus_Code", "") or ""
    pid_counter = 0
    for ptype, variant, diff, q in true_list:
        pid_counter += 1
        probes.append(
            {
                "Stimulus_Code": sid,
                "Probe_ID": f"{pid_base}_T{pid_counter}",
                "Probe_Type": ptype,
                "Variant": variant,
                "Difficulty": diff,
                "Probe_String": q,
                "Is_True": "true",
            }
        )
    for ptype, variant, diff, q in false_list:
        pid_counter += 1
        probes.append(
            {
                "Stimulus_Code": sid,
                "Probe_ID": f"{pid_base}_F{pid_counter}",
                "Probe_Type": ptype,
                "Variant": variant,
                "Difficulty": diff,
                "Probe_String": q,
                "Is_True": "false",
            }
        )

    return probes


def generate_probes_for_all(stimuli, language="french", rng=None):
    lexicon = lex_fr if language and language.lower().startswith("fr") else lex_en
    all_probes = []
    for stim in stimuli:
        all_probes.extend(generate_probes_for_stimulus(stim, lexicon, language=language, rng=rng))
    return all_probes


def write_probes(probes, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not probes:
        return
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(probes[0].keys()))
        writer.writeheader()
        writer.writerows(probes)


def read_stimuli_csv(path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return [r for r in reader]

def augment_stimuli_csv(input_path, output_path=None, language="french", seed=13):
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path
    else:
        output_path = Path(output_path)

    # read existing stimuli CSV
    with input_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [r for r in reader]
        base_fieldnames = reader.fieldnames or []

    lexicon = lex_fr if language and language.lower().startswith("fr") else lex_en
    rng = random.Random(seed)

    # ensure deterministic per-run sampling if desired
    augmented_rows = []
    for r in rows:
        probes = generate_probes_for_stimulus(r, lexicon, language=language, rng=rng)

        # collect true/false probe strings (preserve order)
        true_qs = [p["Probe_String"] for p in probes if p.get("Is_True", "").lower() == "true"][:4]
        false_qs = [p["Probe_String"] for p in probes if p.get("Is_True", "").lower() == "false"][:4]

        # pad if fewer than 4
        while len(true_qs) < 4:
            true_qs.append("")
        while len(false_qs) < 4:
            false_qs.append("")

        # add columns
        for i, q in enumerate(true_qs, start=1):
            r[f"Probe{i}_True"] = q
        for i, q in enumerate(false_qs, start=1):
            r[f"Probe{i}_False"] = q

        augmented_rows.append(r)

    # build header preserving original ordering, appending new probe columns
    new_cols = [f"Probe{i}_True" for i in range(1, 5)] + [f"Probe{i}_False" for i in range(1, 5)]
    out_fieldnames = list(dict.fromkeys((base_fieldnames or []) + new_cols))

    # write augmented CSV (overwrites if same path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(augmented_rows)

    return str(output_path)

# update main to accept --augment flag
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--language", required=False, default="french")
    ap.add_argument("--input", required=False, help="Input stimuli CSV (if omitted, generate fresh stimuli)")
    ap.add_argument("--output", required=False, help="Output probes CSV or augmented stimuli CSV path")
    ap.add_argument("--augment", action="store_true", help="Augment input CSV in-place (or to --output) with probe columns")
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    if args.input and args.augment:
        out = args.output or args.input
        augment_stimuli_csv(args.input, out, language=args.language, seed=args.seed)
        print(f"Augmented stimuli written to: {out}")
        return

    if args.input:
        stimuli = read_stimuli_csv(args.input)
    else:
        stimuli = generate_stimuli(seed=args.seed, language=args.language)

    # previous behaviour: generate and write probes-only CSV if output provided
    probes = generate_probes_for_all(stimuli, language=args.language, rng=random.Random(args.seed))
    if args.output:
        write_probes(probes, args.output)
        print(f"Probes written to: {args.output}")
    else:
        print("No --output given: probes generated but not written.")

if __name__ == "__main__":
    main()