"""Optional launcher: `python main.py` starts the Streamlit app."""

import subprocess
import sys


if __name__ == "__main__":
    raise SystemExit(
        subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py"])
    )
