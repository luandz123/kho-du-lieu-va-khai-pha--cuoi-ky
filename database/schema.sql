-- P1-S04-draft-v2 / contract v2 / PostgreSQL 17.
-- Inherits draft-v1; no change to table, column, constraint, index or view definitions.
-- Updated basis: PR5 head b73c8e2, merge a8d2615; P1 s04_inputs_pr5.json.
-- Canonical checksums unchanged; metadata SHA correction does not change this design.
-- DESIGN ONLY: not executed. No connection, schema creation or load is authorized now.
-- Evidence: G1 head 9299268, merge b71d439; P1 g1_verification_9299268.json.
-- First installation only; existing schemas cause an error rather than being replaced.
-- Future operator must approve a dedicated project DB and set session btl.target_database.
-- This file never creates a database, a role, credentials, or inserts business data.

BEGIN;
SET LOCAL TIME ZONE 'UTC';

DO $database_guard$
DECLARE
    target_database text := current_setting('btl.target_database', true);
BEGIN
    IF target_database IS NULL OR target_database = ''
       OR current_database() <> target_database
       OR current_database() IN ('postgres', 'template0', 'template1') THEN
        RAISE EXCEPTION 'Approved dedicated project database required; draft must not run in maintenance databases';
    END IF;
END;
$database_guard$;

CREATE SCHEMA staging;
CREATE SCHEMA dw;
CREATE SCHEMA analytics;

-- Source line number is traceability, not an invented MovieLens identifier.
-- Text fields allow validation/rejection before dimension/fact insertion.
-- ZIP code is neither staged as a field nor used in the warehouse.
CREATE TABLE staging.users_raw (
    source_line bigint PRIMARY KEY CHECK (source_line > 0),
    user_id_raw text,
    gender_raw text,
    age_code_raw text,
    occupation_raw text
);

CREATE TABLE staging.movies_raw (
    source_line bigint PRIMARY KEY CHECK (source_line > 0),
    movie_id_raw text,
    title_raw text,
    genres_raw text
);

CREATE TABLE staging.ratings_raw (
    source_line bigint PRIMARY KEY CHECK (source_line > 0),
    user_id_raw text,
    movie_id_raw text,
    rating_raw text,
    timestamp_raw text
);

CREATE TABLE dw.dim_user (
    user_key integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id integer NOT NULL UNIQUE CHECK (user_id > 0),
    gender text NOT NULL CHECK (gender IN ('F', 'M')),
    age_group text NOT NULL CHECK (
        age_group IN ('Under 18', '18-24', '25-34', '35-44', '45-49', '50-55', '56+')
    ),
    occupation smallint NOT NULL CHECK (occupation BETWEEN 0 AND 20)
);

CREATE TABLE dw.dim_movie (
    movie_key integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    movie_id integer NOT NULL UNIQUE CHECK (movie_id > 0),
    title text NOT NULL,
    release_year smallint CHECK (release_year BETWEEN 0 AND 9999)
);

CREATE TABLE dw.dim_date (
    date_key integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_date date NOT NULL UNIQUE,
    calendar_year smallint GENERATED ALWAYS AS (EXTRACT(YEAR FROM full_date)::smallint) STORED,
    quarter_number smallint GENERATED ALWAYS AS (EXTRACT(QUARTER FROM full_date)::smallint) STORED,
    month_number smallint GENERATED ALWAYS AS (EXTRACT(MONTH FROM full_date)::smallint) STORED,
    day_of_month smallint GENERATED ALWAYS AS (EXTRACT(DAY FROM full_date)::smallint) STORED,
    -- Composite FK in fact also proves the date dimension matches the UTC rating day.
    CONSTRAINT uq_dim_date_key_day UNIQUE (date_key, full_date),
    CONSTRAINT ck_dim_date_quarter CHECK (quarter_number BETWEEN 1 AND 4),
    CONSTRAINT ck_dim_date_month CHECK (month_number BETWEEN 1 AND 12),
    CONSTRAINT ck_dim_date_day CHECK (day_of_month BETWEEN 1 AND 31)
);

CREATE TABLE dw.dim_genre (
    genre_key integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    genre_name text NOT NULL UNIQUE
);

CREATE TABLE dw.bridge_movie_genre (
    movie_key integer NOT NULL REFERENCES dw.dim_movie (movie_key),
    genre_key integer NOT NULL REFERENCES dw.dim_genre (genre_key),
    PRIMARY KEY (movie_key, genre_key)
);

CREATE TABLE dw.fact_rating (
    rating_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_key integer NOT NULL REFERENCES dw.dim_user (user_key),
    movie_key integer NOT NULL REFERENCES dw.dim_movie (movie_key),
    date_key integer NOT NULL,
    rating smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
    rating_timestamp bigint NOT NULL,
    rated_at timestamptz NOT NULL,
    rated_date date GENERATED ALWAYS AS ((rated_at AT TIME ZONE 'UTC')::date) STORED,
    -- Verified duplicate_pairs=0 at G1; not an assumption about viewing sessions.
    CONSTRAINT uq_fact_rating_user_movie UNIQUE (user_key, movie_key),
    CONSTRAINT ck_fact_rating_epoch CHECK (EXTRACT(EPOCH FROM rated_at) = rating_timestamp),
    CONSTRAINT fk_fact_rating_utc_day FOREIGN KEY (date_key, rated_date)
        REFERENCES dw.dim_date (date_key, full_date)
);

