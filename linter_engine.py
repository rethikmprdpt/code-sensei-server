import subprocess
import tempfile
from pathlib import Path


def run_python_linter(code: str):
    """
    Runs flake8 on the code string.

    Returns a list of error strings.
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp:
        temp.write(code)
        temp_path = temp.name

    try:
        # Run flake8
        # E9,F63,F7,F82 = Syntax errors and undefined names
        result = subprocess.run(  # noqa: S603
            ["flake8", temp_path, "--select=E9,F63,F7,F82", "--format=default"],  # noqa: S607
            check=False,
            capture_output=True,
            text=True,
        )

        # Parse output
        errors = []
        if result.stdout:
            for line in result.stdout.splitlines():
                # Clean up the path from the message
                clean_msg = line.replace(temp_path, "Line")
                errors.append(clean_msg)

    except Exception as e:  # noqa: BLE001
        print(f"Linter failed: {e}")
        return []
    else:
        print(errors)
        return errors
    finally:
        Path(temp_path).unlink(missing_ok=True)
