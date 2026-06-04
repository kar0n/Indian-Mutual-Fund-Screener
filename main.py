"""Main entry point script for executing the Mutual Fund Quant Screener."""

import logging
import sys

# Production Guardrail: Suppress internal thread context warnings before modules compile
logging.basicConfig(level=logging.ERROR)
streamlit_loggers = [
    logging.getLogger(name)
    for name in logging.root.manager.loggerDict
    if "streamlit" in name
]
for logger in streamlit_loggers:
    logger.setLevel(logging.ERROR)

from ui import StreamlitDashboard

def main():
    StreamlitDashboard.render()

if __name__ == "__main__":
    main()