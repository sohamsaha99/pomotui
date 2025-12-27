# Pomo

A terminal-based Pomodoro timer built with [Textual](https://textual.textualize.io/).


https://github.com/user-attachments/assets/4ba8bd93-dc14-4612-80a8-d2f61d248229


## Features

- **Timer**: Standard Pomodoro intervals (Work, Short Break, Long Break).
- **Phases**: Automatically switches between work and break phases.
- **History**: Tracks completed sessions with stats (planned vs actual time).
- **Settings**: Customizable durations for work and break intervals.
- **Keyboard Control**: efficient keyboard shortcuts for controlling the timer.
- **Premium UI**: Smooth progress bars, big timer display, and responsive layout.

## Installation

Ensure you have Python 3.10+ installed.

### Option 1: Using pipx (Recommended)

Run directly without cloning:

```bash
pipx install git+https://github.com/sohamsaha99/pomotui.git
```

### Option 2: Using uv

If you use `uv`, you can install it as a tool:

```bash
uv tool install git+https://github.com/sohamsaha99/pomotui.git
```

### Option 3: Manual Install (Clone & virtualenv)

1. Clone the repository:
   ```bash
   git clone https://github.com/sohamsaha99/pomotui.git
   cd pomotui
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the package:
   ```bash
   pip install .
   ```

## Usage

Run the application:

```bash
pomotui
```

## Key Bindings

| Key | Action |
| :--- | :--- |
| `Space` | Start / Pause / Continue |
| `e` | End current phase (Work/Break) |
| `b` | Start Break (if available) |
| `k` | Skip Break |
| `s` | Open Settings |
| `+` / `-` | Add / Subtract 1 minute |
| `]` / `[` | Add / Subtract 10 seconds |
| `Ctrl+q` | Quit |

## Configuration

Press `s` to open the settings modal where you can configure:
- Work duration
- Short break duration
- Long break duration
- Long break frequency

## License

[MIT](LICENSE)
