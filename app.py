from src import llm, config
from src.agent import answer


def main():
    client = llm.get_client()
    print(f"On-Call Copilot  (provider={config.PROVIDER})  — ask a question, Ctrl-C to quit.\n")
    while True:
        try:
            q = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        print("\nbot>", answer(q, client), "\n")


if __name__ == "__main__":
    main()
