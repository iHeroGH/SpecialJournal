-- The poo_events table keeps track of logged events
CREATE TABLE IF NOT EXISTS poo_events(
    user_id BIGINT NOT NULL,

    volume SMALLINT default 0,
    texture SMALLINT default 0,
    shape SMALLINT default 0,
    feel SMALLINT default 0,
    wipe_count SMALLINT default 0,
    color SMALLINT default 0,
    smell SMALLINT default 0,
    continuous BOOLEAN default False,
    rise BOOLEAN default False,

    event_time TIMESTAMP WITH TIME ZONE,

    PRIMARY KEY (user_id, event_time)
);