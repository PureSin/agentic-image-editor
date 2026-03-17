"""Entry point: agentic image editor."""

import argparse
import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

from agent import AgentError, AuthenticationError, InsufficientBalanceError
from agents.pipeline import run_pipeline
import config
from tools import state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Edit an image using a natural language prompt.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --image photo.jpg --prompt "make it black and white and crop to a square"
  python main.py --image photo.jpg --prompt "add a warm vintage look" --output vintage.jpg
  python main.py --image photo.jpg --prompt "sharpen and boost contrast" --max-iterations 5
  python main.py --image photo.jpg --prompt "crop to square" --target-iterations 2
        """,
    )
    parser.add_argument("--image", required=True, help="Path to the input image")
    parser.add_argument("--prompt", required=True, help="Natural language editing instruction")
    parser.add_argument("--output", default=None, help="Output image path (default: output/<stem>_edited.<ext>)")
    parser.add_argument("--trace", default=None, help="Trace output path (default: output/<stem>_trace.json)")
    parser.add_argument(
        "--max-iterations", type=int, default=config.MAX_ITERATIONS,
        help=f"Hard ceiling on editor→judge cycles (default: {config.MAX_ITERATIONS})",
    )
    parser.add_argument(
        "--target-iterations", type=int, default=None,
        help="Accept result after this many iterations regardless of judge verdict",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    input_path = Path(args.image).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    output_path = args.output or str(output_dir / f"{input_path.stem}_edited{input_path.suffix}")
    trace_path = args.trace or str(output_dir / f"{input_path.stem}_trace.json")

    # Copy input to a temp working file — original is never modified
    suffix = input_path.suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        working_path = tmp.name
    shutil.copy2(str(input_path), working_path)

    state.set_working_path(working_path)
    state.reset_trace()

    print(f"Image            : {input_path}")
    print(f"Prompt           : {args.prompt}")
    print(f"Editor model     : {config.EDITOR_MODEL}")
    print(f"Judge model      : {config.JUDGE_MODEL}")
    print(f"Max iterations   : {args.max_iterations}")
    if args.target_iterations:
        print(f"Target iterations: {args.target_iterations}")
    print()

    try:
        response = await run_pipeline(
            original_image_path=str(input_path),
            working_image_path=working_path,
            prompt=args.prompt,
            max_iterations=args.max_iterations,
            target_iterations=args.target_iterations,
        )
    except (AgentError, FileNotFoundError, KeyboardInterrupt):
        if os.path.exists(working_path):
            os.unlink(working_path)
        raise
    finally:
        if os.path.exists(working_path):
            shutil.copy2(working_path, output_path)
            os.unlink(working_path)

    steps = state.get_trace()
    iterations_used = state._current_iteration

    trace_data = {
        "input": str(input_path),
        "output": output_path,
        "prompt": args.prompt,
        "editor_model": config.EDITOR_MODEL,
        "judge_model": config.JUDGE_MODEL,
        "max_iterations": args.max_iterations,
        "target_iterations": args.target_iterations,
        "iterations_used": iterations_used,
        "agent_summary": response,
        "steps": steps,
    }
    with open(trace_path, "w") as f:
        json.dump(trace_data, f, indent=2)

    print(f"Output     : {output_path}")
    print(f"Trace      : {trace_path}")
    print(f"Iterations : {iterations_used}")
    print(f"Tool calls : {len(steps)}")
    for i, step in enumerate(steps, 1):
        status = "✓" if step["success"] else "✗"
        args_str = ", ".join(f"{k}={v}" for k, v in step["args"].items()) if step["args"] else ""
        print(f"  {i}. [iter {step['iteration']}] {status} {step['tool']}({args_str})")
    print(f"\nSummary: {response}")


def main() -> None:
    args = parse_args()
    try:
        asyncio.run(run(args))
    except InsufficientBalanceError as e:
        print(f"\nError: {e}")
        raise SystemExit(1)
    except AuthenticationError as e:
        print(f"\nError: {e}")
        raise SystemExit(1)
    except AgentError as e:
        print(f"\nAgent error: {e}")
        raise SystemExit(1)
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(130)


if __name__ == "__main__":
    main()
