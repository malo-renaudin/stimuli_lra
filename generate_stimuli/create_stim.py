import argparse
from generator import generate_stimuli, write_stimuli

argument_parser = argparse.ArgumentParser(description="Generate stimuli for experiments.")
argument_parser.add_argument("--language", type=str, required=True, help="Language of the stimuli to generate.")
argument_parser.add_argument("--output", type=str, required=True, help="Output file path for the generated stimuli.")
args = argument_parser.parse_args()

stim = generate_stimuli(args.language)
write_stimuli(stim, args.output)
