from __future__ import annotations
from enum import IntEnum

from typing import Any

import datetime as dt
from zoneinfo import ZoneInfo as tz

class PoopEnum(IntEnum):

    DEFAULT: Any
    @classmethod
    def _missing_(cls, value):
        if value == -1:
            try:
                return cls.DEFAULT
            except:
                raise NotImplementedError("Default requested for base Enum")
        return None

    def __str__(self) -> str:
        return f"**{self.name.replace("_", " ").title()}**"

    def __repr__(self) -> str:
        return self.name.replace("_", " ").title()

class Volume(PoopEnum):
    sparse = 1
    minimal = 2
    moderate = 3
    considerable = 4
    respectable = 5
    abundant = 6
    substantial = 7
    ample = 8
    copious = 9
    profuse = 10

    DEFAULT = 5

class Texture(PoopEnum):
    liquid = 1
    soft = 2
    loose = 3
    formed = 4
    firm = 5
    hard = 6
    dense = 7
    compact = 8
    dry = 9
    rock = 10

    DEFAULT = 5

class Shape(PoopEnum):
    formless = 1
    soft_serve = 2
    ribbon = 3
    sausage = 4
    caterpillar = 5
    marble = 6

    DEFAULT = 4

class Feel(PoopEnum):
    sticky = 1
    tacky = 2
    clumpy = 3
    smooth = 4
    slippery = 5
    gritty = 6

    DEFAULT = 4

class Color(PoopEnum):
    black = 1
    dark_brown = 2
    light_brown = 3
    green_brown = 4
    yellow_brown = 5
    red_brown = 6
    green = 7
    yellow = 8
    red = 9

    DEFAULT = 3

class Smell(PoopEnum):
    odorless = 1
    mild = 2
    earthy = 3
    gross = 4
    foul = 5
    rancid = 6
    horrid = 7
    demonic = 8

    DEFAULT = 2

class LoggedEvent:

    def __init__(
                self,
                volume: Volume = Volume.DEFAULT,
                texture: Texture = Texture.DEFAULT,
                shape: Shape = Shape.DEFAULT,
                feel: Feel = Feel.DEFAULT,
                wipe_count: int = 1,
                color: Color = Color.DEFAULT,
                smell: Smell = Smell.DEFAULT,
                continuous: bool = True,
                rise: bool = True,
                event_time: dt.datetime = dt.datetime.now(tz("America/Los_Angeles"))
            ) -> None:

        """Initializes an event..."""
        self.volume = volume
        self.texture = texture
        self.shape = shape
        self.feel = feel
        self.wipe_count = wipe_count
        self.color = color
        self.smell = smell
        self.continuous = continuous
        self.rise = rise

        self.event_time = event_time

    def __repr__(self) -> str:
        return (f"Event(" +
                f"volume={self.volume}, "
                f"texture={self.texture}, "
                f"shape={self.shape}, "
                f"feel={self.feel}, "
                f"wipe_count={self.wipe_count}, "
                f"color={self.color}, "
                f"smell={self.smell}, "
                f"continuous={self.continuous}, "
                f"rise={self.rise}, "
                f"event_time={self.event_time})"
            )

    def __str__(self) -> str:
        return f"A **{'dis' if not self.continuous else ''}continuous**, " + \
            f"{self.color}, {self.volume} amount " + \
            f"with {self.texture} texture, {self.shape} shape, " + \
            f"{self.feel} feel, and a {self.smell} smell.\n" + \
            f"Required **{self.wipe_count} wipe{'s' if self.wipe_count > 1 else ''}** " + \
            f"and **did {'not' if not self.rise else ''}** result in a rise."

    @classmethod
    def from_record(cls, record) -> LoggedEvent:
        try:
            return cls(
                volume = Volume(record['volume']),
                texture = Texture(record['texture']),
                shape = Shape(record['shape']),
                feel = Feel(record['feel']),
                wipe_count = record['wipe_count'],
                color = Color(record['color']),
                smell = Smell(record['smell']),
                continuous = record['continuous'],
                rise = record['rise'],
                event_time = record['event_time']
            )
        except KeyError:
            raise KeyError("Invalid Event record passed to `from_record`.")

class Pooper:

    def __init__(self, user_id: int, logged_events: list[LoggedEvent] = []):
        self.user_id = user_id
        self.logged_events = logged_events

    def clear(self) -> Pooper:
        self.logged_events = []
        return self

    def get_paginated_events(
                self,
                max_per_page: int = 6
            ) -> dict[dt.datetime, list[list[LoggedEvent]]]:
        """
        Retrieves a dict of Master Datetime: Matrix of events with
        max events per page
        """
        paginated_events: dict[dt.datetime, list[list[LoggedEvent]]] = {}
        for event in sorted(
                self.logged_events,
                key=lambda e: dt.datetime(e.event_time.year,
                                          e.event_time.month,
                                          e.event_time.day
                                        )
            ):
            event_time = event.event_time
            master_time = dt.datetime(
                year=event_time.year,
                month=event_time.month,
                day=event_time.day,
                tzinfo=tz("America/Los_Angeles")
            )

            if master_time not in paginated_events:
                paginated_events[master_time] = [[]]

            if len(paginated_events[master_time][-1]) >= max_per_page:
                paginated_events[master_time].append([])

            paginated_events[master_time][-1].append(event)

        return paginated_events

    def __str__(self) -> str:
        return (f"Pooper(" +
                f"user_id={self.user_id}, "
                f"{len(self.logged_events)} events)"
            )

    def __repr__(self) -> str:
        return str(self)