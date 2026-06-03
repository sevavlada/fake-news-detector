#!/usr/bin/env python3
"""
Fake News Detection System - Main Entry Point

Usage:
    python run.py                    # Interactive mode
    python run.py -a                 # Use Architecture A (router)
    python run.py -b                 # Use Architecture B (parallel)
    python run.py -q "Your query"    # Direct query
    python run.py -v                 # Verbose output
"""

import argparse
import sys
import os

# Add parent directory to path so we can import as a package
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

# Now import using the package name
from fake_news_detector.state import create_initial_state
from fake_news_detector.graphs import create_router_graph, create_parallel_graph
from fake_news_detector.graphs.architecture_b import create_truly_parallel_graph
from fake_news_detector.utils import format_result, format_comparable


SAMPLE_QUERIES = [
    "Солнце горячее",
    "The Earth is flat and NASA is hiding the truth",
    "BREAKING: Scientists discover that coffee cures all diseases!!!",
    "COVID-19 vaccines contain microchips for government tracking",
]


def run_detection(query: str, architecture: str = "A", verbose: bool = False,
                  parallel: bool = False, compare: bool = False, as_json: bool = False):
    """Run fake news detection on a query."""
    print(f"\nUsing Architecture {architecture}")
    print("-" * 40)

    if architecture == "A":
        graph = create_router_graph()
    elif architecture == "B":
        if parallel:
            print("(Using truly parallel execution)")
            graph = create_truly_parallel_graph()
        else:
            graph = create_parallel_graph()
    else:
        print(f"Unknown architecture: {architecture}")
        return None

    initial_state = create_initial_state(query)

    try:
        result = graph.invoke(initial_state)
        if compare or as_json:
            source = f"Fake News Detector (Arch {architecture})"
            print(format_comparable(result, source=source, as_json=as_json))
        else:
            print(format_result(result, verbose=verbose))
        return result
    except Exception as e:
        print(f"Error during detection: {e}")
        import traceback
        traceback.print_exc()
        return None


def interactive_mode():
    """Run in interactive mode."""
    print("=" * 60)
    print("FAKE NEWS DETECTION SYSTEM")
    print("=" * 60)
    print("\nArchitectures available:")
    print("  A - Router-based (selects one agent)")
    print("  B - Parallel synthesis (all agents)")
    print("\nCommands:")
    print("  quit/exit - Exit the program")
    print("  sample    - Run sample queries")
    print("  arch A/B  - Switch architecture")
    print()

    current_arch = "B"

    while True:
        try:
            query = input(f"\n[Arch {current_arch}] Enter query (or command): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue

        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if query.lower() == "sample":
            print("\nRunning sample queries...")
            for sq in SAMPLE_QUERIES:
                print(f"\n{'=' * 60}")
                print(f"Sample: {sq}")
                run_detection(sq, current_arch)
            continue

        if query.lower().startswith("arch "):
            new_arch = query.split()[-1].upper()
            if new_arch in ("A", "B"):
                current_arch = new_arch
                print(f"Switched to Architecture {current_arch}")
            else:
                print("Invalid architecture. Use A or B.")
            continue

        run_detection(query, current_arch)


def main():
    parser = argparse.ArgumentParser(
        description="Fake News Detection Multi-Agent System"
    )
    parser.add_argument(
        "-a", "--arch-a", action="store_true",
        help="Use Architecture A (router-based)"
    )
    parser.add_argument(
        "-b", "--arch-b", action="store_true",
        help="Use Architecture B (parallel synthesis)"
    )
    parser.add_argument(
        "-q", "--query", type=str,
        help="Query to analyze"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-p", "--parallel", action="store_true",
        help="Use truly parallel execution (with Architecture B)"
    )
    parser.add_argument(
        "-s", "--sample", action="store_true",
        help="Run sample queries"
    )
    parser.add_argument(
        "-c", "--compare", action="store_true",
        help="Output in the shared canonical format (for A/B testing)"
    )
    parser.add_argument(
        "-j", "--json", action="store_true",
        help="Output the canonical verdict as raw JSON (for A/B testing)"
    )

    args = parser.parse_args()

    if args.arch_a:
        arch = "A"
    elif args.arch_b:
        arch = "B"
    else:
        # Default: Architecture B — all agents in sequence (D -> T -> C -> synthesizer).
        arch = "B"

    if args.sample:
        print("Running sample queries...")
        for sq in SAMPLE_QUERIES:
            print(f"\n{'=' * 60}")
            print(f"Sample: {sq}")
            run_detection(sq, arch, verbose=args.verbose, parallel=args.parallel,
                          compare=args.compare, as_json=args.json)
        return

    if args.query:
        run_detection(args.query, arch, verbose=args.verbose, parallel=args.parallel,
                      compare=args.compare, as_json=args.json)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
