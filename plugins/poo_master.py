import logging

import novus as n
from novus import types as t
from novus.ext import client, database as db

import datetime as dt
from zoneinfo import ZoneInfo as tz
import random

from .utils.poo_objects import Volume, Texture, Shape, Feel, \
                                    Color, Smell, LoggedEvent
from .utils.poo_cache_utils import get_pooper, poo_modify_cache_db, \
                                    parse_datetime
from .utils.autocomplete import VOLUME_OPTIONS, TEXTURE_OPTIONS, \
                                SHAPE_OPTIONS, FEEL_OPTIONS, \
                                    COLOR_OPTIONS, SMELL_OPTIONS, BOOLEAN_OPTIONS

log = logging.getLogger("plugins.poo_master")

class PooMaster(client.Plugin):

    @client.event.filtered_component(
        r"LOG SCROLL\|\d+\|\d+\|\d+\|\d+\|\d+\|(\+|-)\d+"
    )
    async def log_scrolled(self, ctx: t.ComponentI):
        """Pinged when a scroll button is clicked"""

        _, user_id, year, month, day, current_page, direction = ctx.data.custom_id.split("|")

        user_id = int(user_id)
        year, month, day = int(year), int(month), int(day)
        current_page = int(current_page)
        direction = int(direction)

        if user_id != ctx.user.id:
            return

        if not ctx.message:
            return

        pooper = get_pooper(ctx.user.id)

        paginated_events: dict[dt.datetime, list[list[LoggedEvent]]]
        paginated_events = pooper.get_paginated_events()

        new_formatted_page, final_page = self.get_formatted_page(
            paginated_events, year, month, day, current_page + direction
        )

        await ctx.update(
            embeds=[new_formatted_page],
            components=self.get_scroll_buttons(
                ctx.user.id, year, month, day,
                current_page + direction, final_page
            )
        )

    @client.event.filtered_component(r"LOG CANCEL\|\d+")
    async def log_cancelled(self, ctx: t.ComponentI):
        """Pinged when a user cancels log viewing"""

        _, user_id = ctx.data.custom_id.split("|")
        user_id = int(user_id)

        if user_id != ctx.user.id:
            return

        if ctx.message:
            await ctx.message.delete()

    @client.command(
        name="log add",
        options = [
            n.ApplicationCommandOption(
                name="event_time",
                type=n.ApplicationOptionType.string,
                description=f"The YYYY/MM/DD HH:MM:SS AM/PM of the event (defaults to right now)",
                required=False
            ),
            n.ApplicationCommandOption(
                name="volume",
                type=n.ApplicationOptionType.integer,
                description=f"The relative size of the package (default {Volume.DEFAULT})",
                choices=VOLUME_OPTIONS,
                required=False
            ),
            n.ApplicationCommandOption(
                name="texture",
                type=n.ApplicationOptionType.integer,
                description=f"The texture of the package's components (default {Texture.DEFAULT})",
                choices=TEXTURE_OPTIONS,
                required=False
            ),
            n.ApplicationCommandOption(
                name="shape",
                type=n.ApplicationOptionType.integer,
                description=f"The shape of the package's componenets (default {Shape.DEFAULT})",
                choices=SHAPE_OPTIONS,
                required=False
            ),
            n.ApplicationCommandOption(
                name="feel",
                type=n.ApplicationOptionType.integer,
                description=f"How the package felt while delivering (default {Feel.DEFAULT})",
                choices=FEEL_OPTIONS,
                required=False
            ),
            n.ApplicationCommandOption(
                name="wipe_count",
                type=n.ApplicationOptionType.integer,
                description="How many wipes it took to clear the beast (default **1**)",
                required=False,
                min_value=0,
                max_value=32_700
            ),
            n.ApplicationCommandOption(
                name="color",
                type=n.ApplicationOptionType.integer,
                description=f"The color of the package's components (default {Color.DEFAULT})",
                choices=COLOR_OPTIONS,
                required=False
            ),
            n.ApplicationCommandOption(
                name="smell",
                type=n.ApplicationOptionType.integer,
                description=f"The smell of the package (default {Smell.DEFAULT})",
                choices=SMELL_OPTIONS,
                required=False
            ),
            n.ApplicationCommandOption(
                name="continuous",
                type=n.ApplicationOptionType.integer,
                description="Was the package delivered in one fell swoop? (default **Yes**)",
                choices=BOOLEAN_OPTIONS,
                required=False
            ),
            n.ApplicationCommandOption(
                name="rise",
                type=n.ApplicationOptionType.integer,
                description="Did the package rise above the water line? (default **Yes**)",
                choices=BOOLEAN_OPTIONS,
                required=False
            ),
            n.ApplicationCommandOption(
                name="hide",
                type=n.ApplicationOptionType.integer,
                description="Whether or not to hide your crime (default **No**)",
                choices=BOOLEAN_OPTIONS,
                required=False
            ),
        ]
    )
    async def add_event(
                self,
                ctx: t.CommandI,
                event_time: str | dt.datetime = dt.datetime.now(
                    tz("America/Los_Angeles")
                ),
                volume: int | Volume = Volume.DEFAULT,
                texture: int | Texture = Texture.DEFAULT,
                shape: int | Shape = Shape.DEFAULT,
                feel: int | Feel = Feel.DEFAULT,
                wipe_count: int = 1,
                color: int | Color = Color.DEFAULT,
                smell: int | Smell = Smell.DEFAULT,
                continuous: int | bool = True,
                rise: int | bool = True,
                hide: int | bool = False
            ) -> None:
        """Logs an event"""

        # Fix our input variables and create the event object
        try:
            event_time = parse_datetime(event_time)
        except:
            return await ctx.send("Ran into an error parsing that time.")
        volume = Volume(volume)
        texture = Texture(texture)
        shape = Shape(shape)
        feel = Feel(feel)
        color = Color(color)
        smell = Smell(smell)

        # TODO
        if continuous == -1:
            continuous = False
        else:
            continuous = bool(continuous)
        if rise == -1:
            rise = False
        else:
            rise = bool(rise)
        if hide == -1:
            hide = False
        else:
            hide = bool(hide)

        logged_event = LoggedEvent(
            volume,
            texture,
            shape,
            feel,
            wipe_count,
            color,
            smell,
            continuous,
            rise,
            event_time
        )

        log.info(f"Attempting to log '{repr(logged_event)}' to {ctx.user.id}")

        # Update the cache and database
        async with db.Database.acquire() as conn:
            success = await poo_modify_cache_db(
                ctx.user.id,
                volume,
                texture,
                shape,
                feel,
                wipe_count,
                color,
                smell,
                continuous,
                rise,
                event_time,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble logging that event", ephemeral=hide
            )

        # Send a confirmation message
        await ctx.send(
            self.get_random_response(),
            ephemeral=hide
        )

    @client.command(
        name="log delete",
        options=[
            n.ApplicationCommandOption(
                name="event_time",
                type=n.ApplicationOptionType.string,
                description=f"The YYYY/MM/DD HH:MM:SS AM/PM of the event to update",
                required=True
            ),
        ]
    )
    async def delete_event(
                self,
                ctx: t.CommandI,
                event_time: str | dt.datetime
            ):
        """Deletes an existing event"""
        await ctx.send("Deleted")

    @client.command(
        name="log update",
        options=[
            n.ApplicationCommandOption(
                name="original_event_time",
                type=n.ApplicationOptionType.string,
                description=f"The YYYY/MM/DD HH:MM:SS AM/PM of the event to update",
                required=True
            ),
            n.ApplicationCommandOption(
                name="new_event_time",
                type=n.ApplicationOptionType.string,
                description=f"The YYYY/MM/DD HH:MM:SS AM/PM to update to (defaults to right now)",
                required=False
            ),
        ]
    )
    async def update_event(
                self,
                ctx: t.CommandI,
                original_event_time: str | dt.datetime,
                new_event_time: str | dt.datetime = dt.datetime.now(
                    tz("America/Los_Angeles")
                )
            ):
        """Updates the time of an existing event"""
        await ctx.send("Updated")

    @client.command(
        name="log list",
        options = [
            n.ApplicationCommandOption(
                name="year",
                type=n.ApplicationOptionType.integer,
                description="The year of the event",
                required=False
            ),
            n.ApplicationCommandOption(
                name="month",
                type=n.ApplicationOptionType.integer,
                description="The month of the event",
                required=False
            ),
            n.ApplicationCommandOption(
                name="day",
                type=n.ApplicationOptionType.integer,
                description="The day of the event",
                required=False
            ),
        ]
    )
    async def list_events(
                self,
                ctx: t.CommandI,
                year: int = 0,
                month: int = 0,
                day: int = 0
            ) -> None:
        """List's a your events in a paginated format"""

        if not (year or month or day):
            return await self.send_event_dates(ctx)

        now = dt.datetime.now(tz("America/Los_Angeles"))

        year = year or now.year
        month = month or now.month
        day = day or now.day

        try:
            entered = dt.datetime(
                year, month, day, tzinfo=tz("America/Los_Angeles")
            )
        except Exception as e:
            return await ctx.send("Please enter a valid date.")

        pooper = get_pooper(ctx.user.id)

        paginated_events: dict[dt.datetime, list[list[LoggedEvent]]]
        paginated_events = pooper.get_paginated_events()

        if not paginated_events:
            return await ctx.send("You have no logged events to display.")

        formatted_page, final_page = self.get_formatted_page(
            paginated_events, year, month, day, 0
        )

        if final_page < 0:
            return await ctx.send(
                f"You have no logged events on { \
                    entered.strftime("%B %d, %Y %I:%M:%S %p") \
                } to display."
            )

        await ctx.send(
            embeds=[formatted_page],
            components=self.get_scroll_buttons(
                ctx.user.id, year, month, day, 0, final_page
            )
        )

    async def send_event_dates(self, ctx: t.CommandI):
        found_dates: set[dt.datetime] | list[dt.datetime] = set()
        pooper = get_pooper(ctx.user.id)

        if not pooper.logged_events:
            return await ctx.send("You have not yet logged any events!")

        for event in pooper.logged_events:
            found_dates.add(
                dt.datetime(
                    event.event_time.year,
                    event.event_time.month,
                    event.event_time.day,
                    tzinfo=event.event_time.tzinfo
                )
            )

        found_dates = sorted(list(found_dates))

        embed = n.Embed(title="Available Poo Dates")
        embed.color = 0x563D2D

        embed.description = "\n".join(
            [date.strftime("%B %d, %Y") for date in found_dates]
        )

        await ctx.send(embeds=[embed])

    def get_formatted_page(
                self,
                paginated_events: dict[dt.datetime, list[list[LoggedEvent]]],
                year: int, month: int, day: int,
                page: int = 0
            ) -> tuple[n.Embed, int]:
        """"""
        fake_date = dt.datetime(
            year=year, month=month, day=day, tzinfo=tz("America/Los_Angeles")
        )

        embed = n.Embed(title=fake_date.strftime("%B %d, %Y"))
        embed.color = 0x563D2D

        if not fake_date in paginated_events or page < 0:
            return embed, -1

        day_pages = paginated_events[fake_date]
        page = min(len(day_pages) - 1, page)
        page_events = day_pages[page]
        for event in page_events:
            embed.add_field(
                name=event.event_time.strftime("%I:%M:%S %p") + "-------------",
                value=str(event),
                inline=False
            )

        embed.set_footer(f"{page + 1}/{len(day_pages)}")

        return embed, len(day_pages) - 1

    def get_scroll_buttons(
                self,
                user_id: int,
                year: int,
                month: int,
                day: int,
                current_page: int = 0,
                final_page: int = 1,
            ) -> list[n.ActionRow]:
        """"""

        buttons = []
        # Add left button
        buttons.append(
            n.Button(
                label="Left",
                custom_id=f"LOG SCROLL|{user_id}|{year}|{month}|{day}|" + \
                            f"{current_page}|-1",
                disabled=(current_page == 0)
            )
        )

        # Add cancel button
        buttons.append(
            n.Button(
                label="Cancel",
                custom_id=f"LOG CANCEL|{user_id}",
                style=n.ButtonStyle.danger
            )
        )

        # Add right button
        buttons.append(
            n.Button(
                label="Right",
                custom_id=f"LOG SCROLL|{user_id}|{year}|{month}|{day}|" + \
                            f"{current_page}|+1",
                disabled=(current_page == final_page)
            )
        )

        return [n.ActionRow(buttons)]

    def get_random_response(self):
        return random.choice(
            [
                "Another beast felled.",
                "You've conquered the porcelain throne.",
                "Congratulations on your successful deployment.",
                "I salute your triumph in the battle of the bowels.",
                "Another victorious mission completed.",
                "You are the tamer of the beast.",
                "A toast to you, the fearless conquerer.",
                "A hard-fought battle won.",
                "The destroyer of porcelain stands before me.",
                "A silent nod to your quiet triumph.",
                "The warrior's journey is never easy, but you endure.",
                "Your mastery over the bowl is unmatched.",
                "The victor emerges from the battlefield.",
                "A testament to your unwavering resolve.",
                "Now you are become death, the destroyer of worlds."
            ]
        )

