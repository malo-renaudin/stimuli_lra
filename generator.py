import csv
import random

import french_lexicon as lexicon_fr
import english_lexicon as lexicon_en
from pathlib import Path
from wordfreq import zipf_frequency


def _lower_initial(text):
    return text[:1].lower() + text[1:]


def _render(structure, row):
    # short: PP1, PP2, subject VP
    if structure == "short":
        return f"{row['pp1'].capitalize()}, {row['pp2']}, {_lower_initial(row['subject'])} {row['verb_phrase']}."
    # medium: PP1, subject PP2 VP
    if structure == "medium":
        return f"{row['pp1'].capitalize()}, {_lower_initial(row['subject'])} {row['pp2']}, {row['verb_phrase']}."
    # long: subject PP1, PP2 VP
    return f"{row['subject']} {row['pp1']}, {row['pp2']}, {row['verb_phrase']}."


def _vp_form(row, grammaticality):
    vp = row["verb_phrase"]
    if grammaticality == "grammatical":
        return vp
    explicit_violation = row.get("verb_phrase_violation")
    if explicit_violation:
        return explicit_violation
    raise RuntimeError(
        "Missing 'verb_phrase_violation' in lexicon row for ungrammatical stimulus generation."
    )


def _verb_head(verb_phrase):
    return verb_phrase.split(maxsplit=1)[0]


def _zipf_fr(text):
    return round(zipf_frequency(text.lower(), "fr"), 3)


def _letter_count(text):
    return sum(1 for char in text if char.isalpha())


def _noun_congruency(subject_number, pp1_number, pp2_number):
    number_code = {"singular": "S", "plural": "P"}
    try:
        return (
            f"{number_code[subject_number]}"
            f"{number_code[pp1_number]}"
            f"{number_code[pp2_number]}"
        )
    except KeyError as exc:
        raise RuntimeError(f"Unexpected number label in row: {exc.args[0]}") from exc


def _congruency_locus(structure, subject_number, pp1_number, pp2_number):
    if structure == "medium":
        pre_subject = "C" if pp1_number == subject_number else "I"
        between_subject_verb = "C" if pp2_number == subject_number else "I"
        return f"pre{pre_subject}_between{between_subject_verb}"
    if structure == "long":
        return "auto_long"
    return "auto_short"



def _split_det_subject(display, language="english"):
    d = display or ""
    if language == "english":
        if d.lower().startswith("the "):
            return ("the ", d[len("The "):])
        return ("", d)
    # french
    for prefix in ("L'", "Le ", "La ", "Les "):
        if d.startswith(prefix):
            return (prefix, d[len(prefix):])
    return ("", d)


def _scene_probe_for_pp(subject_display, subject_number, pp_text, language="english"):
    det, subj = _split_det_subject(subject_display, language=language)
    if language == "english":
        aux = "Is" if subject_number == "singular" else "Are"
        return f"{aux} {det}{subj} {pp_text}?"
    # french template: Est-ce que {det}{subject} est {PP} ?
    aux = "Est-ce que"
    return f"{aux} {det}{subj} est {pp_text} ?"


def _subject_probe_from_row(row, language="english"):
    display = row.get("subject") or row.get("subject_noun")
    det, subj = _split_det_subject(display, language=language)
    if language == "english":
        aux = "Is" if row["subject_number"] == "singular" else "Are"
        vp = row["verb_phrase"]
        # copula case: don't repeat copula
        if vp.startswith("is ") or vp.startswith("are "):
            rest = vp.split(" ", 1)[1] if " " in vp else ""
            return f"{aux} {det}{subj} {rest}?"
        # non-copula: form present participle (simple rule: remove trailing 's' then add 'ing')
        verb_head = _verb_head(vp)
        rest = vp.split(" ", 1)[1] if " " in vp else ""
        base = verb_head[:-1] if verb_head.endswith("s") else verb_head
        verb_ing = base + "ing"
        return f"{aux} {det}{subj} {verb_ing}{(' ' + rest) if rest else ''}?"
    # french: use existing VP directly
    aux = "Est-ce que"
    vp = row["verb_phrase"]
    return f"{aux} {det}{subj} {vp} ?"


