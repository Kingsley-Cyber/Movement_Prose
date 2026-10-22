import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.probability import predict
from engine.ontology import write


def main():
    p = argparse.ArgumentParser(description="BLOCK deterministic, uncalibrated matchup prediction")
    p.add_argument("fighter_a")
    p.add_argument("fighter_b")
    p.add_argument("--ruleset", choices=["mma", "boxing"], default="mma")
    p.add_argument("--output")
    args = p.parse_args()
    result = predict(args.fighter_a, args.fighter_b, args.ruleset)
    if args.output:
        write(args.output, result)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
