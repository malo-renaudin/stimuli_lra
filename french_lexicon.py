from itertools import permutations, product


def _entry(noun, gender, number, **extra):
    return {"noun": noun, "gender": gender, "number": number, **extra}


SUBJECTS = [
    {
        "forms": {
            "f_sg": {"display": "L'autrice", "noun": "autrice", "vp": "lit un livre", "vp_violation": "lisent un livre", "no_probe": ""},
            "f_pl": {"display": "Les autrices", "noun": "autrices", "vp": "lisent un livre", "vp_violation": "lit un livre", "no_probe": ""},
            "m_sg": {"display": "L'auteur", "noun": "auteur", "vp": "lit un livre", "vp_violation": "lisent un livre", "no_probe": ""},
            "m_pl": {"display": "Les auteurs", "noun": "auteurs", "vp": "lisent un livre", "vp_violation": "lit un livre", "no_probe": ""},
        },
        "no_probe": "",
    },
    {
        "forms": {
            "f_sg": {"display": "L'étudiante", "noun": "étudiante", "vp": "apprend une leçon", "vp_violation": "apprennent une leçon", "no_probe": ""},
            "f_pl": {"display": "Les étudiantes", "noun": "étudiantes", "vp": "apprennent une leçon", "vp_violation": "apprend une leçon", "no_probe": ""},
            "m_sg": {"display": "L'étudiant", "noun": "étudiant", "vp": "apprend une leçon", "vp_violation": "apprennent une leçon", "no_probe": ""},
            "m_pl": {"display": "Les étudiants", "noun": "étudiants", "vp": "apprennent une leçon", "vp_violation": "apprend une leçon", "no_probe": ""},
        },
        "no_probe": "",
    },
    {
        "forms": {
            "f_sg": {"display": "L'ouvrière", "noun": "ouvrière", "vp": "est fatiguée", "vp_violation": "sont fatiguées", "no_probe": ""},
            "f_pl": {"display": "Les ouvrières", "noun": "ouvrières", "vp": "sont fatiguées", "vp_violation": "est fatiguée", "no_probe": ""},
            "m_sg": {"display": "L'ouvrier", "noun": "ouvrier", "vp": "est fatigué", "vp_violation": "sont fatigués", "no_probe": ""},
            "m_pl": {"display": "Les ouvriers", "noun": "ouvriers", "vp": "sont fatigués", "vp_violation": "est fatigué", "no_probe": ""},
        },
        "no_probe": "",
    },
    {
        "forms": {
            "f_sg": {"display": "L'usagère", "noun": "usagère", "vp": "est en retard", "vp_violation": "sont en retard", "no_probe": ""},
            "f_pl": {"display": "Les usagères", "noun": "usagères", "vp": "sont en retard", "vp_violation": "est en retard", "no_probe": ""},
            "m_sg": {"display": "L'usager", "noun": "usager", "vp": "est en retard", "vp_violation": "sont en retard", "no_probe": ""},
            "m_pl": {"display": "Les usagers", "noun": "usagers", "vp": "sont en retard", "vp_violation": "est en retard", "no_probe": ""},
        },
        "no_probe": "",
    },
]

PLACES = [
    # _entry("atelier", "m", "singular", "culture"),
    # _entry("université", "f", "singular", "culture"),
    _entry("amphithéâtre", "m", "singular"),
    _entry("école", "f", "singular"),
    _entry("usine", "f", "singular"),
    _entry("entrepôt", "m", "singular"),
    _entry("abri", "m", "singular"),
    _entry("avenue", "f", "singular"),
    _entry("immeubles", "m", "plural"),
    _entry("escaliers", "m", "plural"),
    _entry("installations", "f", "plural"),
    _entry("habitations", "f", "plural"),
    _entry("infrastructures", "f", "plural"),
    _entry("affiches", "f", "plural"),
]

PREPOSITIONS = [
    {"label": "devant", "words": 2, "opposite": "derrière"},
    {"label": "derrière", "words": 2, "opposite": "devant"},
    {"label": "près de", "words": 2, "opposite": "loin de"},
    {"label": "à côté de", "words": 3, "opposite": "loin de"},
    {"label": "loin de", "words": 3, "opposite": "près de"},
    {"label": "en face de", "words": 3, "opposite": "derrière"},
    {"label": "à gauche de", "words": 3, "opposite": "à droite de"},
    {"label": "à droite de", "words": 3, "opposite": "à gauche de"},
]


def preposition_opposites(prepositions=PREPOSITIONS):
    labels = {prep["label"] for prep in prepositions}
    opposites = {}
    for prep in prepositions:
        label = prep["label"]
        opposite = prep.get("opposite", "")
        opposites[label] = opposite if opposite in labels else ""
    return opposites


