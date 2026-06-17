CREATE TABLE merchants (
    merchant_id         INT             NOT NULL AUTO_INCREMENT,
    name                VARCHAR(120)    NOT NULL,
    category            VARCHAR(60)     NOT NULL,
    city                VARCHAR(80)     NOT NULL,
    region              VARCHAR(60)     NOT NULL,
    franchise_group     VARCHAR(80)         NULL,
    tenure_years        DECIMAL(4,1)    NOT NULL,
    card_acceptance_date DATE            NOT NULL,
    PRIMARY KEY (merchant_id)
);

CREATE TABLE transactions (
    txn_id          INT             NOT NULL AUTO_INCREMENT,
    merchant_id     INT             NOT NULL,
    cardholder_id   INT             NOT NULL,
    amount          DECIMAL(10,2)   NOT NULL,
    status          VARCHAR(20)     NOT NULL,
    txn_date        DATE            NOT NULL,
    refund_flag     TINYINT(1)      NOT NULL DEFAULT 0,
    decline_reason  VARCHAR(80)         NULL,
    PRIMARY KEY (txn_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);

CREATE TABLE merchant_health (
    health_id           INT             NOT NULL AUTO_INCREMENT,
    merchant_id         INT             NOT NULL,
    month_year          VARCHAR(7)      NOT NULL,
    txn_volume          INT             NOT NULL,
    avg_ticket          DECIMAL(10,2)   NOT NULL,
    refund_rate         DECIMAL(5,4)    NOT NULL,
    decline_rate        DECIMAL(5,4)    NOT NULL,
    cardholder_count    INT             NOT NULL,
    seasonal_baseline   DECIMAL(10,2)       NULL,
    msi_score           DECIMAL(5,2)        NULL,
    stress_flag         VARCHAR(20)         NULL,
    PRIMARY KEY (health_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id),
    UNIQUE KEY uq_merchant_month (merchant_id, month_year)
);

CREATE TABLE merchant_network (
    edge_id                 INT             NOT NULL AUTO_INCREMENT,
    merchant_a              INT             NOT NULL,
    merchant_b              INT             NOT NULL,
    relationship_type       VARCHAR(40)     NOT NULL,
    shared_cardholder_count INT             NOT NULL DEFAULT 0,
    edge_weight             DECIMAL(5,4)    NOT NULL,
    last_updated            DATE            NOT NULL,
    PRIMARY KEY (edge_id),
    FOREIGN KEY (merchant_a) REFERENCES merchants(merchant_id),
    FOREIGN KEY (merchant_b) REFERENCES merchants(merchant_id)
);

CREATE TABLE contagion_events (
    event_id                    INT             NOT NULL AUTO_INCREMENT,
    source_merchant_id          INT             NOT NULL,
    triggered_at                DATETIME        NOT NULL,
    propagation_depth           TINYINT         NOT NULL,
    affected_merchant_ids       TEXT            NOT NULL,
    estimated_chargeback_volume DECIMAL(14,2)       NULL,
    severity_level              VARCHAR(20)     NOT NULL,
    PRIMARY KEY (event_id),
    FOREIGN KEY (source_merchant_id) REFERENCES merchants(merchant_id)
);

CREATE TABLE geo_risk_zones (
    zone_id         INT             NOT NULL AUTO_INCREMENT,
    city            VARCHAR(80)     NOT NULL,
    region          VARCHAR(60)     NOT NULL,
    merchant_count  INT             NOT NULL,
    avg_msi         DECIMAL(5,2)    NOT NULL,
    critical_count  INT             NOT NULL DEFAULT 0,
    elevated_count  INT             NOT NULL DEFAULT 0,
    risk_tier       VARCHAR(20)     NOT NULL,
    flagged_at      DATE            NOT NULL,
    PRIMARY KEY (zone_id),
    UNIQUE KEY uq_city (city)
);
