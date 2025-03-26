# List all available commands
default:
    @just --list

# Shorthand for common packages
PACKAGES := "dsbin dsupdater evremixes iplooker pybumper"

# Update dependencies in all packages to latest versions
update-all:
    @printf "\033[0;32mUpdating dsbase...\033[0m\n"
    @poetry up --latest
    @for pkg in {{PACKAGES}}; do \
        printf "\n\033[0;32mUpdating $pkg...\033[0m\n"; \
        cd ./packages/$pkg && poetry up --latest && cd ../..; \
    done
    @printf "\033[0;32mAll packages updated!\033[0m\n"

# Install all packages in development mode
install-all:
    @for pkg in {{PACKAGES}}; do \
        printf "\033[0;32mInstalling $pkg...\033[0m\n"; \
        cd ./packages/$pkg && poetry install && cd ../..; \
    done
    @printf "\033[0;32mInstalling dsbase...\033[0m\n"
    @poetry install
    @printf "\033[0;32mAll packages updated!\033[0m\n"

# Set up the Poetry environment for all packages
setup-env:
    @printf "\033[0;32mSetting up environment for dsbase...\033[0m\n"
    @poetry env use system
    @for pkg in {{PACKAGES}}; do \
        printf "\033[0;32mSetting up environment for $pkg...\033[0m\n"; \
        cd ./packages/$pkg && poetry env use system && cd ../..; \
    done
    @printf "\033[0;32mEnvironment setup complete!\033[0m\n"

# Create a new package
new-package name:
    @echo "Creating new package: {{name}}"
    mkdir -p packages/{{name}}/src/{{name}}
    touch packages/{{name}}/src/{{name}}/__init__.py
    cp templates/pyproject.toml packages/{{name}}/pyproject.toml
    sed -i '' 's/PACKAGE_NAME/{{name}}/g' packages/{{name}}/pyproject.toml
    @echo "Created package skeleton. Now run:"
    @echo "cd ./packages/{{name}} && poetry install && poetry env use system"
