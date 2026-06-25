DROP VIEW IF EXISTS vw_daily_radiation_summary;
DROP VIEW IF EXISTS vw_location_anomaly_summary;
DROP VIEW IF EXISTS vw_model_performance;
DROP VIEW IF EXISTS vw_latest_anomalies;
DROP VIEW IF EXISTS vw_hourly_radiation_summary;

CREATE OR REPLACE VIEW vw_daily_radiation_summary AS
SELECT
    d.id AS dataset_id,
    d.name AS dataset_name,
    DATE(cm.timestamp) AS measurement_date,
    COUNT(cm.id) AS total_measurements,
    ROUND(AVG(cm.radiation_level)::numeric, 4) AS avg_radiation_level,
    ROUND(MIN(cm.radiation_level)::numeric, 4) AS min_radiation_level,
    ROUND(MAX(cm.radiation_level)::numeric, 4) AS max_radiation_level,
    ROUND(STDDEV_SAMP(cm.radiation_level)::numeric, 4) AS std_radiation_level,
    COALESCE(SUM(CASE WHEN cm.original_label = TRUE THEN 1 ELSE 0 END), 0) AS original_anomalies,
    COALESCE(SUM(CASE WHEN ar.predicted_anomaly = TRUE THEN 1 ELSE 0 END), 0) AS predicted_anomalies,
    COALESCE(SUM(CASE WHEN ar.status = 'Critical' THEN 1 ELSE 0 END), 0) AS critical_anomalies,
    COALESCE(SUM(CASE WHEN ar.status = 'Elevated' THEN 1 ELSE 0 END), 0) AS elevated_anomalies,
    COALESCE(SUM(CASE WHEN ar.status = 'Normal' THEN 1 ELSE 0 END), 0) AS normal_measurements
FROM datasets d
    JOIN clean_measurements cm
ON d.id = cm.dataset_id
    LEFT JOIN feature_measurements fm
    ON cm.id = fm.clean_measurement_id
    LEFT JOIN anomaly_results ar
    ON fm.id = ar.feature_measurement_id
GROUP BY
    d.id,
    d.name,
    DATE(cm.timestamp)
ORDER BY
    measurement_date;


CREATE OR REPLACE VIEW vw_hourly_radiation_summary AS
SELECT
    d.id AS dataset_id,
    d.name AS dataset_name,
    DATE(cm.timestamp) AS measurement_date,
    EXTRACT(HOUR FROM cm.timestamp)::integer AS hour_of_day,
    COUNT(cm.id) AS total_measurements,
    ROUND(AVG(cm.radiation_level)::numeric, 4) AS avg_radiation_level,
    ROUND(MIN(cm.radiation_level)::numeric, 4) AS min_radiation_level,
    ROUND(MAX(cm.radiation_level)::numeric, 4) AS max_radiation_level,
    COALESCE(SUM(CASE WHEN ar.predicted_anomaly = TRUE THEN 1 ELSE 0 END), 0) AS predicted_anomalies
FROM datasets d
    JOIN clean_measurements cm
ON d.id = cm.dataset_id
    LEFT JOIN feature_measurements fm
    ON cm.id = fm.clean_measurement_id
    LEFT JOIN anomaly_results ar
    ON fm.id = ar.feature_measurement_id
GROUP BY
    d.id,
    d.name,
    DATE(cm.timestamp),
    EXTRACT(HOUR FROM cm.timestamp)
ORDER BY
    measurement_date,
    hour_of_day;


CREATE OR REPLACE VIEW vw_location_anomaly_summary AS
SELECT
    d.id AS dataset_id,
    d.name AS dataset_name,
    COALESCE(cm.location, 'Unknown') AS location,
    COALESCE(cm.sensor_id, 'UNKNOWN_SENSOR') AS sensor_id,
    COUNT(cm.id) AS total_measurements,
    ROUND(AVG(cm.radiation_level)::numeric, 4) AS avg_radiation_level,
    ROUND(MAX(cm.radiation_level)::numeric, 4) AS max_radiation_level,
    COALESCE(SUM(CASE WHEN cm.original_label = TRUE THEN 1 ELSE 0 END), 0) AS original_anomalies,
    COALESCE(SUM(CASE WHEN ar.predicted_anomaly = TRUE THEN 1 ELSE 0 END), 0) AS predicted_anomalies,
    COALESCE(SUM(CASE WHEN ar.status = 'Critical' THEN 1 ELSE 0 END), 0) AS critical_anomalies,
    COALESCE(SUM(CASE WHEN ar.status = 'Elevated' THEN 1 ELSE 0 END), 0) AS elevated_anomalies,
    COALESCE(SUM(CASE WHEN ar.status = 'Normal' THEN 1 ELSE 0 END), 0) AS normal_measurements
FROM datasets d
         JOIN clean_measurements cm
              ON d.id = cm.dataset_id
         LEFT JOIN feature_measurements fm
                   ON cm.id = fm.clean_measurement_id
         LEFT JOIN anomaly_results ar
                   ON fm.id = ar.feature_measurement_id
GROUP BY
    d.id,
    d.name,
    COALESCE(cm.location, 'Unknown'),
    COALESCE(cm.sensor_id, 'UNKNOWN_SENSOR')
ORDER BY
    predicted_anomalies DESC,
    max_radiation_level DESC;


CREATE OR REPLACE VIEW vw_model_performance AS
WITH ranked_metrics AS (
    SELECT
        mm.*,
        ROW_NUMBER() OVER (
            PARTITION BY mm.dataset_id, mm.model_name
            ORDER BY mm.created_at DESC
        ) AS row_number
    FROM model_metrics mm
)
SELECT
    d.id AS dataset_id,
    d.name AS dataset_name,
    rm.model_name,
    ROUND(rm.accuracy::numeric, 2) AS accuracy,
    ROUND(rm.precision_score::numeric, 4) AS precision_score,
    ROUND(rm.recall_score::numeric, 4) AS recall_score,
    ROUND(rm.fpr::numeric, 4) AS fpr,
    ROUND(rm.fnr::numeric, 4) AS fnr,
    rm.total_records,
    rm.total_anomalies,
    rm.created_at
FROM ranked_metrics rm
         JOIN datasets d
              ON rm.dataset_id = d.id
WHERE rm.row_number = 1
ORDER BY
    d.id,
    rm.model_name;


CREATE OR REPLACE VIEW vw_latest_anomalies AS
SELECT
    d.id AS dataset_id,
    d.name AS dataset_name,
    ar.timestamp,
    ar.radiation_level,
    COALESCE(cm.sensor_id, 'UNKNOWN_SENSOR') AS sensor_id,
    COALESCE(cm.location, 'Unknown') AS location,
    cm.temperature,
    cm.humidity,
    cm.original_label,
    cm.anomaly_type,
    ar.predicted_anomaly,
    ROUND(ar.anomaly_score::numeric, 4) AS anomaly_score,
    ar.status,
    ar.model_name,
    ar.created_at
FROM anomaly_results ar
         JOIN datasets d
              ON ar.dataset_id = d.id
         JOIN feature_measurements fm
              ON ar.feature_measurement_id = fm.id
         JOIN clean_measurements cm
              ON fm.clean_measurement_id = cm.id
WHERE ar.predicted_anomaly = TRUE
ORDER BY
    ar.timestamp DESC;