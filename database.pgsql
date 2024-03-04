-- The poo_events table keeps track of logged events
CREATE TABLE IF NOT EXISTS poo_events(
    user_id BIGINT NOT NULL,

    volume SMALLINT default 1,
    texture SMALLINT default 1,
    shape SMALLINT default 1,
    feel SMALLINT default 1,
    wipe_count SMALLINT default 1,
    color SMALLINT default 1,
    smell SMALLINT default 1,
    continuous BOOLEAN default False,
    rise BOOLEAN default False,

    event_time TIMESTAMP WITH TIME ZONE,

    PRIMARY KEY (user_id, event_time)
);