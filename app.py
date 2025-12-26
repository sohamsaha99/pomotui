from datetime import datetime, timedelta

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Button, Input
from textual.reactive import reactive

from .models import Session, Phase, TimerState, HistoryItem, Settings
from .ui import TimerView, HistoryView, SettingsModal, fmt_mmss, fmt_time
from .storage import load_data, save_data


class PomodoroApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
            ("space", "toggle_primary", "Start/Pause/Continue"),
            ("e", "end_phase", "End"),
            ("b", "start_break", "Start Break"),
            ("k", "skip_break", "Skip Break"),
            ("s", "open_settings", "Settings"),
            ("+", "add_minute", "+1m"),
            ("-", "sub_minute", "-1m"),
            ("]", "add_10s", "+10s"),
            ("[", "sub_10s", "-10s"),
            ]

    session: Session
    tick_handle = None

    # history
    history: list[HistoryItem] = []
    history_index = reactive(0)

    def __init__(self) -> None:
        super().__init__()
        self.session = Session()
        
        # Load from storage
        loaded_settings, loaded_history = load_data()
        self.session.settings = loaded_settings
        self.history = loaded_history
        if self.history:
            self.history_index = self.history[-1].index
        
        self.session.current_phase = Phase.WORK
        self._reset_phase_to_defaults()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="timer"):
            with TabPane("Timer", id="timer"):
                yield TimerView(id="timer_view")
            with TabPane("History", id="history"):
                yield HistoryView(id="history_view")
        yield Footer()

    def on_mount(self) -> None:
        self.tick_handle = self.set_interval(0.25, self._tick)  # smooth progress updates
        self.query_one("#history_view", HistoryView).setup_table()
        
        # Populate history view
        for item in self.history:
            self._push_history_row(item)
            
        self._sync_ui()

    # ----------------------------
    # Phase + timer mechanics
    # ----------------------------

    def _reset_phase_to_defaults(self) -> None:
        secs = self.session.compute_default_seconds_for_phase()
        self.session.planned_seconds = secs
        self.session.remaining_seconds = secs
        self.session.start_at = None
        self.session.end_at = None
        self.session.state = TimerState.IDLE

    def _start(self) -> None:
        s = self.session
        now = datetime.now()
        s.start_at = now
        s.end_at = now + timedelta(seconds=s.remaining_seconds)
        s.state = TimerState.RUNNING

    def _pause(self) -> None:
        s = self.session
        if s.state != TimerState.RUNNING or not s.end_at:
            return
        now = datetime.now()
        s.remaining_seconds = max(0, int((s.end_at - now).total_seconds()))
        s.end_at = None
        s.state = TimerState.PAUSED

    def _resume(self) -> None:
        s = self.session
        if s.state != TimerState.PAUSED:
            return
        now = datetime.now()
        if not s.start_at:
            s.start_at = now
        s.end_at = now + timedelta(seconds=s.remaining_seconds)
        s.state = TimerState.RUNNING

    def _finish_current_phase(self, status: str) -> None:
        """Finish work/break and transition according to spec."""
        s = self.session
        now = datetime.now()

        # Determine actual seconds worked in this phase
        planned = s.planned_seconds
        actual = planned - max(0, s.remaining_seconds)

        # If running, compute remaining from end_at to avoid drift
        if s.state == TimerState.RUNNING and s.end_at is not None:
            actual = planned - max(0, int((s.end_at - now).total_seconds()))

        # history record
        if s.start_at is None:
            s.start_at = now
        end_time = now
        task = (s.task_name or "").strip()
        if not task:
            task = "—"

        self.history_index += 1
        self.history.append(
                HistoryItem(
                    index=self.history_index,
                    phase=s.current_phase.value,
                    task=task,
                    start=s.start_at,
                    end=end_time,
                    planned_seconds=planned,
                    actual_seconds=max(0, actual),
                    status=status,
                    )
                )
        self._push_history_row(self.history[-1])

        # Transition logic
        if s.current_phase == Phase.WORK:
            if status in ("completed", "ended"):
                s.pomodoros_completed += 1
            s.current_phase = Phase.BREAK
        else:
            # break finished or skipped -> back to work
            s.current_phase = Phase.WORK

        # Reset to next phase defaults
        s.task_name = s.task_name if s.current_phase == Phase.WORK else s.task_name  # keep task unless you prefer clearing
        self._reset_phase_to_defaults()
        
        # Save data
        save_data(s.settings, self.history)
        
        self._sync_ui()

    def _push_history_row(self, item: HistoryItem) -> None:
        hv = self.query_one("#history_view", HistoryView)
        hv.add_item(
                idx=item.index,
                phase=item.phase,
                task=item.task,
                start=item.start.strftime("%Y-%m-%d %H:%M:%S"),
                end=item.end.strftime("%Y-%m-%d %H:%M:%S"),
                planned=fmt_mmss(item.planned_seconds),
                actual=fmt_mmss(item.actual_seconds),
                status=item.status,
                )

    def _tick(self) -> None:
        s = self.session
        if s.state == TimerState.RUNNING and s.end_at is not None:
            now = datetime.now()
            rem = int((s.end_at - now).total_seconds())
            s.remaining_seconds = max(0, rem)
            if s.remaining_seconds <= 0:
                # timer ran out
                self._finish_current_phase(status="completed")
            else:
                self._sync_ui(progress_only=True)

    # ----------------------------
    # Time adjustments (keeps end_at consistent)
    # ----------------------------

    def _adjust_time(self, delta_seconds: int) -> None:
        s = self.session
        # planned duration changes too (so progress bar scaling stays sensible)
        new_planned = max(10, s.planned_seconds + delta_seconds)
        planned_delta = new_planned - s.planned_seconds
        s.planned_seconds = new_planned

        if s.state == TimerState.RUNNING and s.end_at is not None:
            # keep end time consistent by shifting end_at
            s.end_at = s.end_at + timedelta(seconds=planned_delta)
            # remaining recomputed on next tick, but update immediately for responsiveness
            now = datetime.now()
            s.remaining_seconds = max(0, int((s.end_at - now).total_seconds()))
        else:
            # idle/paused: just adjust remaining, clamp to planned
            s.remaining_seconds = max(0, min(s.planned_seconds, s.remaining_seconds + planned_delta))

        self._sync_ui()

    # ----------------------------
    # UI sync + button states
    # ----------------------------

    def _sync_ui(self, progress_only: bool = False) -> None:
        s = self.session
        tv = self.query_one("#timer_view", TimerView)

        # phase pill + count pill
        phase_label = "Work" if s.current_phase == Phase.WORK else ("Long Break" if s.is_long_break_due() else "Break")
        tv.update_phase(phase_label)
        tv.update_count(f"Pomos: {s.pomodoros_completed}")

        # big time
        tv.update_big_time(fmt_mmss(s.remaining_seconds))

        # start/end pills
        start_dt = s.start_at if s.state != TimerState.IDLE else None
        end_dt = s.end_at if s.state == TimerState.RUNNING else (None if s.state == TimerState.IDLE else None)
        # If paused, show projected end if resumed immediately? (optional)
        if s.state == TimerState.PAUSED:
            end_dt = datetime.now() + timedelta(seconds=s.remaining_seconds)
        tv.update_start_end(fmt_time(start_dt), fmt_time(end_dt))

        # progress bar
        elapsed = max(0, s.planned_seconds - s.remaining_seconds)
        tv.set_progress(elapsed, s.planned_seconds)

        if progress_only:
            return

        # Task input handling
        tv.set_task_value(s.task_name)

        # Buttons per spec
        # Hide all optional buttons first
        tv.show_button("end", False)
        tv.show_button("skip", False)
        tv.show_button("end_session", False)

        primary = tv.query_one("#primary", Button)

        if s.current_phase == Phase.WORK:
            if s.state == TimerState.IDLE:
                tv.set_primary_label("Start")
                tv.show_button("end", False)
            elif s.state == TimerState.RUNNING:
                tv.set_primary_label("Pause")
            elif s.state == TimerState.PAUSED:
                tv.set_primary_label("Continue")
                tv.show_button("end", True)  # appears on pause
        else:
            # break phase
            if s.state == TimerState.IDLE:
                tv.set_primary_label("Start Break")
                tv.show_button("skip", True)
                tv.show_button("end_session", True)
            elif s.state == TimerState.RUNNING:
                tv.set_primary_label("Pause")
                tv.show_button("end", False)
                tv.show_button("skip", False)
                tv.show_button("end_session", False)
            elif s.state == TimerState.PAUSED:
                tv.set_primary_label("Continue")
                tv.show_button("end", True)  # end break early if desired

        # Task row: only really relevant for work, but keep it visible (premium, minimal)
        # If you want it hidden during break, set display here.

    # ----------------------------
    # Events
    # ----------------------------

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "task_input":
            self.session.task_name = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "settings":
            self.action_open_settings()
            return
        if bid == "primary":
            self.action_toggle_primary()
            return
        if bid == "end":
            self.action_end_phase()
            return
        if bid == "skip":
            self.action_skip_break()
            return
        if bid == "end_session":
            self.action_end_session()
            return
        if bid == "minus_1m":
            self.action_sub_minute()
            return
        if bid == "plus_1m":
            self.action_add_minute()
            return
        if bid == "minus_10s":
            self.action_sub_10s()
            return
        if bid == "plus_10s":
            self.action_add_10s()
            return

    # ----------------------------
    # Actions / keybinds
    # ----------------------------

    def action_toggle_primary(self) -> None:
        s = self.session
        if s.state == TimerState.IDLE:
            # Start work or start break
            self._start()
        elif s.state == TimerState.RUNNING:
            self._pause()
        elif s.state == TimerState.PAUSED:
            self._resume()
        self._sync_ui()

    def action_end_phase(self) -> None:
        s = self.session
        if s.current_phase == Phase.WORK:
            # "End" while paused or running counts as ended
            self._finish_current_phase(status="ended")
        else:
            # ending break early is "ended"
            self._finish_current_phase(status="ended")

    def action_start_break(self) -> None:
        s = self.session
        if s.current_phase != Phase.BREAK or s.state != TimerState.IDLE:
            self.app.bell()
            return
        self._start()
        self._sync_ui()

    def action_skip_break(self) -> None:
        s = self.session
        if s.current_phase != Phase.BREAK or s.state != TimerState.IDLE:
            self.app.bell()
            return
        # record a skipped break for history consistency
        self._finish_current_phase(status="skipped")

    def action_end_session(self) -> None:
        # Minimal: reset to a fresh work phase, keep history
        self.session.current_phase = Phase.WORK
        self.session.state = TimerState.IDLE
        self._reset_phase_to_defaults()
        self._sync_ui()

    def action_open_settings(self) -> None:
        self.push_screen(SettingsModal(self.session.settings), self._on_settings_closed)

    def _on_settings_closed(self, result: Settings | None) -> None:
        if result is None:
            return
        self.session.settings = result

        if self.session.state == TimerState.IDLE:
            self._reset_phase_to_defaults()
        
        save_data(self.session.settings, self.history)
        self._sync_ui()

    # time adjustments
    def action_add_minute(self) -> None:
        self._adjust_time(60)

    def action_sub_minute(self) -> None:
        self._adjust_time(-60)

    def action_add_10s(self) -> None:
        self._adjust_time(10)

    def action_sub_10s(self) -> None:
        self._adjust_time(-10)


if __name__ == "__main__":
    PomodoroApp().run()

