DROP TABLE IF EXISTS anomaly_results CASCADE;
DROP TABLE IF EXISTS model_metrics CASCADE;
DROP TABLE IF EXISTS feature_measurements CASCADE;
DROP TABLE IF EXISTS clean_measurements CASCADE;
DROP TABLE IF EXISTS raw_measurements CASCADE;
DROP TABLE IF EXISTS datasets CASCADE;
DROP TABLE IF EXISTS app_settings CASCADE;

CREATE TABLE datasets (
                          id SERIAL PRIMARY KEY,
                          name VARCHAR(255) NOT NULL,
                          original_filename VARCHAR(255) NOT NULL,
                          source_type VARCHAR(50) NOT NULL DEFAULT 'csv',
                          uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          row_count INTEGER NOT NULL DEFAULT 0,
                          status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
                          is_active BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE raw_measurements (
                                  id SERIAL PRIMARY KEY,
                                  dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
                                  timestamp_raw TEXT,
                                  radiation_raw TEXT,
                                  sensor_id_raw TEXT,
                                  location_raw TEXT,
                                  temperature_raw TEXT,
                                  humidity_raw TEXT,
                                  is_anomaly_raw TEXT,
                                  anomaly_type_raw TEXT,
                                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_raw_measurements_dataset_id
    ON raw_measurements(dataset_id);

CREATE TABLE clean_measurements (
                                    id SERIAL PRIMARY KEY,
                                    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
                                    timestamp TIMESTAMP NOT NULL,
                                    radiation_level DOUBLE PRECISION NOT NULL,
                                    sensor_id VARCHAR(100),
                                    location VARCHAR(255),
                                    temperature DOUBLE PRECISION,
                                    humidity DOUBLE PRECISION,
                                    original_label BOOLEAN,
                                    anomaly_type VARCHAR(100),
                                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clean_measurements_dataset_id
    ON clean_measurements(dataset_id);

CREATE INDEX idx_clean_measurements_timestamp
    ON clean_measurements(timestamp);

CREATE TABLE feature_measurements (
                                      id SERIAL PRIMARY KEY,
                                      dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
                                      clean_measurement_id INTEGER NOT NULL REFERENCES clean_measurements(id) ON DELETE CASCADE,
                                      timestamp TIMESTAMP NOT NULL,
                                      radiation_level DOUBLE PRECISION NOT NULL,
                                      temperature DOUBLE PRECISION,
                                      humidity DOUBLE PRECISION,
                                      hour_of_day INTEGER,
                                      day_of_week INTEGER,
                                      rolling_mean DOUBLE PRECISION,
                                      rolling_std DOUBLE PRECISION,
                                      radiation_diff DOUBLE PRECISION,
                                      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feature_measurements_dataset_id
    ON feature_measurements(dataset_id);

CREATE TABLE anomaly_results (
                                 id SERIAL PRIMARY KEY,
                                 dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
                                 feature_measurement_id INTEGER NOT NULL REFERENCES feature_measurements(id) ON DELETE CASCADE,
                                 timestamp TIMESTAMP NOT NULL,
                                 radiation_level DOUBLE PRECISION NOT NULL,
                                 predicted_anomaly BOOLEAN NOT NULL,
                                 anomaly_score DOUBLE PRECISION NOT NULL,
                                 status VARCHAR(50) NOT NULL,
                                 model_name VARCHAR(100) NOT NULL DEFAULT 'Isolation Forest',
                                 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_anomaly_results_dataset_id
    ON anomaly_results(dataset_id);

CREATE INDEX idx_anomaly_results_predicted
    ON anomaly_results(predicted_anomaly);

CREATE TABLE model_metrics (
                               id SERIAL PRIMARY KEY,
                               dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
                               model_name VARCHAR(100) NOT NULL,
                               accuracy DOUBLE PRECISION,
                               precision_score DOUBLE PRECISION,
                               recall_score DOUBLE PRECISION,
                               fpr DOUBLE PRECISION,
                               fnr DOUBLE PRECISION,
                               total_records INTEGER NOT NULL DEFAULT 0,
                               total_anomalies INTEGER NOT NULL DEFAULT 0,
                               created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_metrics_dataset_id
    ON model_metrics(dataset_id);

CREATE TABLE app_settings (
                              key VARCHAR(100) PRIMARY KEY,
                              value TEXT NOT NULL,
                              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);