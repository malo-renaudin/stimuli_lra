import pandas as pd
import random
import argparse 

argument_parser = argparse.ArgumentParser(description="Create runs from stimuli.")
argument_parser.add_argument("--input", type=str, required=True, help="Input CSV file path for the stimuli.")
argument_parser.add_argument("--output_dir", type=str, required=True, help="Output directory for the generated runs.")
argument_parser.add_argument("--num_runs", type=int, default=6, help="Number of runs to create.")
args = argument_parser.parse_args()

df = pd.read_csv(args.input)
df['CodePrefix'] = df['Stimulus_Code'].astype(str).str.split('_').str[:2].str.join('_')

pool = df.copy()
prefixes = pool['CodePrefix'].unique()
runs = []
seed = 13
R = args.num_runs

for run_i in range(R):
    rng = random.Random(seed + run_i)
    parts = []
    if pool.empty:
        break
    for prefix in prefixes:
        sub = pool[pool['CodePrefix'] == prefix]
        if sub.empty:
            continue
        noun_vals = sorted(sub['Noun_Congruency'].unique())
        gender_vals = sorted(sub['Noun_Gender_Congruency'].unique())
        if len(noun_vals) != len(gender_vals):
            noun_vals = sorted(df['Noun_Congruency'].unique())
            gender_vals = sorted(df['Noun_Gender_Congruency'].unique())
        perm = rng.sample(gender_vals, k=len(gender_vals))
        mapping = dict(zip(noun_vals, perm))
        sub_ok = sub[sub['Noun_Gender_Congruency'] == sub['Noun_Congruency'].map(mapping)]
        if sub_ok.empty:
            continue
        sampled = sub_ok.groupby('Stimulus_Code', group_keys=False).apply(
            lambda g: g.sample(n=1, random_state=rng.randint(0, 2**30 - 1))
        )
        parts.append(sampled)
    if parts:
        run_df = pd.concat(parts, ignore_index=False)
        runs.append(run_df)
        pool = pool.drop(run_df.index)            # remove used rows so they can't appear in later runs
        run_df.to_csv(f"{args.output_dir}/run_{run_i+1:02d}.csv", index=False)
    else:
        runs.append(pd.DataFrame())  # empty run

print("Created runs; sizes:", [len(r) for r in runs])