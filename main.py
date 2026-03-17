"""Entry point: agentic image editor."""

import argparse
import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

import agent as agent_module
from agent import AgentError, AuthenticationError, InsufficientBalanceError
from tools import state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Edit an image using a natural language prompt.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --image photo.jpg --prompt "make it black and white and crop to a square"
  python main.py --image photo.jpg --prompt "add a warm vintage look" --output vintage.jpg
  python main.py --image photo.jpg --prompt "sharpen and boost contrast" --trace my_trace.json
        """,
    )
    parser.add_argument("--image", required=True, help="Path to the input image")
    parser.add_argument("--prompt", required=True, help="Natural language editing instruction")
    parser.add_argument("--output", default=None, help="Output image path (default: output/<input-stem>_edited.<ext>)")
    parser.add_argument("--trace", default=None, help="Trace output path (default: output/<input-stem>_trace.json)")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    input_path = Path(args.image).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    output_path = args.output or str(output_dir / f"{input_path.stem}_edited{input_path.suffix}")
    trace_path = args.trace or str(output_dir / f"{input_path.stem}_trace.json")
    args.output = output_path
    args.trace = trace_path

    # Copy input to a temp working file so originals are never overwritten
    suffix = input_path.suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        working_path = tmp.name
    shutil.copy2(str(input_path), working_path)

    state.set_working_path(working_path)
    state.reset_trace()

    print(f"Image : {input_path}")
    print(f"Prompt: {args.prompt}")
    print(f"Model : {os.getenv('MODEL', 'GLM-4.6V')}\n")

    try:
        response = await agent_module.run_agent(str(input_path), args.prompt)
    except (AgentError, FileNotFoundError, KeyboardInterrupt) as e:
        # Clean up temp file before re-raising
        if os.path.exists(working_path):
            os.unlink(working_path)
        raise
    finally:
        # Write whatever progress was made, even on partial runs
        if os.path.exists(working_path):
            shutil.copy2(working_path, args.output)
            os.unlink(working_path)

    steps = state.get_trace()
    trace_data = {
        "input": str(input_path),
        "output": args.output,
        "prompt": args.prompt,
        "model": os.getenv("MODEL", "GLM-4.6V"),
        "agent_summary": response,
        "steps": steps,
    }
    with open(args.trace, "w") as f:
        json.dump(trace_data, f, indent=2)

    print(f"Output : {args.output}")
    print(f"Trace  : {args.trace}")
    print(f"Steps  : {len(steps)}")
    for i, step in enumerate(steps, 1):
        status = "✓" if step["success"] else "✗"
        args_str = ", ".join(f"{k}={v}" for k, v in step["args"].items()) if step["args"] else ""
        print(f"  {i}. {status} {step['tool']}({args_str})")
    print(f"\nAgent: {response}")


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
