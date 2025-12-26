# Pomo

A premium terminal-based Pomodoro timer built with [Textual](https://textual.textualize.io/).

## Features

- **Timer**: Standard Pomodoro intervals (Work, Short Break, Long Break).
- **Phases**: Automatically switches between work and break phases.
- **History**: Tracks completed sessions with stats (planned vs actual time).
- **Settings**: Customizable durations for work and break intervals.
- **Keyboard Control**: efficient keyboard shortcuts for controlling the timer.
- **Premium UI**: Smooth progress bars, big timer display, and responsive layout.

## Installation

Ensure you have Python 3.10+ installed.

1.  Clone the repository.
2.  Install dependencies (it is recommended to use a virtual environment):

    ```bash
    pip install -r requirements.txt
    ```

    *(Note: Check `requirements.txt` for dependencies.)*

## Usage

Run the application using Python:

```bash
python -m pomotui
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
