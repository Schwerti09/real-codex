import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay emergency events")
    parser.add_argument("--file", default="logs/emergency_log.jsonl")
    args = parser.parse_args()

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                evt = json.loads(line)
                ts = evt.get("timestamp", 0)
                print(f"[{ts}] {evt.get('type')} - Drone {evt.get('drone_id')}")
    except FileNotFoundError:
        print("Log file not found")


if __name__ == "__main__":
    main()
