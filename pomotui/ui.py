from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Center
from textual.widgets import (
        Button,
        Footer,
        Header,
        Input,
        Label,
        ProgressBar,
        Static,
        TabbedContent,
        TabPane,
        DataTable,
        Digits,
        )
from textual.screen import ModalScreen
from textual.reactive import reactive

from .models import Settings


def fmt_mmss(seconds: int) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def fmt_time(dt: datetime | None) -> str:
    if not dt:
        return "--:--"
    return dt.strftime("%H:%M:%S")


class Pill(Static):
    """Small label-like widget with nicer styling."""
    pass


class SettingsModal(ModalScreen[Settings | None]):
    """Returns Settings if saved, else None."""

    BINDINGS = [("escape", "dismiss(None)", "Close")]

    def __init__(self, initial: Settings) -> None:
        super().__init__()
        self.initial = initial

    def compose(self) -> ComposeResult:
        s = self.initial
        yield Container(
                Static("Settings", id="modal_title"),
                Vertical(
                    Horizontal(Label("Work (min):", classes="field_label"), Input(value=str(s.work_minutes), id="work")),
                    Horizontal(Label("Short break (min):", classes="field_label"), Input(value=str(s.short_break_minutes), id="short")),
                    Horizontal(Label("Long break (min):", classes="field_label"), Input(value=str(s.long_break_minutes), id="long")),
                    Horizontal(Label("Long break every (pomo):", classes="field_label"), Input(value=str(s.long_break_every), id="every")),
                    classes="modal_body",
                    ),
                Horizontal(
                    Button("Cancel", variant="default", id="cancel"),
                    Button("Save", variant="primary", id="save"),
                    classes="modal_actions",
                    ),
                id="modal_card",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return

        if event.button.id == "save":
            try:
                work = int(self.query_one("#work", Input).value.strip())
                short = int(self.query_one("#short", Input).value.strip())
                longb = int(self.query_one("#long", Input).value.strip())
                every = int(self.query_one("#every", Input).value.strip())
                # minimal sanity
                work = max(1, work)
                short = max(1, short)
                longb = max(1, longb)
                every = max(1, every)
            except ValueError:
                self.app.bell()
                return

            self.dismiss(Settings(work, short, longb, every))


class TimerView(Static):
    """Main timer panel UI elements, no business logic."""
    phase_text = reactive("Work")
    tomato_count = reactive(0)
    
    def compose(self) -> ComposeResult:
        yield Container(
                Horizontal(
                    Static("Pomodoro", id="title"),
                    Horizontal(
                        Button("Settings", id="settings", variant="default"),
                        classes="top_actions",
                        ),
                    id="topbar",
                    ),
                Vertical(
                    Horizontal(
                        Pill("Start: --:--", id="start_pill"),
                        Pill("", id="phase_pill"),
                        Pill("", id="count_pill"),
                        Pill("End: --:--", id="end_pill"),
                        id="pills",
                        ),
                    Static(classes="spacer"),
                    # New Main Display: Grid | Time
                    Horizontal(
                        # Col 2: Tomato Grid
                        Center(
                            Static("", id="tomato_bar"), 
                            classes="grid_col",
                        ),
                        # Col 3: Big Time
                        Center(
                            Digits("25:00", id="time_big"),
                            classes="digits_col",
                        ),
                        id="timer_display_row",
                    ),
                    
                    Static(classes="spacer"),

                    Horizontal(
                        Input(placeholder="What are you working on?", id="task_input"),
                        id="task_row",
                        ),
                    Static(classes="spacer"),
                    Horizontal(
                        Button("−1m", id="minus_1m", variant="default"),
                        Button("+1m", id="plus_1m", variant="default"),
                        Button("−10s", id="minus_10s", variant="default"),
                        Button("+10s", id="plus_10s", variant="default"),
                        id="adjust_row",
                        ),
                    Static(classes="spacer"),
                    Horizontal(
                        Button("Start", id="primary", variant="primary"),
                        Button("End", id="end", variant="error"),
                        Button("Skip Break", id="skip", variant="default"),
                        Button("End Session", id="end_session", variant="error"),
                        id="buttons_row",
                        ),

                    id="timer_panel",
                    ),
                )

    def update_big_time(self, mmss: str) -> None:
        self.query_one("#time_big", Digits).update(mmss)

    def update_phase(self, text: str) -> None:
        self.query_one("#phase_pill", Pill).update(text)

    def update_count(self, text: str) -> None:
        self.query_one("#count_pill", Pill).update(text)

    def update_start_end(self, start: str, end: str) -> None:
        self.query_one("#start_pill", Pill).update(f"Start: {start}")
        self.query_one("#end_pill", Pill).update(f"End: {end}")

    def set_progress(self, value: int, total: int) -> None:
        # value = elapsed seconds, total = planned seconds
        # 100 tomatoes in 10x10 grid
        total = max(1, total)
        percent = max(0, min(value / total, 1.0))
        
        total_tomatoes = 100
        filled_count = int(percent * total_tomatoes)
        
        # Build grid string
        # We need 10 lines, each with 10 chars/tomatoes + spaces
        lines = []
        for row in range(10):
            line_chars = []
            for col in range(10):
                idx = row * 10 + col
                if idx < filled_count:
                    line_chars.append("🍅")
                else:
                    line_chars.append("🌱") # use seedling as placeholder for empty/growing
            lines.append(" ".join(line_chars))
            
        final_str = "\n".join(lines)
        self.query_one("#tomato_bar", Static).update(final_str)

    def set_primary_label(self, text: str) -> None:
        self.query_one("#primary", Button).label = text

    def show_button(self, button_id: str, show: bool) -> None:
        btn = self.query_one(f"#{button_id}", Button)
        btn.display = show

    def set_task_value(self, value: str) -> None:
        self.query_one("#task_input", Input).value = value


class HistoryView(Static):
    def compose(self) -> ComposeResult:
        yield Container(
                Static("History", id="history_title"),
                Static("You'll be able to customize what appears here later.", id="history_subtitle"),
                DataTable(id="history_table"),
                id="history_panel",
                )

    def setup_table(self) -> None:
        table = self.query_one("#history_table", DataTable)
        table.clear(columns=True)
        table.add_columns("#", "Phase", "Task", "Start", "End", "Planned", "Actual", "Status", "Actions")
        table.zebra_stripes = True

    def add_item(
            self,
            idx: int,
            phase: str,
            task: str,
            start: str,
            end: str,
            planned: str,
            actual: str,
            status: str,
            ) -> None:
        table = self.query_one("#history_table", DataTable)
        table.add_row(str(idx), phase, task, start, end, planned, actual, status, "❌", key=str(idx))