-- PK/UNIQUE already index user_id/movie_id/full_date/genre_name and fact user prefix.
CREATE INDEX ix_fact_rating_movie ON dw.fact_rating (movie_key);
CREATE INDEX ix_fact_rating_date_movie ON dw.fact_rating (date_key, movie_key);
CREATE INDEX ix_fact_rating_rated_at ON dw.fact_rating (rated_at);
CREATE INDEX ix_bridge_genre_movie ON dw.bridge_movie_genre (genre_key, movie_key);

-- Contract views expose original IDs, exact column order, and no implicit ordering.
CREATE VIEW dw.v_ml_users AS
SELECT u.user_id AS user_id, u.gender AS gender, u.age_group AS age_group,
       u.occupation::integer AS occupation
FROM dw.dim_user AS u;

CREATE VIEW dw.v_ml_movies AS
SELECT m.movie_id AS movie_id, m.title AS title, m.release_year::integer AS release_year
FROM dw.dim_movie AS m;

CREATE VIEW dw.v_ml_movie_genres AS
SELECT m.movie_id AS movie_id, g.genre_name AS genre_name
FROM dw.bridge_movie_genre AS b
JOIN dw.dim_movie AS m ON m.movie_key = b.movie_key
JOIN dw.dim_genre AS g ON g.genre_key = b.genre_key;

CREATE VIEW dw.v_ml_ratings AS
SELECT u.user_id AS user_id, m.movie_id AS movie_id, f.rating::integer AS rating,
       f.rating_timestamp AS "timestamp",
       to_char(f.rated_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS rated_at
FROM dw.fact_rating AS f
JOIN dw.dim_user AS u ON u.user_key = f.user_key
JOIN dw.dim_movie AS m ON m.movie_key = f.movie_key;

-- Technical model registry, not a new source dimension or an additional ML method.
-- Cross-row checks (K, complete profiles, hashes, means, cohort) occur before activation.
CREATE TABLE analytics.model_registry (
    model_version text PRIMARY KEY CHECK (length(btrim(model_version)) > 0),
    contract_version smallint NOT NULL CHECK (contract_version = 2),
    source_hashes jsonb NOT NULL CHECK (
        jsonb_typeof(source_hashes) = 'object'
        AND source_hashes ?& ARRAY['users.dat', 'movies.dat', 'ratings.dat', 'README']
    ),
    canonical_hashes jsonb NOT NULL CHECK (
        jsonb_typeof(canonical_hashes) = 'object'
        AND canonical_hashes ?& ARRAY['users', 'movies', 'movie_genres', 'ratings']
    ),
    k smallint NOT NULL CHECK (k BETWEEN 2 AND 8),
    seed integer NOT NULL,
    preprocessing jsonb NOT NULL,
    genre_order text[] NOT NULL CHECK (
        cardinality(genre_order) > 0 AND array_ndims(genre_order) = 1
        AND array_position(genre_order, NULL) IS NULL
    ),
    libraries jsonb NOT NULL CHECK (jsonb_typeof(libraries) = 'object'),
    training_config_hash text NOT NULL CHECK (training_config_hash ~ '^[0-9a-f]{64}$'),
    model_created_at timestamptz NOT NULL,
    registered_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_valid_for_dw boolean NOT NULL DEFAULT false,
    is_active boolean NOT NULL DEFAULT false,
    CONSTRAINT ck_active_model_valid CHECK (NOT is_active OR is_valid_for_dw)
);

CREATE UNIQUE INDEX uq_model_registry_one_active
    ON analytics.model_registry (is_active) WHERE is_active;

CREATE TABLE analytics.user_cluster (
    model_version text NOT NULL REFERENCES analytics.model_registry (model_version),
    user_id integer NOT NULL REFERENCES dw.dim_user (user_id),
    cluster_id integer,
    status text NOT NULL,
    PRIMARY KEY (model_version, user_id),
    CONSTRAINT ck_user_cluster_status CHECK (
        (status = 'assigned' AND cluster_id IS NOT NULL AND cluster_id >= 0)
        OR (status = 'insufficient_evidence' AND cluster_id IS NULL)
    )
);

CREATE TABLE analytics.cluster_genre_profile (
    model_version text NOT NULL REFERENCES analytics.model_registry (model_version),
    cluster_id integer NOT NULL CHECK (cluster_id >= 0),
    genre_name text NOT NULL REFERENCES dw.dim_genre (genre_name),
    mean_preference double precision NOT NULL CHECK (mean_preference BETWEEN 0 AND 1),
    n_users integer NOT NULL CHECK (n_users >= 0),
    PRIMARY KEY (model_version, cluster_id, genre_name)
);

CREATE INDEX ix_user_cluster_version_cluster
    ON analytics.user_cluster (model_version, cluster_id);
CREATE INDEX ix_user_cluster_source_user ON analytics.user_cluster (user_id);
CREATE INDEX ix_cluster_profile_genre ON analytics.cluster_genre_profile (genre_name);

-- Internal BI entry points always filter one active, current-DW model.
-- These do not change the four-table contract or the handoff CSV column order.
CREATE VIEW analytics.v_active_user_cluster AS
SELECT c.user_id, c.cluster_id, c.status, c.model_version
FROM analytics.user_cluster AS c
JOIN analytics.model_registry AS r ON r.model_version = c.model_version
WHERE r.is_active AND r.is_valid_for_dw;

CREATE VIEW analytics.v_active_cluster_genre_profile AS
SELECT p.cluster_id, p.genre_name, p.mean_preference, p.n_users, p.model_version
FROM analytics.cluster_genre_profile AS p
JOIN analytics.model_registry AS r ON r.model_version = p.model_version
WHERE r.is_active AND r.is_valid_for_dw;

COMMIT;
