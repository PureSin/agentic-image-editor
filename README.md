# Agentic Image Editor

An agentic image editor powered by the [Agent Development Kit (ADK)](https://google.github.io/adk-docs/) framework and [ImageMagick](https://imagemagick.org/).

## Overview

Given an input image and a natural language prompt, the agent:

1. **Inspects** the image (dimensions, format, colorspace)
2. **Reasons** about the prompt to plan which tools to apply and in what order
3. **Executes** each ImageMagick operation deterministically
4. **Produces** an output image and a `trace.json` of every decision and command run

```
Input Image + Prompt
        │
        ▼
  ┌─────────────┐
  │  ADK Agent  │  ← GLM-4.6V (or any OpenAI-compatible model)
  └──────┬──────┘
         │  selects & sequences tools
         ▼
  ┌──────────────────────────────────────┐
  │  ImageMagick Tool Execution          │
  │  crop → grayscale → sharpen → ...   │
  └──────────────────┬───────────────────┘
                     │
                     ▼
         output.jpg + trace.json
```

## Setup

### 1. Install ImageMagick

```bash
brew install imagemagick   # macOS
sudo apt install imagemagick  # Ubuntu/Debian
```

### 2. Install Python dependencies

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
# Edit .env and set your Z_AI_API_KEY
```

The model is configured via `.env` — swap `MODEL` to try any OpenAI-compatible multimodal model:

```env
Z_AI_API_KEY=your-key
MODEL=GLM-4.6V
API_BASE=https://api.z.ai/api/paas/v4/
```

## Usage

```bash
python main.py --image photo.jpg --prompt "make it black and white and crop to a square"
python main.py --image photo.jpg --prompt "add a warm vintage look" --output vintage.jpg
python main.py --image photo.jpg --prompt "sharpen and boost contrast" --trace my_trace.json
```

## Tools

| Tool | Description |
|------|-------------|
| `get_image_info` | Get dimensions, format, colorspace — always called first |
| `crop` | Crop by pixel geometry (`300x200+50+25`) or aspect ratio (`1:1`, `16:9`) |
| `rotate` | Rotate clockwise by degrees |
| `adjust_brightness` | -100 (dark) to +100 (bright) |
| `adjust_contrast` | -100 (flat) to +100 (punchy) |
| `adjust_saturation` | 0 = grayscale, 100 = unchanged, 200 = vivid |
| `sharpen` | Unsharp mask — sigma controls strength |
| `blur` | Gaussian blur — sigma controls radius |
| `grayscale` | Convert to black and white |
| `sepia` | Warm vintage tone |
| `vignette` | Darken edges (strength 1–100) |

## Trace Format

Every run writes a `trace.json`:

```json
{
  "input": "photo.jpg",
  "output": "output.jpg",
  "prompt": "make it black and white and crop to a square",
  "model": "GLM-4.6V",
  "agent_summary": "Converted to grayscale and cropped to a 1:1 square.",
  "steps": [
    {
      "tool": "get_image_info",
      "args": {},
      "success": true,
      "command": "magick identify -format ...",
      "error": ""
    },
    {
      "tool": "grayscale",
      "args": {},
      "success": true,
      "command": "magick photo.jpg -colorspace Gray photo.jpg",
      "error": ""
    },
    {
      "tool": "crop",
      "args": { "geometry": "1:1" },
      "success": true,
      "command": "magick photo.jpg -crop 300x300+50+0 +repage photo.jpg",
      "error": ""
    }
  ]
}
```

## Project Structure

```
agentic-image-editor/
├── main.py          # CLI entry point
├── agent.py         # ADK agent + LiteLLM/z.AI wiring
├── config.py        # Loads .env (API key, model, base URL)
├── tools/
│   ├── __init__.py  # Exports ALL_TOOLS list
│   ├── state.py     # Working image path + trace recorder
│   ├── magick.py    # Shared subprocess helper
│   ├── info.py      # get_image_info tool
│   ├── transform.py # crop, rotate
│   └── filters.py   # brightness, contrast, saturation, sharpen, blur, grayscale, sepia, vignette
├── requirements.txt
└── .env.example
```

## Model Provider

The agent uses **ADK + LiteLLM** to connect to any OpenAI-compatible endpoint. Default is `GLM-4.6V` via [z.AI](https://z.ai). To switch models, change `MODEL` and `API_BASE` in `.env` — no code changes needed.

The input image is base64-encoded and sent to the model alongside the prompt as a multimodal message, so the model can see the image when planning its edits.

## Safety

The input image is **never modified**. On each run, it is copied to a temporary working file. All tool operations are applied to the temp file, which is then copied to the output path when the agent finishes. The original is always preserved.
