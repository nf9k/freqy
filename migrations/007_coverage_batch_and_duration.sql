-- DB-backed batch state (single-row, id always = 1)
CREATE TABLE IF NOT EXISTS coverage_batch (
    id           INT PRIMARY KEY DEFAULT 1,
    running      TINYINT(1) NOT NULL DEFAULT 0,
    total        INT NOT NULL DEFAULT 0,
    done         INT NOT NULL DEFAULT 0,
    errors       INT NOT NULL DEFAULT 0,
    current_subdir VARCHAR(20),
    started_at   DATETIME,
    finished_at  DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO coverage_batch (id) VALUES (1);

-- Track how long each plot run took
ALTER TABLE coverage_plots
    ADD COLUMN IF NOT EXISTS duration_secs SMALLINT UNSIGNED DEFAULT NULL;
