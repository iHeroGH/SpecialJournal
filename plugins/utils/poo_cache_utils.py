from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from datetime import datetime as dt

if TYPE_CHECKING:
    from asyncpg.connection import Connection

from novus.ext import database as db

from .poo_objects import Volume, Texture, Shape, Feel, Color, Smell, \
                        LoggedEvent, Pooper

log = logging.getLogger("plugins.cache_handler.poo_cache_utils")
global poo_cache
poo_cache: dict[int, Pooper] = {}

def clear_cache():
    global poo_cache
    for _, pooper in poo_cache.items():
        pooper.clear()
    poo_cache.clear()

def log_cache() -> None:
    """Logs a message of the cache"""
    global poo_cache
    log.info(f"Cache Requested: {poo_cache}")

async def load_data() -> None:
    """Loads all the data from the database into the cache."""
    global poo_cache

    # We want a fresh cache every time we load
    clear_cache()

    # Get all the data from the database
    async with db.Database.acquire() as conn:
        poo_rows = await conn.fetch(
            """
            SELECT
                *,
                event_time AT TIME ZONE 'America/Los_Angeles' AS event_time
            FROM
                poo_events
            """
        )

    # Add it to the cache
    log.info("Caching Shit.")
    for poo_record in poo_rows:
        logged_event = LoggedEvent.from_record(poo_record)
        pooper = get_pooper(poo_record['user_id'])
        pooper.logged_events.append(logged_event)

    log.info(f"Caching Complete! {poo_cache}")

def get_pooper(user_id: int) -> Pooper:
    """Creates an empty Pooper object if one is not found for a User ID"""
    global poo_cache
    if not user_id in poo_cache:
        log.info(f"Creating Pooper {user_id}")
        poo_cache[user_id] = Pooper(user_id).clear()

    return poo_cache[user_id]

def get_all_poopers() -> list[Pooper]:
    global poo_cache
    return list(poo_cache.values())

async def poo_modify_cache_db(
            user_id: int,
            volume: Volume,
            texture: Texture,
            shape: Shape,
            feel: Feel,
            wipe_count: int,
            color: Color,
            smell: Smell,
            continuous: bool,
            rise: bool,
            event_time: dt,
            conn: Connection | None = None,
        ) -> bool:
    """
    Performs an operation on the cache and optionally updates the database

    Parameters
    ----------
    user_id: int
        The user_id of the Pooper to update
    volume: Volume
        The size of the event
    texture: Texture
        The texture of the event
    shape: Shape
        The shape of the event
    feel: Feel
        The feel as the event occured
    wipe_count: int
        The number of wipes required
    color: Color
        The color of the event
    smell: Smell
        The smell of the event
    continuous: bool
        Whether the event was continuously made or if it was done in stages
    rise: bool
        Whether the event rised when it was over
    event_time: dt
        When the event took place
    conn : Connection | None
        An optional DB connection. If given, a query will be run to add the
        given data to the database in addition to the cache

    Returns
    -------
    success : bool
        A state of sucess for the requested operation.
    """

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

    log.info(
        f"Adding event {repr(logged_event)} to {user_id} " +
        f"{'with DB' if conn else ''}"
    )

    # Make sure we have a Pooper object in cache
    pooper = get_pooper(user_id)

    DB_QUERY = (
        """
        INSERT INTO
            poo_events
            (
                user_id,
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
        VALUES
            (
                $1,
                $2,
                $3,
                $4,
                $5,
                $6,
                $7,
                $8,
                $9,
                $10,
                $11
            )
        """
    )

    # CACHE_CHECK must be true to perform the caching and storing
    CACHE_CHECK: bool = True

    # Perfrom the operation
    if CACHE_CHECK:
        pooper.logged_events.append(logged_event)

        # If a database connection was given, add it to the db as well
        if conn:
            await conn.execute(
                DB_QUERY,
                user_id,
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

    return CACHE_CHECK