CREATE TABLE IF NOT EXISTS coverage_plots (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    record_id    INT      NOT NULL,
    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    error        TEXT,
    UNIQUE KEY uq_record (record_id),
    FOREIGN KEY (record_id) REFERENCES coordination_records(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
