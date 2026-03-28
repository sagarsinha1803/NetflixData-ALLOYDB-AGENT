-- =============================================================
-- Netflix Titles: AlloyDB for PostgreSQL Schema
-- Compatible with: AlloyDB (PostgreSQL 15+)
-- Generated from netflix_titles.csv
-- =============================================================

-- Enable pg_trgm for trigram-based ILIKE / full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Idempotent: drop before recreate
DROP TABLE IF EXISTS netflix_titles;

CREATE TABLE netflix_titles (
    "show_id"       TEXT        NOT NULL,
    "type"          TEXT        NOT NULL,
    "title"         TEXT        NOT NULL,
    "director"      TEXT        DEFAULT NULL,
    "cast"          TEXT        DEFAULT NULL, -- Enclosed in double quotes
    "country"       TEXT        DEFAULT NULL,
    "date_added"    DATE        DEFAULT NULL,
    "release_year"  SMALLINT    NOT NULL,
    "rating"        TEXT        DEFAULT NULL,
    "duration"      TEXT        NOT NULL,
    "listed_in"     TEXT        NOT NULL,
    "description"   TEXT        NOT NULL,

    CONSTRAINT pk_netflix_titles   PRIMARY KEY ("show_id"),
    CONSTRAINT chk_type            CHECK ("type" IN ('Movie', 'TV Show')),
    CONSTRAINT chk_release_year    CHECK ("release_year" BETWEEN 1900 AND 2100)
);

-- B-tree indexes for equality / range lookups
CREATE INDEX idx_netflix_type         ON netflix_titles USING btree ("type");
CREATE INDEX idx_netflix_release_year ON netflix_titles USING btree ("release_year");
CREATE INDEX idx_netflix_rating       ON netflix_titles USING btree ("rating");
CREATE INDEX idx_netflix_country      ON netflix_titles USING btree ("country");
CREATE INDEX idx_netflix_date_added   ON netflix_titles USING btree ("date_added");

-- GIN trigram indexes for ILIKE / full-text search
CREATE INDEX idx_netflix_title_trgm       ON netflix_titles USING gin ("title" gin_trgm_ops);
CREATE INDEX idx_netflix_listed_in_trgm   ON netflix_titles USING gin ("listed_in" gin_trgm_ops);
CREATE INDEX idx_netflix_description_trgm ON netflix_titles USING gin ("description" gin_trgm_ops);

-- Table and column comments
COMMENT ON TABLE  netflix_titles              IS 'Netflix catalog of movies and TV shows.';
COMMENT ON COLUMN netflix_titles."show_id"      IS 'Unique Netflix content identifier (e.g. s1).';
COMMENT ON COLUMN netflix_titles."type"         IS 'Content type: Movie or TV Show.';
COMMENT ON COLUMN netflix_titles."title"        IS 'Title of the content.';
COMMENT ON COLUMN netflix_titles."director"     IS 'Director name(s); NULL if not applicable.';
COMMENT ON COLUMN netflix_titles."cast"         IS 'Comma-separated list of cast members.'; -- Enclosed in double quotes
COMMENT ON COLUMN netflix_titles."country"      IS 'Country or countries of production.';
COMMENT ON COLUMN netflix_titles."date_added"   IS 'Date the title was added to Netflix (ISO 8601).';
COMMENT ON COLUMN netflix_titles."release_year" IS 'Original release year of the content.';
COMMENT ON COLUMN netflix_titles."rating"       IS 'Content rating (e.g. TV-MA, PG-13).';
COMMENT ON COLUMN netflix_titles."duration"     IS 'Duration: minutes for movies, seasons for TV shows.';
COMMENT ON COLUMN netflix_titles."listed_in"    IS 'Comma-separated genre/category tags.';
COMMENT ON COLUMN netflix_titles."description"  IS 'Short synopsis of the content.';