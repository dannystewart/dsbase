from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import ClassVar


class ImpactAnalyzer:
    """Class to analyze the impact of changes in dsbase on other packages."""

    DSBASE_PATH: ClassVar[Path] = Path("src/dsbase")
    PACKAGES_PATH: ClassVar[Path] = Path("packages")
    PACKAGES: ClassVar[list[str]] = [
        "dsbin",
        "dsupdater",
        "evremixes",
        "iplooker",
        "pybumper",
    ]

    def analyze(self) -> None:
        """Run the analyzer."""
        # Get changed files
        changed_files = self.find_changed_files()
        if not changed_files:
            print("No Python files changed in dsbase.")
            return

        print("Changed files in dsbase:\n  " + "\n  ".join(changed_files))

        # Convert to module paths
        changed_modules = self.get_changed_modules(changed_files)
        print("\nChanged modules:\n  " + "\n  ".join(changed_modules))

        # Analyze impact
        impacted_packages = self.analyze_impact(changed_modules)

        if impacted_packages:
            print("\nImpacted packages:")
            for package, imports in impacted_packages.items():
                print(f"\n{package} (uses {len(imports)} affected modules):")
                for import_path in sorted(imports):
                    print(f"  - {import_path}")
        else:
            print("\nNo packages are directly impacted by these changes.")

        print("\nSummary of packages requiring new releases:")
        if impacted_packages:
            for package in impacted_packages:
                print(f"  - {package}")
        else:
            print("  None (but you should still release a new version of dsbase)")

    def find_imports_in_file(self, file_path: Path) -> set[str]:
        """Find all imports from dsbase in a given file."""
        with Path(file_path).open(encoding="utf-8") as f:
            content = f.read()

        imports = set()

        # Parse the Python file
        try:
            tree = ast.parse(content)

            # Look for imports
            for node in ast.walk(tree):
                # Regular imports: import dsbase.xyz
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name.startswith("dsbase."):
                            imports.add(name.name)

                # From imports: from dsbase import xyz
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("dsbase"):
                        imports.update(f"{node.module}.{name.name}" for name in node.names)
        except SyntaxError:
            print(f"Warning: Could not parse {file_path}")

        return imports

    def scan_package_for_imports(self, package_dir: Path) -> dict[str, set[str]]:
        """Scan a package for all dsbase imports."""
        imports_by_file = {}

        # Find all Python files
        for py_file in package_dir.glob("**/*.py"):
            imports = self.find_imports_in_file(py_file)
            if imports:
                imports_by_file[str(py_file)] = imports

        return imports_by_file

    def find_changed_files(self, base_commit: str = "HEAD") -> list[str]:
        """Find files changed in the current working directory compared to base_commit."""
        # Get the diff
        result = subprocess.run(
            ["git", "diff", "--name-only", base_commit], capture_output=True, text=True, check=False
        )
        return [
            f
            for f in result.stdout.splitlines()
            if f.endswith(".py") and f.startswith(self.DSBASE_PATH.as_posix())
        ]

    def get_changed_modules(self, changed_files: list[str]) -> set[str]:
        """Convert file paths to module paths."""
        modules = set()

        for file_path in changed_files:
            # Convert src/dsbase/xyz/abc.py to dsbase.xyz.abc
            if file_path.endswith(".py"):
                rel_path = file_path.replace("src/", "", 1).replace("/", ".").replace(".py", "")
                modules.add(rel_path)

                # Also add the parent module
                parts = rel_path.split(".")
                if len(parts) > 1:
                    parent = ".".join(parts[:-1])
                    modules.add(parent)

        return modules

    def analyze_impact(self, changed_modules: set[str]) -> dict[str, set[str]]:
        """Analyze which packages are impacted by changes to specific modules."""
        impacted_packages = {}

        for package_name in self.PACKAGES:
            package_dir = self.PACKAGES_PATH / package_name
            imports_by_file = self.scan_package_for_imports(package_dir)

            package_impacted = False
            package_imports = set()

            # Check if any of the changed modules are imported
            for imports in imports_by_file.values():
                for import_path in imports:
                    for changed_module in changed_modules:
                        # Check if the import matches or is a submodule of the changed module
                        if import_path == changed_module or import_path.startswith(
                            f"{changed_module}."
                        ):
                            package_impacted = True
                            package_imports.add(import_path)

            if package_impacted:
                impacted_packages[package_name] = package_imports

        return impacted_packages


def main() -> None:
    """Main function to analyze impact of changes in dsbase."""
    analyzer = ImpactAnalyzer()
    analyzer.analyze()


if __name__ == "__main__":
    main()
