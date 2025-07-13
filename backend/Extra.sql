CREATE TABLE etl_logs (
    log_id SERIAL PRIMARY KEY,
    process_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    error_message TEXT,
    rows_processed INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);