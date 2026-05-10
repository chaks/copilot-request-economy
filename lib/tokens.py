"""Parse token usage from Copilot process debug logs."""

import glob
import os
import re
from typing import Optional


def find_latest_process_log(logs_dir: str) -> Optional[str]:
    """Find the most recently modified process-*.log file in logs_dir."""
    pattern = os.path.join(logs_dir, 'process-*.log')
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def parse_tokens_from_log(log_path: str) -> dict:
    """Parse all chat.completion entries from a process log and sum token counts.

    Returns:
        {"input_tokens": int, "output_tokens": int}
    """
    try:
        with open(log_path, 'r') as f:
            content = f.read()
    except (IOError, OSError):
        return {"input_tokens": 0, "output_tokens": 0}

    input_tokens = 0
    output_tokens = 0

    # Find all JSON-like blocks that contain "chat.completion"
    # We use a two-step approach: first find chat.completion blocks, then extract tokens
    chat_block_pattern = re.compile(r'"object"\s*:\s*"chat\.completion".*?(?="object"|$)', re.DOTALL)

    prompt_pattern = re.compile(r'"prompt_tokens"\s*:\s*(\d+)')
    completion_pattern = re.compile(r'"completion_tokens"\s*:\s*(\d+)')

    for block in chat_block_pattern.finditer(content):
        block_text = block.group(0)
        prompt_match = prompt_pattern.search(block_text)
        completion_match = completion_pattern.search(block_text)

        if prompt_match:
            try:
                input_tokens += int(prompt_match.group(1))
            except (ValueError, IndexError):
                pass
        if completion_match:
            try:
                output_tokens += int(completion_match.group(1))
            except (ValueError, IndexError):
                pass

    return {"input_tokens": input_tokens, "output_tokens": output_tokens}
