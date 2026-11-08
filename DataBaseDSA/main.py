from cli import build_parser, run
from migrations.init import migrate


def main(argv=None):
    migrate()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:  # no arguments -> open the window
        args = parser.parse_args(["gui"])
    run(args)


if __name__ == "__main__":
    main()