-- Table: tickfeed.bookticker_daily

-- DROP TABLE IF EXISTS tickfeed.bookticker_daily;

CREATE TABLE IF NOT EXISTS tickfeed.bookticker_daily
(
    exchange character varying COLLATE pg_catalog."default" NOT NULL,
    symbol character varying COLLATE pg_catalog."default" NOT NULL,
    date date NOT NULL,
    open numeric(32,16),
    high numeric(32,16),
    low numeric(32,16),
    close numeric(32,16),
    spread_min numeric(32,16),
    spread_max numeric(32,16),
    num_samples integer,
    bid_mean numeric(32,16),
    bid_variance numeric(32,16),
    ask_mean numeric(32,16),
    ask_variance numeric(32,16),
    mid_mean numeric(32,16),
    mid_variance numeric(32,16),
    CONSTRAINT bookticker_daily_pkey PRIMARY KEY (exchange, symbol, date)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS tickfeed.bookticker_daily
    OWNER to user;

GRANT ALL ON TABLE tickfeed.bookticker_daily TO user;

GRANT ALL ON TABLE tickfeed.bookticker_daily TO tickfeedwriter;


-- Index: symbol_date_btree_clustered

-- DROP INDEX IF EXISTS tickfeed.symbol_date_btree_clustered;

CREATE INDEX IF NOT EXISTS symbol_date_btree_clustered
    ON tickfeed.bookticker_daily USING btree
    (symbol COLLATE pg_catalog."default" ASC NULLS LAST, exchange COLLATE pg_catalog."default" ASC NULLS LAST, date ASC NULLS LAST)
    WITH (deduplicate_items=True)
    TABLESPACE pg_default;

ALTER TABLE IF EXISTS tickfeed.bookticker_daily
    CLUSTER ON symbol_date_btree_clustered;