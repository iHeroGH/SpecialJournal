import io
import logging
import novus as n
from novus import types as t
from novus.ext import client

import datetime as dt
from zoneinfo import ZoneInfo as tz
from matplotlib import pyplot as plt
from matplotlib.projections.polar import PolarAxes
from matplotlib.colors import Normalize, LinearSegmentedColormap
import numpy as np

from .utils.poo_objects import LoggedEvent
from .utils.poo_cache_utils import get_pooper

log = logging.getLogger("plugins.poo_master")

class Statistician(client.Plugin):

    @client.command(name="stats table")
    async def list_statistics(self, ctx: t.CommandI):
        """Calculates some helpful event statistics"""
        stats_embed = n.Embed(title=f"{ctx.user.username}'s Poopy Statistics")
        stats_embed.color = 0x563D2D

        pooper = get_pooper(ctx.user.id)
        paginated_events: dict[dt.datetime, list[list[LoggedEvent]]]
        paginated_events = pooper.get_paginated_events()

        now = dt.datetime.now(tz("America/Los_Angeles"))
        year = now.year
        month = now.month
        day = now.day

        lifetime_p = 0
        year_p = 0
        month_p = 0
        day_p = 0

        years_a: set[int] = set()
        months_a: set[int] = set()
        days_a: set[int] = set()

        total_wipes: int = 0
        max_wipe: int = 0

        for time_part, all_poops_matrix in paginated_events.items():
            years_a.add(time_part.year)
            months_a.add(time_part.month)
            days_a.add(time_part.day)

            for all_poops in all_poops_matrix:
                for poop in all_poops:
                    lifetime_p += 1

                    if poop.event_time.year == year:
                        year_p += 1
                    if poop.event_time.month == month:
                        month_p += 1
                    if poop.event_time.day == day:
                        day_p += 1

                    total_wipes += poop.wipe_count
                    if poop.wipe_count > max_wipe:
                        max_wipe = poop.wipe_count

        if not (years_a and months_a and days_a):
            return await ctx.send(\
                "Something went wrong gathering statistics. " + \
                "You may not have any logs."
            )

        stats_embed.add_field(
            name="Lifetime Poops",
            value=str(lifetime_p),
            inline=False
        )

        stats_embed.add_field(
            name="Year Poops",
            value=str(year_p),
            inline=True
        )
        stats_embed.add_field(
            name="Month Poops",
            value=str(month_p),
            inline=True
        )
        stats_embed.add_field(
            name="Day Poops",
            value=str(day_p),
            inline=True
        )

        stats_embed.add_field(
            name="Avg. Poops/Day",
            value=str(lifetime_p//len(days_a)),
            inline=True
        )
        stats_embed.add_field(
            name="Avg. Poops/Month",
            value=str(lifetime_p//len(months_a)),
            inline=True
        )
        stats_embed.add_field(
            name="Avg. Poops/Year",
            value=str(lifetime_p//len(years_a)),
            inline=True
        )

        stats_embed.add_field(
            name="Total Wipes Made",
            value=str(total_wipes),
            inline=True
        )
        stats_embed.add_field(
            name="Average Wipe Count",
            value=str(total_wipes//lifetime_p),
            inline=True
        )
        stats_embed.add_field(
            name="Highest Wipe Count",
            value=str(max_wipe),
            inline=True
        )

        await ctx.send(embeds=[stats_embed])

    @client.command(name="stats graph frequency")
    async def graph_frequency(self, ctx:t.CommandI):
        """Visualizes the commonality of delivery times"""
        stats_embed = n.Embed(title=f"{ctx.user.username}'s Poo-Time Frequency")
        stats_embed.color = 0x563D2D

        pooper = get_pooper(ctx.user.id)
        logged_events = pooper.logged_events

        await ctx.defer()

        image = Statistician.create_clock_plot(logged_events)
        image.seek(0)
        file = n.File(image, "graph.png")
        stats_embed.set_image(url="attachment://graph.png")
        await ctx.send(embeds=[stats_embed], files=[file])

    @staticmethod
    def create_clock_plot(
                logged_events: list[LoggedEvent],
                minute_intervals: int = 30
            ) -> io.BytesIO:
        """"""

        # Fill the axis with time-parts based on the minute interval
        start_time = dt.datetime(
            year=1, month=1, day=1,
            tzinfo=tz("America/Los_Angeles")
        )
        end_time = dt.datetime(
            year=1, month=1, day=1,
            hour=23, minute=60-minute_intervals,
            tzinfo=tz("America/Los_Angeles")
        )
        axis_times = [start_time]
        while axis_times[-1] < end_time:
            axis_times.append(
                axis_times[-1] + dt.timedelta(minutes=minute_intervals)
            )

        log.info(f"Creating clock-plot with axis times {axis_times}")

        # Create the plot itself
        plt.figure(figsize=(8,8))
        clock_plot: PolarAxes = plt.subplot(111, projection="polar") # type: ignore

        # Make the clock start at midnight and go clockwise around
        clock_plot.set_theta_direction(-1)
        clock_plot.set_theta_zero_location("N")

        # The hidden radian ticks
        theta = np.linspace(0, 2 * np.pi, len(axis_times), endpoint=False)

        # The input data (maps onto the hidden ticks)
        event_by_time = sorted(
            logged_events,
            key=lambda e: Statistician.truncate_datetime(e.event_time)
        )

        log.info(f"Creating clock-plot for events {event_by_time}")

        next_axis_time = 1
        current_event = 0
        counts = [0]
        # Calculate the frequency of each time-piece
        while current_event < len(event_by_time):
            event = event_by_time[current_event]
            if Statistician.truncate_datetime(event.event_time) < axis_times[next_axis_time]:
                counts[-1] += 1
            else:
                next_axis_time += 1
                current_event -= 1
                counts.append(0)

            current_event += 1
        while len(counts) < len(axis_times):
            counts.append(0)

        # Plot the bars onto the clock
        clock_plot.bar(
            theta,
            np.ones_like(counts),
            width=2*np.pi/len(counts),
            align='edge',
            color=Statistician.frequency_to_color(counts)
        )

        # Format the clock nicer
        clock_plot.set_yticks([0, 1])
        clock_plot.set_rmax(1)
        clock_plot.set_xticks(
            ticks=theta,
            labels=[
                s.strftime("%I:%M %p")
                if not s.minute else ''
                for s in axis_times
            ]
        )
        clock_plot.tick_params(pad=15, grid_color='#F6F6F6', labelcolor="white")
        plt.setp(clock_plot.get_yticklabels(), visible=False)
        plt.ylim(0, 1)

        image_data = io.BytesIO()
        plt.savefig(image_data, format="png", transparent=True)
        plt.close()

        return image_data

    @staticmethod
    def truncate_datetime(to_truncate: dt.datetime):
        return dt.datetime(
            1, 1, 1,
            to_truncate.hour,
            to_truncate.minute,
            to_truncate.second,
            tzinfo=tz("America/Los_Angeles")
        )

    @staticmethod
    def frequency_to_color(counts: list[int]):
        normalizer = Normalize(vmin=min(counts), vmax=max(counts))

        starting_color = (1, 1, 1) # White
        ending_color = (0.361, 0.251, 0.2) # Brown

        cmap = LinearSegmentedColormap.from_list(
            "poop", [starting_color, ending_color]
        )
        return cmap(normalizer(counts))
