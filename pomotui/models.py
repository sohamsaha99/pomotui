from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Literal


class Phase(str, Enum):
    WORK = "work"
    BREAK = "break"


class TimerState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class Settings:
    work_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    long_break_every: int = 4  # after N work pomodoros


@dataclass
class HistoryItem:
    index: int
    phase: Literal["work", "break"]
    task: str
    start: datetime
    end: datetime
    planned_seconds: int
    actual_seconds: int
    status: Literal["completed", "ended", "skipped"]


@dataclass
class Session:
    settings: Settings = field(default_factory=Settings)
    pomodoros_completed: int = 0
    current_phase: Phase = Phase.WORK

    task_name: str = ""

    # timer fields
    state: TimerState = TimerState.IDLE
    planned_seconds: int = 25 * 60
    remaining_seconds: int = 25 * 60

    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None  # authoritative while RUNNING

    def compute_default_seconds_for_phase(self) -> int:
        s = self.settings
        if self.current_phase == Phase.WORK:
            return s.work_minutes * 60
        # break
        if self.is_long_break_due():
            return s.long_break_minutes * 60
        return s.short_break_minutes * 60

    def is_long_break_due(self) -> bool:
        s = self.settings
        if s.long_break_every <= 0:
            return False
        # long break after N completed pomodoros, i.e. before break that follows Nth work
        return (self.pomodoros_completed > 0) and (self.pomodoros_completed % s.long_break_every == 0)

