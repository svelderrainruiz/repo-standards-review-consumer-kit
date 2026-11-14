"""Keep only the CI integration for the chosen forge."""

import json
import shutil
from pathlib import Path

FORGE = json.loads({{ cookiecutter.forge | tojson | tojson }})

shutil.rmtree(Path.cwd() / (".gitlab" if FORGE == "github" else ".github"))
