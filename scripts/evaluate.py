import argparse

from src.evaluation import evaluate
from src.plot_evaluation import plot_evaluation
from src.report_evaluation import report_evaluation


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=1000)
    parser.add_argument("--tune", type=int, default=1000)
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--cores", type=int, default=1)
    parser.add_argument("--refit", action="store_true")
    parser.add_argument("--skip-sensitivity", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    evaluate(args)
    plot_evaluation(include_sensitivity=not args.skip_sensitivity)
    report_evaluation(include_sensitivity=not args.skip_sensitivity)


if __name__ == "__main__":
    main()
