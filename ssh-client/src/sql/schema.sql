USE MachineLogger;

CREATE TABLE IF NOT EXISTS machinestat (
    id int NOT NULL AUTO_INCREMENT,
    ipaddr varchar(255) NOT NULL,
    stat_type varchar(255) NOT NULL,
    stat_value varchar(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS machinelog (
    id int NOT NULL AUTO_INCREMENT,
    ipaddr varchar(255) NOT NULL,
    log_type varchar(255),
    log_id varchar(255),
    event_time varchar(255),
    computer_name varchar(255),
    category varchar(255),
    record_number varchar(255),
    source_name varchar(255),
    event_type varchar(255),
    message varchar(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id)
);
