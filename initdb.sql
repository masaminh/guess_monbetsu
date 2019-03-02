CREATE TABLE IF NOT EXISTS iter_race_calendar (
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    date DATE NOT NULL,
    course TEXT NOT NULL,
    url TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS iter_race_calendar_index
ON iter_race_calendar (year, month);

CREATE TABLE IF NOT EXISTS iter_races_by_url (
    dayurl TEXT NOT NULL,
    date DATE NOT NULL,
    course TEXT NOT NULL,
    raceno INTEGER NOT NULL,
    racename TEXT NOT NULL,
    tracktype TEXT NOT NULL,
    distance INTEGER NOT NULL,
    condition TEXT,
    horsenum INTEGER NOT NULL,
    url TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS iter_races_by_url_index
ON iter_races_by_url(dayurl);

CREATE TABLE IF NOT EXISTS get_race_result_by_url_raceinfo (
    date DATE NOT NULL,
    course TEXT NOT NULL,
    raceno INTEGER NOT NULL,
    racename TEXT NOT NULL,
    tracktype TEXT NOT NULL,
    distance INTEGER NOT NULL,
    condition TEXT NOT NULL,
    horsenum INTEGER NOT NULL,
    url TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS get_race_result_by_url_raceinfo_index
ON get_race_result_by_url_raceinfo(url);

CREATE TABLE IF NOT EXISTS get_race_result_by_url_horse (
    raceurl TEXT NOT NULL,
    horseorder TEXT NOT NULL,
    name TEXT NOT NULL,
    poplar INTEGER,
    weight INTEGER,
    time REAL,
    url TEXT,
    money INTEGER,
    no INTEGER
);
CREATE INDEX IF NOT EXISTS get_race_result_by_url_horse_index
ON get_race_result_by_url_horse(raceurl);

CREATE TABLE IF NOT EXISTS get_racelist_by_horseurl (
    date DATE NOT NULL,
    course TEXT NOT NULL,
    raceno INTEGER,
    racename TEXT NOT NULL,
    tracktype TEXT,
    distance INTEGER NOT NULL,
    condition TEXT,
    horsenum INTEGER NOT NULL,
    raceurl TEXT,
    horseorder TEXT NOT NULL,
    name TEXT NOT NULL,
    poplar INTEGER,
    weight INTEGER,
    time REAL,
    url TEXT,
    money INTEGER,
    no INTEGER
);
CREATE INDEX IF NOT EXISTS get_racelist_by_horseurl_index
ON get_racelist_by_horseurl(url);
