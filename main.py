import argparse

from midi import (
    learn_rule_from_file,
    generate_states_from_rule_and_seed,
    get_rule_from_file,
    get_seed_from_file,
    DEFAULT_BEAT_DURATION,
    DEFAULT_SEQUENCE_STEPS,
)
from ca import DEFAULT_SEED
from convert import convert, generate_all_rules_for_k
import sampling


def cli():
    DEFAULT_OUTDIR = "."

    parser = argparse.ArgumentParser(
        description="Learn cellular automata from sequences and generate new sequences."
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enables additional logging and debug behavior.",
    )

    parser.add_argument(
        "--png",
        default=False,
        action="store_true",
        help="Save PNG of the generated states.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Save JSON of the generated states.",
    )

    parser.add_argument(
        "--midi",
        action="store_true",
        default=False,
        help="Save MIDI of the generated states.",
    )

    parser.add_argument(
        "--learn",
        metavar="S",
        type=str,
        default=None,
        help="Create a rule file from a sequence provided as JSON or MIDI.",
    )

    parser.add_argument(
        "--generateFrom",
        metavar="R",
        type=str,
        default=None,
        help="Generate a new sequence from a provided JSON Rulefile.",
    )

    parser.add_argument(
        "--generate",
        default=False,
        action="store_true",
        help="After learning a rule, generate a new pattern from the rule.",
    )

    parser.add_argument(
        "--generateAllRules",
        default=None,
        type=str,
        help="Generate all rules for a given set of ECA parameters and dump json to outdir.",
    )

    parser.add_argument(
        "--convert",
        metavar="S",
        default=None,
        type=str,
        help="Convert a target file from png, midi to states.json format",
    )

    parser.add_argument(
        "--seed",
        metavar="S",
        type=str,
        default=None,
        help="Provide an array as a JSON file to be used as a seed state.",
    )

    # Model parameters
    parser.add_argument(
        "--scaleNum", metavar="SN", type=int, default=None, help="Select scale 0-12",
    )

    parser.add_argument(
        "--scaleType",
        metavar="ST",
        type=str,
        default="maj",
        help="Select scale type: [maj, min]",
    )

    parser.add_argument(
        "--kernelRadius",
        metavar="R",
        type=int,
        default=1,
        help="The radius of the kernel around the cell.",
    )

    parser.add_argument(
        "--steps",
        metavar="L",
        type=int,
        default=DEFAULT_SEQUENCE_STEPS,
        help="The number of total length in steps of the generated sequence. (Default: {})".format(
            DEFAULT_SEQUENCE_STEPS
        ),
    )

    parser.add_argument(
        "--beatDuration",
        metavar="D",
        type=int,
        default=DEFAULT_BEAT_DURATION,
        help="The total duration in ticks for each MIDI beat. (Default: {})".format(
            DEFAULT_BEAT_DURATION
        ),
    )

    parser.add_argument(
        "--outdir",
        metavar="O",
        type=str,
        default=DEFAULT_OUTDIR,
        help="Output Directory: (default: '{}')".format(DEFAULT_OUTDIR),
    )

    parser.add_argument(
        "--sampler",
        metavar="F",
        type=str,
        default=None,
        help="Choose the sampling function to apply to the resulting cellular automaton sequence. (Options: {})".format(
            sampling.__all__
        ),
    )

    args = parser.parse_args()

    # Store as variables for chaining
    rule = None
    f_name = None

    debug_mode = False

    if args.debug:
        debug_mode = True

    # Just a simple conversion
    if args.convert:
        convert(args.convert)
        exit()

    if args.generateAllRules:
        if args.kernelRadius:
            k_radius = args.kernelRadius
        else:
            print("--kernelRadius is required to generate rules")
            exit(1)
        generate_all_rules_for_k(out_dir=args.generateAllRules, k_radius=k_radius)

    if args.learn:
        f_name = args.learn
        rule, states = learn_rule_from_file(
            args.learn,
            scale_num=args.scaleNum,
            scale_type=args.scaleType,
            k_radius=args.kernelRadius,
            save_json=args.json,
            debug=debug_mode,
        )

    if args.generate or args.generateFrom:
        if args.generate and not rule and f_name:
            print(
                "This command must be chained and run after learning a cell update rule."
            )
            exit(1)

        if args.seed:
            # Get seed from file
            seed = get_seed_from_file(args.seed)
        else:
            seed = DEFAULT_SEED

        if not rule:
            # Error if no rule is present
            if not args.generateFrom:
                print("Rule must be provided from file or learned.")
                exit(1)
            # Get rule from file
            rule = get_rule_from_file(args.generateFrom)

        if not f_name:
            f_name = args.generateFrom

        if debug_mode:
            print("f_name: ", f_name)
            print("using seed: ", seed)
            print("using rule: ", rule)

        # If not chaining
        generate_states_from_rule_and_seed(
            f_name=f_name,
            seed=seed,
            rule=rule,
            scale_num=args.scaleNum,
            scale_type=args.scaleType,
            save_png=args.png,
            save_json=args.json,
            save_midi=args.midi,
            sampler_name=args.sampler,
            steps=args.steps,
            beat_duration=args.beatDuration,
        )


if __name__ == "__main__":
    # Run in CLI mode
    cli()
