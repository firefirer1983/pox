import sys
from .err import run_error
import logging
from argparse import ArgumentParser

DEFAULT_NOTIFICATION = "POX 0.0.1 on linux\n"

logger = logging.getLogger(__name__)



def exec_sript(file_path: str):
    with open(file_path, "r") as f:
        for line in f.read():
            logger.info(f"{line}")


def run(source: str):
    pass


def run_repl():
    sys.stdout.write(DEFAULT_NOTIFICATION)

    while True:
        cmd: str = input(">>> ")
        if run_error:
            continue


def main():
    parser = ArgumentParser()
    parser.add_argument()
    args = parser.parse_args()
    if len(args) > 1:
        sys.stderr.write("pox xxx.pox")
        raise SystemExit(-1)
    elif len(args) == 1:
        logger.info(f"Execute script: {args[0]}")
        exec_sript(args[0])
    else:
        logger.info("Start REPL")
        run_repl()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
