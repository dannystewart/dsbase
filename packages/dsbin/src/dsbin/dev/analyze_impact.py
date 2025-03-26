from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from dsbase import ArgParser, LocalLogger
from dsbase.text import color_print

if TYPE_CHECKING:
    import argparse
    from logging import Logger


class ImpactAnalyzer:
    """Analyzes the impact of changes in dsbase on dependent packages."""

    DSBASE_PATH: ClassVar[Path] = Path("src/dsbase")
    PACKAGES_PATH: ClassVar[Path] = Path("packages")
    PACKAGES: ClassVar[list[str]] = [
        "dsbin",
        "dsupdater",
        "evremixes",
        "iplooker",
        "pybumper",
    ]

    def __init__(
        self,
        base_commit: str = "HEAD",
        verbose: bool = False,
        packages: list[str] | None = None,
    ) -> None:
        self.logger: Logger = LocalLogger().get_logger(simple=True)
        self.base_commit = base_commit
        self.verbose = verbose
        self.packages = packages or self.PACKAGES
        self.changed_files: list[str] = []
        self.changed_modules: set[str] = set()
        self.impacted_packages: dict[str, set[str]] = {}

        # Cache for imports to avoid rescanning
        self._imports_cache: dict[str, dict[str, set[str]]] = {}

    def analyze(self) -> dict[str, set[str]]:
        """Run the analysis and display results.

        Returns:
            Dictionary of impacted packages and their affected imports.
        """
        # Get changed files
        self.changed_files = self.find_changed_files(self.base_commit)
        if not self.changed_files:
            self.logger.info("No Python files changed in dsbase. You're good to go!")
            return {}

        color_print("\n=== Changes Detected ===\n", "yellow")

        color_print("Changed files in dsbase:", "blue")
        for file in self.changed_files:
            print(f"  {file}")

        # Convert to module paths
        self.changed_modules = self.get_changed_modules(self.changed_files)
        color_print("\nChanged modules:", "blue")
        for module in sorted(self.changed_modules):
            print(f"  {module}")

        # Analyze impact
        self.impacted_packages = self.analyze_impact(self.changed_modules)

        if self.impacted_packages:
            color_print("\n=== Impacted Packages ===", "yellow")
            for package, imports in self.impacted_packages.items():
                color_print(f"\n{package} (uses {len(imports)} affected modules):", "cyan")
                for import_path in sorted(imports):
                    print(f"  - {import_path}")
        else:
            self.logger.info("No packages are directly impacted by these changes.")

        color_print("\nPackages requiring new releases:", "yellow")
        if self.impacted_packages:
            for package in self.impacted_packages:
                color_print(f"  - {package}", "green")
        else:
            color_print("  None (but you should still release a new version of dsbase)", "yellow")

        return self.impacted_packages

    def find_imports_in_file(self, file_path: Path) -> set[str]:
        """Find all imports from dsbase in a given file."""
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError) as e:
            self.logger.warning("Couldn't read %s: %s", file_path, str(e))
            return set()

        imports = set()

        try:  # Parse the Python file
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
            self.logger.warning("Couldn't parse %s as a valid Python file.", file_path)

        return imports

    def scan_package_for_imports(self, package_name: str) -> dict[str, set[str]]:
        """Scan a package for all dsbase imports.

        Returns:
            Dictionary mapping file paths to sets of imports.
        """
        # Use cached results if available
        if package_name in self._imports_cache:
            return self._imports_cache[package_name]

        package_dir = self.PACKAGES_PATH / package_name
        imports_by_file = {}

        if self.verbose:
            color_print(f"Scanning {package_name} for imports...", "blue")

        # Find all Python files
        for py_file in package_dir.glob("**/*.py"):
            imports = self.find_imports_in_file(py_file)
            if imports:
                imports_by_file[str(py_file)] = imports
                if self.verbose:
                    color_print(
                        f"  Found {len(imports)} imports in {py_file.relative_to(package_dir)}",
                        "cyan",
                    )

        # Cache the results
        self._imports_cache[package_name] = imports_by_file
        return imports_by_file

    def find_changed_files(self, base_commit: str = "HEAD") -> list[str]:
        """Find files changed in the current working directory compared to base_commit."""
        try:
            # Get the diff
            result = subprocess.run(
                ["git", "diff", "--name-only", base_commit],
                capture_output=True,
                text=True,
                check=True,
            )
            return [
                f
                for f in result.stdout.splitlines()
                if f.endswith(".py") and f.startswith(self.DSBASE_PATH.as_posix())
            ]
        except subprocess.CalledProcessError as e:
            self.logger.error("Error running git diff: %s", str(e))
            return []

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

        for package_name in self.packages:
            imports_by_file = self.scan_package_for_imports(package_name)
            package_imports = set()

            # Check if any of the changed modules are imported
            for imports in imports_by_file.values():
                for import_path in imports:
                    for changed_module in changed_modules:
                        # Check if the import matches or is a submodule of the changed module
                        if import_path == changed_module or import_path.startswith(
                            f"{changed_module}."
                        ):
                            package_imports.add(import_path)

            if package_imports:
                impacted_packages[package_name] = package_imports

        return impacted_packages

    @classmethod
    def discover_packages(cls) -> list[str]:
        """Discover available packages in the packages directory."""
        return [p.name for p in cls.PACKAGES_PATH.glob("*") if (p / "pyproject.toml").exists()]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = ArgParser(description="Analyze the impact of changes in dsbase on dependent packages.")
    parser.add_argument(
        "-b",
        "--base",
        default="HEAD",
        help="Git reference to compare against (default: HEAD)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "-d",
        "--discover",
        action="store_true",
        help="Auto-discover packages instead of using predefined list",
    )
    return parser.parse_args()


def main() -> None:
    """Main function to analyze impact of changes in dsbase."""
    args = parse_args()

    # Optionally discover packages
    packages = None
    if args.discover:
        packages = ImpactAnalyzer.discover_packages()
        color_print(f"Discovered packages: {', '.join(packages)}", "blue")

    analyzer = ImpactAnalyzer(base_commit=args.base, verbose=args.verbose, packages=packages)
    analyzer.analyze()


if __name__ == "__main__":
    main()