def generate_stimuli(seed=13, total_prep_words=5, structures=("short", "medium", "long"), include_vp_violations=True, language="english"):
    rng = random.Random(seed)
    # pick lexicon based on language
    build_lexicon = lexicon_en.build_lexicon if language and language.lower().startswith("en") else lexicon_fr.build_lexicon
    base_rows = build_lexicon(total_prep_words)
    rng.shuffle(base_rows)
    grammaticalities = ("grammatical", "violation") if include_vp_violations else ("grammatical",)
    stimuli = []
    for index, row in enumerate(base_rows, start=1):
        for grammaticality in grammaticalities:
            vp = _vp_form(row, grammaticality)
            verb_head = _verb_head(vp)
            sentence_row = dict(row)
            sentence_row["verb_phrase"] = vp
            for pp_order in ("normal", "swapped"):
                # choose which pp becomes PP1 / PP2 in the output
                if pp_order == "normal":
                    p1_pref, p2_pref = "pp1", "pp2"
                else:
                    p1_pref, p2_pref = "pp2", "pp1"

                for structure in structures:
                    sentence_row2 = dict(sentence_row)
                    sentence_row2["pp1"] = row[p1_pref]
                    sentence_row2["pp2"] = row[p2_pref]
                    # build probes: scene probe uses the PP strings; subject probe uses subject noun
                    pp1_text = row[f"{p1_pref}"]
                    pp2_text = row[f"{p2_pref}"]
                    scene_q1 = _scene_probe_for_pp(row.get("subject"), row.get("subject_number"), pp1_text, language=language)
                    scene_q2 = _scene_probe_for_pp(row.get("subject"), row.get("subject_number"), pp2_text, language=language)
                    subject_q = _subject_probe_from_row(row, language=language)

                    stimuli.append(
                        {
                            "Stimulus_Code": f"{structure[0].upper()}_{grammaticality[0].upper()}_{_noun_congruency(
                                row["subject_number"],
                                row[f"{p1_pref}_number"],
                                row[f"{p2_pref}_number"],
                            )}",
                            "Structure": structure,
                            "VP_Grammaticality": grammaticality,
                            "Noun_Congruency": _noun_congruency(
                                row["subject_number"],
                                row[f"{p1_pref}_number"],
                                row[f"{p2_pref}_number"],
                            ),
                            "Noun_Gender_Congruency": f"{row['subject_gender'].upper()}{row[f'{p1_pref}_gender'].upper()}{row[f'{p2_pref}_gender'].upper()}",
                            "Congruency_Locus": _congruency_locus(
                                structure,
                                row["subject_number"],
                                row[f"{p1_pref}_number"],
                                row[f"{p2_pref}_number"],
                            ),
                            "Sentence_String": _render(structure, sentence_row2),
                            "Subject_Lemma": row["subject_noun"],
                            "Subject_Gender": row["subject_gender"],
                            "Subject_Number": row["subject_number"],
                            "Subject_No_Probe": row.get("subject_no_probe", ""),
                            "Subject_Zipf_Frequency": _zipf_fr(row["subject_noun"]),
                            "Subject_Length": _letter_count(row["subject_noun"]),
                            "Verb_Phrase": vp,
                            "Verb_Lemma": verb_head,
                            "Verb_Zipf_Frequency": _zipf_fr(verb_head),
                            "Verb_Length": _letter_count(verb_head),
                            "PP1_Preposition": row[f"{p1_pref}_prep"],
                            "PP1_Opposite_Preposition": row.get(f"{p1_pref}_opposite_prep", ""),
                            "PP1_Preposition_Zipf_Frequency": _zipf_fr(row[f"{p1_pref}_prep"]),
                            "PP1_Preposition_Length": _letter_count(row[f"{p1_pref}_prep"]),
                            "PP1_Lemma": row[f"{p1_pref}_noun"],
                            "PP1_Lemma_Zipf_Frequency": _zipf_fr(row[f"{p1_pref}_noun"]),
                            "PP1_Gender": row[f"{p1_pref}_gender"],
                            "PP1_Number": row[f"{p1_pref}_number"],
                            "PP2_Preposition": row[f"{p2_pref}_prep"],
                            "PP2_Opposite_Preposition": row.get(f"{p2_pref}_opposite_prep", ""),
                            "PP2_Preposition_Zipf_Frequency": _zipf_fr(row[f"{p2_pref}_prep"]),
                            "PP2_Preposition_Length": _letter_count(row[f"{p2_pref}_prep"]),
                            "PP2_Lemma_Zipf_Frequency": _zipf_fr(row[f"{p2_pref}_noun"]),
                            "PP2_Lemma": row[f"{p2_pref}_noun"],
                            "PP2_Gender": row[f"{p2_pref}_gender"],
                            "PP2_Number": row[f"{p2_pref}_number"],
                            "PP_Word_Budget": row["pp_word_budget"],
                            # "PP_Order": pp_order,
                            "scene_probe_1": scene_q1,
                            "scene_probe_2": scene_q2,
                            "subject_probe": subject_q,
                        }
                    )
    return stimuli


def write_stimuli(rows, output_path, delimiter=","):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)