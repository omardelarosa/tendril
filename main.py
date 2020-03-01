import argparse

from midi import learn_rule_from_file


def cli():
    parser = argparse.ArgumentParser(
        description="Learn cellular automata from sequences and generate new sequences."
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
        "--seed",
        metavar="S",
        type=str,
        default=None,
        help="Provide an array as a JSON file to be used as a seed state.",
    )

    args = parser.parse_args()

    if args.learn:
        learn_rule_from_file(args.learn)


if __name__ == "__main__":
    # Run in CLI mode
    cli()
