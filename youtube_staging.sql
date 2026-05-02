/*
YouTube Trending Video Pipeline
--------------------------------
Sources: USvideos_cleaned.csv, GBvideos_cleaned.csv, US_category_id.json
Output:  all_videos_final (aggregated by video_id)
Steps:
    1. Load US and GB CSV files into staging tables
    2. Convert trending_date to DATE format
    3. Merge US and GB into single table with country column
    4. Data quality checks (nulls, duplicates, distributions)
    5. Join category map from JSON
    6. Aggregate daily metrics by video
*/

create or replace file format csv_header_quotes 
    TYPE = 'CSV' --cvs for a comma separated files
    FIELD_DELIMITER = ',' --comma as column separators
    SKIP_HEADER = 1 --one header row
    FIELD_OPTIONALLY_ENCLOSED_BY = '"' --quotes are used for column entries
;


-- After systematically correcting the tag column entries, opening the file again to test
select $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
from @data/USvideos_cleaned.csv
(file_format => csv_header_quotes);
-- Successful table loaded

create or replace table USvideos(
    video_id VARCHAR,
    trending_date VARCHAR, --Irregular date format to change later
    title VARCHAR,
    channel_title VARCHAR,
    category_id INT,
    publish_time TIMESTAMP_NTZ,
    tags VARCHAR,
    views INT,
    likes INT,
    dislikes INT,
    comment_count INT,
    thumbnail_link VARCHAR,
    comments_disabled BOOLEAN,
    ratings_disabled BOOLEAN,
    video_error_or_removed BOOLEAN,
    description VARCHAR
);

copy into USvideos
from @data
files = ('USvideos_cleaned.csv')
file_format = (format_name=csv_header_quotes);

select * from USvideos LIMIT 10;

-- Repeating for GB file
select $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
from @data/GBvideos_cleaned.csv
(file_format => csv_header_quotes);
-- Successful table loaded

create or replace table GBvideos(
    video_id VARCHAR,
    trending_date VARCHAR,
    title VARCHAR,
    channel_title VARCHAR,
    category_id INT,
    publish_time TIMESTAMP_NTZ,
    tags VARCHAR,
    views INT,
    likes INT,
    dislikes INT,
    comment_count INT,
    thumbnail_link VARCHAR,
    comments_disabled BOOLEAN,
    ratings_disabled BOOLEAN,
    video_error_or_removed BOOLEAN,
    description VARCHAR
);

copy into GBvideos
from @data
files = ('GBvideos_cleaned.csv')
file_format = (format_name=csv_header_quotes);

select * from GBvideos LIMIT 10;

--Updating datetime column
ALTER TABLE USvideos ADD COLUMN trending_date_converted DATE;

UPDATE USvideos
SET trending_date_converted = TO_DATE(trending_date, 'YY.DD.MM');

ALTER TABLE USvideos DROP COLUMN trending_date;

select * from USvideos LIMIT 10;

--Updating datetime column
ALTER TABLE GBvideos ADD COLUMN trending_date_converted DATE;

UPDATE GBvideos
SET trending_date_converted = TO_DATE(trending_date, 'YY.DD.MM');

ALTER TABLE GBvideos DROP COLUMN trending_date;

select * from GBvideos LIMIT 10;

--Merging the two table into one
CREATE OR REPLACE TABLE all_videos AS
SELECT *, 'US' AS country FROM USvideos
UNION ALL
SELECT *, 'GB' AS country FROM GBvideos;

select * from all_videos LIMIT 10;

-- 1. Check for nulls in key columns
SELECT 
    COUNT(*) AS total_rows,
    COUNT(video_id)     AS video_id_count,
    COUNT(title)        AS title_count,
    COUNT(category_id)  AS category_id_count,
    COUNT(views)        AS views_count,
    COUNT(likes)        AS likes_count,
    COUNT(dislikes)     AS dislikes_count,
    COUNT(comment_count)     AS comment_count_count
FROM all_videos;
-- If any count is less than total_rows, that column has nulls
-- 79865 for all columns, no nulls

-- 2. Check for duplicate video entries
SELECT video_id, country, COUNT(*) AS appearances
FROM all_videos
GROUP BY video_id, country
HAVING COUNT(*) > 1
ORDER BY appearances DESC;
-- A video can appear up to 38 times in the table
-- Daily metrics will need to be aggregated by video

-- 3. Check for unexpected values in views/likes
SELECT 
    MIN(views), MAX(views),
    MIN(likes), MAX(likes),
    MIN(dislikes), MAX(dislikes)
FROM all_videos;
-- Videos can have 0 likes or dislikes 
-- but 549 is the minimum number of views within the dataset

-- 4. Check country distribution
SELECT country, COUNT(*) 
FROM all_videos
GROUP BY country;
-- US 40949
-- GB 38916

--Creating JSON File Format for the category map file
create or replace file format json_file_format
type = 'JSON' 
compression = 'AUTO' 
enable_octal = FALSE
allow_duplicate = FALSE 
strip_outer_array = TRUE
strip_null_values = FALSE 
ignore_utf8_errors = FALSE;

--Opening JSON category file
SELECT 
    value:id::INT                AS category_id,
    value:snippet:title::VARCHAR AS category_title -- title is nested inside the 'snippet' object
FROM @data/US_category_id.json
(file_format => json_file_format),
LATERAL FLATTEN(input => $1:items); -- needed because the JSON array is nested under 'items' {}
                                    -- inside a parent object, so strip_outer_array couldn't unwrap it
-- Successful table loaded

create or replace table category_map as 
    SELECT
    value:id::INT                AS category_id,
    value:snippet:title::VARCHAR AS category_title
    FROM @data/US_category_id.json
    (file_format => json_file_format),
    LATERAL FLATTEN(input => $1:items)
;


select * from category_map;


--Joining category map to the table
create or replace table all_videos_mapped as 
    SELECT
        v.*,
        c.category_title
    FROM all_videos v
    JOIN category_map c
        ON v.category_id = c.category_id
;

ALTER TABLE all_videos_mapped DROP COLUMN category_id; --Dropping column that's no longer needed

SELECT * FROM all_videos_mapped LIMIT 10;

--Aggregating the daily video metrics by video_id
create or replace table all_videos_final as
    SELECT
        video_id,
        title,
        channel_title,
        category_title,
        country,
        MAX(views)                              AS views,
        MAX(likes)                              AS likes,
        MAX(dislikes)                           AS dislikes,
        MAX(comment_count)                      AS comment_count,
        COUNT(DISTINCT trending_date_converted) AS days_trending
    FROM all_videos_mapped
    GROUP BY video_id, title, channel_title, category_title, country
;

SELECT * FROM all_videos_final LIMIT 10;

CREATE OR REPLACE FILE FORMAT parquet_format
    TYPE = 'PARQUET';

--Exporting table
COPY INTO @output/all_videos_final.parquet
FROM (
    SELECT --- Snowflake drops column names, preventing that here
        video_id,
        title,
        channel_title,
        category_title,
        country,
        views,
        likes,
        dislikes,
        comment_count,
        days_trending
    FROM all_videos_final
)
FILE_FORMAT = (FORMAT_NAME = parquet_format)
OVERWRITE = TRUE;