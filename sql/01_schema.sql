DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS account_mapping;

CREATE TABLE account_mapping (
    account_code   VARCHAR(10)  PRIMARY KEY,
    account_name   VARCHAR(100) NOT NULL,
    dre_line       VARCHAR(50)  NOT NULL,
    dre_order      INT          NOT NULL,
    amount_sign    SMALLINT     NOT NULL
);

CREATE TABLE transactions (
    id             SERIAL        PRIMARY KEY,
    date           DATE          NOT NULL,
    company        VARCHAR(50)   NOT NULL,
    business_unit  VARCHAR(50)   NOT NULL,
    cost_center    VARCHAR(50)   NOT NULL,
    account_code   VARCHAR(10)   NOT NULL REFERENCES account_mapping(account_code),
    account_name   VARCHAR(100)  NOT NULL,
    dre_line       VARCHAR(50)   NOT NULL,
    amount         NUMERIC(15,2) NOT NULL
);

CREATE INDEX idx_transactions_date    ON transactions(date);
CREATE INDEX idx_transactions_company ON transactions(company);
CREATE INDEX idx_transactions_dre     ON transactions(dre_line);