#!/usr/bin/env python
"""Script to run Gradio UI."""

import sys
from pathlib import Path
from src.llm._gradio_app import create_chatbot_interface
from src.config import get_settings

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

settings = get_settings()


def main():
    """Run Gradio interface."""
    demo = create_chatbot_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


if __name__ == "__main__":
    main()
