"""Deploy a SAM bundle without dropping its configured template parameters.

SAM replaces config-file overrides when any CLI override is supplied.
This wrapper reads the default environment's global and deploy settings.
It retains those values and adds one UTC deployment timestamp.
Arguments are passed directly to SAM, preserving empty values and spaces.
The Lambda Makefiles use this wrapper after building and checking bundles.
"""

import argparse
import json
import shlex
import subprocess
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

DEFAULT = "default"
GLOBAL = "global"
DEPLOY = "deploy"
PARAMETERS = "parameters"
OVERRIDES = "parameter_overrides"
TIMESTAMP = "DeploymentTimestamp"


class Deployment(BaseModel):
    """Resolved source configuration and the complete template override set."""

    config: Path
    template: Path
    parameters: dict[str, str]

    @classmethod
    def load(cls, config: Path, template: Path, timestamp: str | None = None):
        """Read SAM's default config environment and preserve command precedence."""
        data = tomllib.loads(config.read_text())[DEFAULT]
        settings = {**data.get(GLOBAL, {}).get(PARAMETERS, {}),
                    **data.get(DEPLOY, {}).get(PARAMETERS, {})}
        raw = settings.get(OVERRIDES, "")
        tokens = shlex.split(raw) if isinstance(raw, str) else [token for entry in raw for token in shlex.split(entry)]
        parameters = {}
        for token in tokens:
            key, separator, value = token.partition("=")
            if not separator or not key.isalnum():
                raise ValueError("Invalid SAM template parameter override")
            parameters[key] = value
        parameters[TIMESTAMP] = timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        return cls(config=config.resolve(), template=template.resolve(), parameters=parameters)

    def command(self) -> list[str]:
        """Quote values for SAM's parameter parser, without invoking a shell."""
        return ["sam", "deploy", "--config-file", str(self.config), "--template-file", str(self.template),
                "--no-confirm-changeset", "--parameter-overrides",
                *(f"{key}={json.dumps(value)}" for key, value in self.parameters.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    args = parser.parse_args()
    subprocess.run(Deployment.load(args.config, args.template).command(), check=True)


if __name__ == "__main__":
    main()
