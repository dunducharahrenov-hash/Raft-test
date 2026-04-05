import subprocess
import sys
from pathlib import Path


TEST_CASES = [
    ("TC-01", "Backend Python Developer"),
    ("TC-02", "ML Engineer"),
    ("TC-03", "iOS Developer (Swift)"),
]


def main():
    base_dir = Path(__file__).resolve().parent
    for case_id, role in TEST_CASES:
        output_dir = base_dir / "examples" / case_id
        output_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            str(base_dir / "main.py"),
            "--role",
            role,
            "--output-dir",
            str(output_dir),
            "--force",
        ]
        print(f"Running {case_id}: {role}")
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