def starts_with_vowel(word):
    return word[:1].lower() in "aeiouyàâéèêîïôùûü"


def _np(entry):
    noun = entry["noun"]
    if entry["number"] == "plural":
        return f"les {noun}"
    if starts_with_vowel(noun):
        return f"l'{noun}"
    return f"{'le' if entry['gender'] == 'm' else 'la'} {noun}"


def _subject(entry):
    noun = entry["noun"]
    return f"Les {noun}" if entry["number"] == "plural" else f"L'{noun}"


def _pp(preposition, entry):
    label = preposition["label"]
    noun = entry["noun"]
    if label.endswith("de"):
        if entry["number"] == "plural":
            return f"{label}s {noun}"
        if starts_with_vowel(noun):
            return f"{label} l'{noun}"
        article = "du" if entry["gender"] == "m" else "de la"
        return f"{label[:-2]}{article} {noun}"
    return f"{label} {_np(entry)}"


def preposition_pairs(total_words=5, prepositions=PREPOSITIONS):
    return [pair for pair in product(prepositions, repeat=2) if pair[0]["words"] + pair[1]["words"] == total_words]


def build_lexicon(total_prep_words=5):
    rows = []
    opposite_map = preposition_opposites()
    for subject in SUBJECTS:
        # Support two subject formats:
        # - legacy entries with keys: noun, gender, number, vp, vp_violation
        # - grouped entries with a `forms` dict containing keys like 'm_sg','f_sg','m_pl','f_pl'
        if "forms" in subject:
            # expand each form into its own lexicon row
            forms = subject["forms"]

            def strip_article(display):
                d = display
                for prefix in ("Les ", "L'", "Le ", "La "):
                    if d.startswith(prefix):
                        return d[len(prefix):]
                return d

            for place1, place2 in permutations(PLACES, 2):
                for prep1, prep2 in preposition_pairs(total_prep_words):
                    for form_key, form in forms.items():
                        # form_key example: 'm_sg' or 'f_pl'
                        gender, number = form_key.split("_")
                        display = form.get("display") or form.get("subject")
                        noun = form.get("noun") or strip_article(display or "")
                        vp = form.get("vp")

                        # violation VP: prefer explicit `vp_violation` in the form,
                        # otherwise use the same-gender opposite-number form's `vp` if available
                        vp_violation = form.get("vp_violation")
                        if vp_violation is None:
                            opposite_number = "pl" if number == "sg" else "sg"
                            opposite_key = f"{gender}_{opposite_number}"
                            if opposite_key in forms:
                                vp_violation = forms[opposite_key].get("vp")

                        rows.append(
                            {
                                "subject": display,
                                "subject_noun": noun,
                                "subject_gender": "m" if gender == "m" else "f",
                                "subject_number": "plural" if number == "pl" else "singular",
                                "verb_phrase": vp,
                                "verb_phrase_violation": vp_violation,
                                "subject_no_probe": form.get("no_probe", subject.get("no_probe", "")),
                                "pp1_prep": prep1["label"],
                                "pp1_opposite_prep": opposite_map.get(prep1["label"], ""),
                                "pp1": _pp(prep1, place1),
                                "pp1_noun": place1["noun"],
                                "pp1_gender": place1["gender"],
                                "pp1_number": place1["number"],
                                "pp2_prep": prep2["label"],
                                "pp2_opposite_prep": opposite_map.get(prep2["label"], ""),
                                "pp2": _pp(prep2, place2),
                                "pp2_noun": place2["noun"],
                                "pp2_gender": place2["gender"],
                                "pp2_number": place2["number"],
                                "pp_word_budget": total_prep_words,
                            }
                        )
        else:
            for place1, place2 in permutations(PLACES, 2):
                for prep1, prep2 in preposition_pairs(total_prep_words):
                    rows.append(
                        {
                            "subject": _subject(subject),
                            "subject_noun": subject["noun"],
                            "subject_gender": subject["gender"],
                            "subject_number": subject["number"],
                            "verb_phrase": subject["vp"],
                            "verb_phrase_violation": subject.get("vp_violation"),
                            "subject_no_probe": subject.get("no_probe", ""),
                            "pp1_prep": prep1["label"],
                            "pp1_opposite_prep": opposite_map.get(prep1["label"], ""),
                            "pp1": _pp(prep1, place1),
                            "pp1_noun": place1["noun"],
                            "pp1_gender": place1["gender"],
                            "pp1_number": place1["number"],
                            "pp2_prep": prep2["label"],
                            "pp2_opposite_prep": opposite_map.get(prep2["label"], ""),
                            "pp2": _pp(prep2, place2),
                            "pp2_noun": place2["noun"],
                            "pp2_gender": place2["gender"],
                            "pp2_number": place2["number"],
                            "pp_word_budget": total_prep_words,
                        }
                    )
    return rows