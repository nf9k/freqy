-- freqy-database schema
-- MariaDB 11

SET NAMES utf8mb4;

-- -------------------------------------------------------
-- Users (one row per callsign/account)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    callsign        VARCHAR(10)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    email           VARCHAR(255),
    fname           VARCHAR(100),
    mname           VARCHAR(50),
    lname           VARCHAR(100),
    suffix          VARCHAR(20),
    address         VARCHAR(255),
    city            VARCHAR(100),
    state           CHAR(2),
    zip             VARCHAR(10),
    phone_home      VARCHAR(20),
    phone_work      VARCHAR(20),
    phone_cell      VARCHAR(20),
    is_admin         TINYINT(1)   NOT NULL DEFAULT 0,
    totp_secret      VARCHAR(32),
    totp_enabled     TINYINT(1)   NOT NULL DEFAULT 0,
    webauthn_enabled TINYINT(1)   NOT NULL DEFAULT 0,
    license_class    VARCHAR(20),               -- FCC license class (Extra, General, etc.)
    dashboard_final_only TINYINT(1) NOT NULL DEFAULT 0,
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- Password reset tokens
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    token       VARCHAR(64)  NOT NULL UNIQUE,
    expires_at  DATETIME     NOT NULL,
    used        TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- Coordination records (one row per repeater/link/beacon)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS coordination_records (
    id                  INT AUTO_INCREMENT PRIMARY KEY,

    -- Identity
    subdir              VARCHAR(20)  UNIQUE,          -- legacy record ID e.g. A00315
    subdsc              VARCHAR(255),                 -- short description
    user_id             INT          NOT NULL,         -- account owner
    secondary_contact_id INT,                         -- alternate contact (one max)
    system_id           VARCHAR(10),                  -- system callsign (may differ from owner)
    system_sponsor      VARCHAR(50),                  -- sponsor callsign or club name
    sponsor_abbrev      VARCHAR(50),
    sponsor_url         VARCHAR(255),
    parent_record_id    INT,                          -- NULL if top-level

    -- Classification
    app_type            VARCHAR(20)  NOT NULL DEFAULT 'Repeater',  -- Repeater, Link, Control RX, Beacon, Other
    status              VARCHAR(30)  NOT NULL DEFAULT 'New',       -- New, Final, Cancelled, Audit, Construction Permit, On Hold, Expired, Placeholder, Other
    last_action         VARCHAR(100),
    willbe              VARCHAR(20),                 -- Open, Closed, Private

    -- Dates
    orig_date           DATE,
    mod_date            DATE,
    expires_date        DATE,                        -- NULL for Cancelled / N/A records
    eq_ready            TINYINT(1),
    eq_ready_date       DATE,
    inherit             TINYINT(1)   DEFAULT 1,

    -- Notes
    comments            TEXT,
    audit_comments      TEXT,
    rdnotes             VARCHAR(100),
    rdnotes2            VARCHAR(100),

    -- Frequency
    band                VARCHAR(10),                 -- 29, 50, 144, 222, 440, GHZ
    freq_output         DECIMAL(10,4),               -- MHz
    freq_input          DECIMAL(10,4),               -- MHz
    bandwidth           VARCHAR(30),
    emission_des        VARCHAR(20),
    emission_des2       VARCHAR(20),

    -- Tone / Digital
    tx_pl               VARCHAR(10),                 -- CTCSS Hz
    rx_pl               VARCHAR(10),
    tx_dcs              VARCHAR(10),
    rx_dcs              VARCHAR(10),
    dmr_cc              TINYINT UNSIGNED,
    p25_nac             VARCHAR(10),
    nxdn_ran            VARCHAR(10),
    fusion_dsq          VARCHAR(10),

    -- TX power & site
    tx_power            SMALLINT UNSIGNED,           -- watts
    loc_lat             DECIMAL(9,6),                -- decimal degrees, positive N
    loc_lng             DECIMAL(9,6),                -- decimal degrees, negative W
    loc_building        VARCHAR(255),
    loc_street          VARCHAR(255),
    loc_city            VARCHAR(100),
    loc_county          VARCHAR(100),
    loc_state           CHAR(2),
    loc_region          VARCHAR(30),

    -- TX antenna
    ant_type            VARCHAR(50),
    ant_gain            DECIMAL(5,2),                -- dBd
    ant_haat            SMALLINT,                    -- ft
    ant_amsl            SMALLINT,                    -- ft
    ant_ahag            SMALLINT,                    -- ft
    ant_favor           VARCHAR(50),
    ant_beamwidth       VARCHAR(20),
    ant_frontback       VARCHAR(20),
    ant_polarization    VARCHAR(10),
    ant_comment         VARCHAR(255),
    fdl_loss            DECIMAL(5,2),                -- dB

    -- RX site (NULL = same as TX)
    rx_lat              DECIMAL(9,6),
    rx_lng              DECIMAL(9,6),

    -- RX antenna
    ant_type_rx         VARCHAR(50),
    ant_gain_rx         DECIMAL(5,2),
    ant_ahag_rx         SMALLINT,
    ant_favor_rx        VARCHAR(50),
    ant_beamwidth_rx    VARCHAR(20),
    ant_frontback_rx    VARCHAR(20),
    ant_polarization_rx VARCHAR(10),
    ant_comment_rx      VARCHAR(255),
    fdl_loss_rx         DECIMAL(5,2),

    -- Trustee (denormalized from user for display/export without a join)
    trustee_name        VARCHAR(255),
    trustee_callsign    VARCHAR(10),
    trustee_phone_day   VARCHAR(20),
    trustee_phone_eve   VARCHAR(20),
    trustee_phone_cell  VARCHAR(20),
    trustee_email       VARCHAR(255),

    last_activity_confirmed DATE     DEFAULT NULL,
    activity_confirm_token  VARCHAR(64) DEFAULT NULL,

    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)                REFERENCES users(id),
    FOREIGN KEY (secondary_contact_id)  REFERENCES users(id),
    FOREIGN KEY (parent_record_id)       REFERENCES coordination_records(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- TOTP backup codes (one row per code)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS totp_backup_codes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    code_hash   VARCHAR(255) NOT NULL,
    used        TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- WebAuthn / FIDO2 credentials (one row per registered key)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS webauthn_credentials (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT          NOT NULL,
    credential_id VARCHAR(512) NOT NULL,
    public_key    TEXT         NOT NULL,
    sign_count    INT          NOT NULL DEFAULT 0,
    name          VARCHAR(100) NOT NULL DEFAULT 'Security Key',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_credential_id (credential_id(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- FCC ULS callsign lookup cache (updated daily via import_fcc.py)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS fcc_licenses (
    callsign        VARCHAR(10)  NOT NULL PRIMARY KEY,
    fname           VARCHAR(100),
    mi              VARCHAR(5),
    lname           VARCHAR(100),
    suffix          VARCHAR(20),
    address         VARCHAR(255),
    city            VARCHAR(100),
    state           CHAR(2),
    zip             VARCHAR(10),
    license_class   VARCHAR(20),   -- Extra, Advanced, General, Technician, Novice, Technician Plus
    license_status  CHAR(1),       -- A=Active, E=Expired, C=Cancelled, T=Terminated
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_zip (zip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- Expiration notice tracking (one row per record+threshold)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS expiration_notices (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    record_id       INT      NOT NULL,
    days_threshold  SMALLINT NOT NULL,   -- 90, 60, 30, 14, 7, 1
    sent_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_record_threshold (record_id, days_threshold),
    FOREIGN KEY (record_id) REFERENCES coordination_records(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- Activity confirmations (use-it-or-lose-it tracking)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_confirmations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    record_id       INT          NOT NULL,
    confirmed_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_by    VARCHAR(10),
    method          VARCHAR(20)  NOT NULL DEFAULT 'email',
    FOREIGN KEY (record_id) REFERENCES coordination_records(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- Changelog (one row per change event, mirrors changelog.txt)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS record_changelog (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    record_id   INT          NOT NULL,
    changed_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by  VARCHAR(10),             -- callsign or 'SYSTEM'
    summary     TEXT,
    FOREIGN KEY (record_id) REFERENCES coordination_records(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
