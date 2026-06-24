import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
import seaborn as sns


def infer_gender_from_filename(path: Path):
    name = path.stem.lower()
    if "_male" in name or name.endswith("_male"):
        return "male"
    if "_female" in name or name.endswith("_female"):
        return "female"
    if name.endswith("_m") or "_m" in name:
        return "male"
    if name.endswith("_f") or "_f" in name:
        return "female"
    return "unknown"


def compute_stats(wav_path: Path):
    data, sr = sf.read(wav_path, always_2d=False)
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    duration = len(data) / sr
    rms = float(np.sqrt(np.mean(np.square(data.astype(float)))))
    return duration, rms


def main():
    ap = argparse.ArgumentParser(description="Plot audio duration and RMS by structure and voice gender")
    ap.add_argument("--run_csv", required=True)
    ap.add_argument("--audio_dir", required=True)
    ap.add_argument("--output_plot", required=False)
    args = ap.parse_args()

    run_csv = Path(args.run_csv)
    audio_dir = Path(args.audio_dir)
    df = pd.read_csv(run_csv)

    # try to find a column that contains WAV filenames
    wav_col = None
    for c in df.columns:
        if df[c].astype(str).str.contains(r"\.wav$", regex=True).any():
            wav_col = c
            break

    wav_paths = sorted(audio_dir.glob("*.wav"))
    # Build an expanded table: one row per WAV (male and female) with original metadata
    expanded_rows = []

    # helper markers
    male_markers = ("_male", "-male", ".male", "_m", "-m", ".m")
    female_markers = ("_female", "-female", ".female", "_f", "-f", ".f")

    for i, row in df.iterrows():
        code = str(row.get("Stimulus_Code", "")).strip().lower()
        sent = str(row.get("Sentence_String", "")).strip().lower()

        # search for candidates matching this row
        male_file = None
        female_file = None
        for p in wav_paths:
            name = p.name.lower()
            matches_row = False
            if code and code in name:
                matches_row = True
            elif sent and len(sent) > 8 and sent[:12] in name:
                matches_row = True

            if matches_row:
                if any(m in name for m in male_markers):
                    male_file = p
                if any(f in name for f in female_markers):
                    female_file = p

        # fallback: if not found, and audio count == 2 * rows, take by order
        if not male_file or not female_file:
            if len(wav_paths) == 2 * len(df):
                try:
                    cand_m = wav_paths[2 * i]
                    cand_f = wav_paths[2 * i + 1]
                    # assign based on markers if possible otherwise keep order
                    if any(m in cand_m.name.lower() for m in male_markers) or any(f in cand_f.name.lower() for f in female_markers):
                        male_file = cand_m
                        female_file = cand_f
                    else:
                        # try swap if necessary
                        if any(m in cand_f.name.lower() for m in male_markers):
                            male_file = cand_f
                            female_file = cand_m
                        else:
                            male_file = cand_m
                            female_file = cand_f
                except Exception:
                    pass

        # if still not found, try looser matching by checking filename prefixes
        if not (male_file and female_file):
            prefix = code or (sent[:10] if sent else "")
            if prefix:
                for p in wav_paths:
                    if prefix in p.name.lower():
                        if any(m in p.name.lower() for m in male_markers) and not male_file:
                            male_file = p
                        if any(f in p.name.lower() for f in female_markers) and not female_file:
                            female_file = p

        # append found files (if any) as separate rows
        if male_file:
            r = dict(row)
            r["_wav_path"] = male_file
            r["Gender_Inferred"] = infer_gender_from_filename(male_file)
            expanded_rows.append(r)
        if female_file:
            r = dict(row)
            r["_wav_path"] = female_file
            r["Gender_Inferred"] = infer_gender_from_filename(female_file)
            expanded_rows.append(r)

    if not expanded_rows:
        raise SystemExit("No WAV files matched any rows. Check filenames and Stimulus_Code matching.")

    exp_df = pd.DataFrame(expanded_rows)

    # compute stats per WAV
    durations = []
    rms_vals = []
    for p in exp_df["_wav_path"]:
        dur, rms = compute_stats(Path(p))
        durations.append(dur)
        rms_vals.append(rms)

    exp_df["Duration"] = durations
    exp_df["RMS"] = rms_vals

    # find structure column
    structure_col = None
    for c in ("Structure", "structure", "Condition", "condition", "Structure_Label"):
        if c in df.columns:
            structure_col = c
            break
    if structure_col is None:
        raise SystemExit("No structure column found. Add a `Structure` column to the CSV.")

    sns.set(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    sns.boxplot(x=structure_col, y="Duration", data=exp_df, ax=axes[0, 0])
    axes[0, 0].set_title("Duration by Structure")

    sns.boxplot(x=structure_col, y="RMS", data=exp_df, ax=axes[0, 1])
    axes[0, 1].set_title("RMS by Structure")

    sns.boxplot(x="Gender_Inferred", y="Duration", data=exp_df, ax=axes[1, 0])
    axes[1, 0].set_title("Duration by Voice Gender")

    sns.boxplot(x="Gender_Inferred", y="RMS", data=exp_df, ax=axes[1, 1])
    axes[1, 1].set_title("RMS by Voice Gender")

    plt.tight_layout()
    if args.output_plot:
        plt.savefig(args.output_plot)
        print(f"Plot saved to {args.output_plot}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
