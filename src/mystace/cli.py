import argparse
import json
from importlib.metadata import version
from pathlib import Path

from .mustache_tree import render_from_template


def cli(argv=None):
    parser = argparse.ArgumentParser(
        prog="mystace",
        description="an explosive mustache v1.4 implementation with lambdas",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=version("mystace"),
    )

    parser.add_argument(
        "template",
        help="mustache template file (use -s for string)",
    )

    parser.add_argument(
        "-s",
        "--string",
        action="store_true",
        help="pass in a string instead of a file for template",
    )

    parser.add_argument(
        "-d",
        "--data",
        type=argparse.FileType(),
        default="-",
        help="data json file (defaults to stdin)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w"),
        default="-",
        help="output file (defaults to stdout)",
    )

    parser.add_argument(
        "-p",
        "--partial",
        type=argparse.FileType(),
        action="append",
        help="mustache partial file (can add multiple)",
    )

    parser.add_argument(
        "--partial-dir",
        help="directory with mustache partials",
    )

    parser.add_argument(
        "--partial-ext",
        default=".mustache",
        help="partial file extention (defaults to '.mustache')",
    )

    parser.add_argument(
        "--left-delimiter",
        default="{{",
        help="left mustache template delimiter (defaults to '{{')",
    )

    parser.add_argument(
        "--right-delimiter",
        default="}}",
        help="right mustache template delimiter (defaults to '}}')",
    )

    args = parser.parse_args(argv)

    if args.string:
        template = args.template
    else:
        with open(args.template) as f:
            template = f.read()

    if args.partial is None:
        args.partial = []

    data = json.load(args.data)

    partials = {}
    for file in args.partial:
        # file.name is the full name; Path(file.name).name is what we need
        partial_name = Path(file.name).name.removesuffix(args.partial_ext)
        partials[partial_name] = file.read()
        file.close()
    if args.partial_dir:
        dir_path = Path(args.partial_dir)
        partial_paths = dir_path.rglob(f"**/*{args.partial_ext}")
        for path in partial_paths:
            with path.open() as file:
                partial_name = path.name.removesuffix(args.partial_ext)
                partials[partial_name] = file.read()

    # left_delimiter = args.left_delimiter
    # right_delimiter = args.right_delimiter

    output = render_from_template(template, data, partials)
    args.output.write(output)


if __name__ == "__main__":
    cli()
