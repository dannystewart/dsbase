# Polykit

A delightful Python utility toolkit that brings power and personality to your projects.

[![PyPI version](https://img.shields.io/pypi/v/polykit.svg)](https://pypi.org/project/polykit/)
[![Python versions](https://img.shields.io/pypi/pyversions/polykit.svg)](https://pypi.org/project/polykit/)
[![PyPI downloads](https://img.shields.io/pypi/dm/polykit.svg)](https://pypi.org/project/polykit/)
[![License](https://img.shields.io/pypi/l/polykit.svg)](https://github.com/dannystewart/polykit/blob/main/LICENSE)

Polykit contains various utilities refined through years of practical development, offering elegant solutions for common programming tasks. From sophisticated logging to environment variable management, from path handling to text processing, Polykit makes everyday coding more joyful and productive.

## Installation

```bash
pip install polykit
```

## Core Components

### Elegant Logging with Logician

Polykit includes a beautiful, customizable logging system that you'll actually enjoy using:

```python
from polykit.log import Logician

logger = Logician.get_logger(__name__)
logger.info("Starting process with %s items", count)
logger.success("All items processed successfully!")
```

Features include colorized output, custom log levels, context managers, and much more.

### Environment Variable Management

Declaratively define and validate environment variables:

```python
from polykit.env import Enviromancer

env = Enviromancer()
env.add_var("API_KEY", required=True)
env.add_var("DEBUG", default="False", transform=bool)
env.add_var("MAX_CONNECTIONS", default="10", transform=int)

# Access anywhere
api_key = env.API_KEY
```

### Cross-Platform Path Management

Easily work with application directories across operating systems:

```python
from polykit.paths import PathKeeper

paths = PathKeeper("myapp", app_author="MyCompany")

config_file = paths.from_config("settings.json")  # ~/.config/myapp/settings.json on Linux
cache_dir = paths.from_cache("responses")         # ~/Library/Caches/myapp/responses on macOS
```

### Command Line Interface Tools

Build better command-line tools with minimal effort:

```python
from polykit.cli import ArgParser

parser = ArgParser(description="My awesome tool")
parser.add_argument("--input", "-i", help="Input file")
args = parser.parse_args()
```

### Smart Text Processing

Powerful text manipulation and formatting tools:

```python
from polykit.formatters import Text

# Convert between formats
html = Text.markdown_to_html("# Hello World")

# Format text with color
colored_text = Text.color("Important message", color="red", style=["bold"])
Text.print_color("Success!", color="green")

# Smart text operations
Text.truncate("This is a very long text...", chars=20)  # "This is a very lon..."
Text.plural("item", 5, with_count=True)  # "5 items"
Text.format_duration(hours=2, minutes=30)  # "2 hours and 30 minutes"
```

### Intelligent Time Handling

Work with times in a natural, human-friendly way:

```python
from polykit.time import Time, TZ

# Parse natural language time expressions
meeting = Time.parse("3pm tomorrow")
deadline = Time.parse("Friday at 5pm")

# Format times in a human-readable way
Time.get_pretty_time(meeting)  # "tomorrow at 3:00 PM"
Time.get_pretty_time(deadline, capitalize=True)  # "Friday at 5:00 PM"

# Convert durations to readable text
Time.convert_sec_to_interval(3665)  # "1 hour, 1 minute and 5 seconds"
```

### Walking Man, Your Friendly Loading Animation `<('-'<)`

Meet Walking Man, the charming character who keeps your users company during long-running operations:

```python
from polykit.cli import walking_man

# As a context manager
with walking_man("Loading your data..."):
    time.sleep(5)  # Your long-running operation here

# Customize his appearance (walk faster, in yellow!)
with walking_man("Processing...", color="yellow", speed=0.1):
    process_data()
```

Walking Man appears when you need him and cleans up after himself when the task is done!

## Additional Utilities

Polykit also includes:

- Thread-safe `Singleton` metaclass
- File comparison and diff tools
- Helpers for shell operations

## License

This project is licensed under the [MIT license](https://github.com/dannystewart/polykit/blob/main/LICENSE). Contributions are welcome!
