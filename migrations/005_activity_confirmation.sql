ALTER TABLE coordination_records
    ADD COLUMN last_activity_confirmed DATE DEFAULT NULL,
    ADD COLUMN activity_confirm_token VARCHAR(64) DEFAULT NULL;

CREATE TABLE IF NOT EXISTS activity_confirmations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    record_id       INT          NOT NULL,
    confirmed_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_by    VARCHAR(10),
    method          VARCHAR(20)  NOT NULL DEFAULT 'email',
    FOREIGN KEY (record_id) REFERENCES coordination_records(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
