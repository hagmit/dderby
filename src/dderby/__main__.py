"""Readiness output only; never enqueue or process media."""
import json


def main() -> None:
    print(json.dumps({"service": "dderby", "mode": "bootstrap", "processing_enabled": False}))


if __name__ == "__main__":
    main()
