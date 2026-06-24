from itertools import permutations, product


def _entry(noun, gender, number, **extra):
    return {"noun": noun, "gender": gender, "number": number, **extra}


SUBJECTS = [
    {
        "forms": {
            "f_sg": {"display": "The author", "noun": "author", "vp": "reads a book", "vp_violation": "read a book", "no_probe": ""},
            "f_pl": {"display": "The authors", "noun": "authors", "vp": "read a book", "vp_violation": "reads a book", "no_probe": ""},
            "m_sg": {"display": "The author", "noun": "author", "vp": "reads a book", "vp_violation": "read a book", "no_probe": ""},
            "m_pl": {"display": "The authors", "noun": "authors", "vp": "read a book", "vp_violation": "reads a book", "no_probe": ""},
        },
        "no_probe": "",
    },
    {
        "forms": {
            "f_sg": {"display": "The student", "noun": "student", "vp": "learns a lesson", "vp_violation": "learn a lesson", "no_probe": ""},
            "f_pl": {"display": "The students", "noun": "students", "vp": "learn a lesson", "vp_violation": "learns a lesson", "no_probe": ""},
            "m_sg": {"display": "The student", "noun": "student", "vp": "learns a lesson", "vp_violation": "learn a lesson", "no_probe": ""},
            "m_pl": {"display": "The students", "noun": "students", "vp": "learn a lesson", "vp_violation": "learns a lesson", "no_probe": ""},
        },
        "no_probe": "",
    },
    {
        "forms": {
            "f_sg": {"display": "The worker", "noun": "worker", "vp": "is tired", "vp_violation": "are tired", "no_probe": ""},
            "f_pl": {"display": "The workers", "noun": "workers", "vp": "are tired", "vp_violation": "is tired", "no_probe": ""},
            "m_sg": {"display": "The worker", "noun": "worker", "vp": "is tired", "vp_violation": "are tired", "no_probe": ""},
            "m_pl": {"display": "The workers", "noun": "workers", "vp": "are tired", "vp_violation": "is tired", "no_probe": ""},
        },
        "no_probe": "",
    },
    {
        "forms": {
            "f_sg": {"display": "The passenger", "noun": "passenger", "vp": "is late", "vp_violation": "are late", "no_probe": ""},
            "f_pl": {"display": "The passengers", "noun": "passengers", "vp": "are late", "vp_violation": "is late", "no_probe": ""},
            "m_sg": {"display": "The passenger", "noun": "passenger", "vp": "is late", "vp_violation": "are late", "no_probe": ""},
            "m_pl": {"display": "The passengers", "noun": "passengers", "vp": "are late", "vp_violation": "is late", "no_probe": ""},
        },
        "no_probe": "",
    },
]

PLACES = [
    _entry("auditorium", "m", "singular"),
    _entry("school", "f", "singular"),
    _entry("factory", "f", "singular"),
    _entry("warehouse", "m", "singular"),
    _entry("shelter", "m", "singular"),
    _entry("avenue", "f", "singular"),
    _entry("apartment buildings", "m", "plural"),
    _entry("stairs", "m", "plural"),
    _entry("facilities", "f", "plural"),
    _entry("residences", "f", "plural"),
    _entry("infrastructures", "f", "plural"),
    _entry("posters", "f", "plural"),
]

PREPOSITIONS = [
    {"label": "in front of", "words": 3, "opposite": "behind"},
    {"label": "behind", "words": 1, "opposite": "in front of"},
    {"label": "near", "words": 1, "opposite": "far from"},
    {"label": "next to", "words": 2, "opposite": "far from"},
    {"label": "far from", "words": 2, "opposite": "near"},
    {"label": "opposite", "words": 2, "opposite": "behind"},
    {"label": "to the left of", "words": 3, "opposite": "to the right of"},
    {"label": "to the right of", "words": 3, "opposite": "to the left of"},
]


def preposition_opposites(prepositions=PREPOSITIONS):
    labels = {prep["label"] for prep in prepositions}
    opposites = {}
    for prep in prepositions:
        label = prep["label"]
        opposite = prep.get("opposite", "")
        opposites[label] = opposite if opposite in labels else ""
    return opposites

def _np(entry):
    noun = entry["noun"]
    return f"the {noun}"


def _subject(entry):
    noun = entry["noun"]
    return f"The {noun}"


def _pp(preposition, entry):
    label = preposition["label"]
    return f"{label} {_np(entry)}"


def preposition_pairs(total_words=5, prepositions=PREPOSITIONS):
    return [pair for pair in product(prepositions, repeat=2) if pair[0]["words"] + pair[1]["words"] == total_words]


def build_lexicon(total_prep_words=5):
    rows = []
    opposite_map = preposition_opposites()
    for subject in SUBJECTS:
        if "forms" in subject:
            forms = subject["forms"]

            def strip_article(display):
                d = display
                for prefix in ("The",):
                    if d.startswith(prefix + " "):
                        return d[len(prefix) + 1:]
                return d

            for place1, place2 in permutations(PLACES, 2):
                for prep1, prep2 in preposition_pairs(total_prep_words):
                    for form_key, form in forms.items():
                        gender, number = form_key.split("_")
                        display = form.get("display") or form.get("subject")
                        noun = form.get("noun") or strip_article(display or "")
                        vp = form.get("vp")

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
