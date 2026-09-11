DROP VIEW IF EXISTS vw_daily_radiation_summary;
DROP VIEW IF EXISTS vw_location_anomaly_summary;
DROP VIEW IF EXISTS vw_model_performance;
DROP VIEW IF EXISTS vw_latest_anomalies;
DROP VIEW IF EXISTS vw_hourly_radiation_summary;


CREATE OR REPLACE VIEW vw_daily_radiation_summary AS

WITH current_settings AS (
    SELECT
        COALESCE(
            (
                SELECT value::double precision
                FROM app_settings
                WHERE key = 'threshold'
            ),
            0.18
        ) AS threshold,

        COALESCE(
            (
                SELECT CASE value
                    WHEN 'isolation_forest' THEN 'Isolation Forest'
                    WHEN 'lof' THEN 'Local Outlier Factor'
                    WHEN 'one_class_svm' THEN 'One-Class SVM'
                    WHEN 'dbscan' THEN 'DBSCAN'
                    WHEN 'kmeans_distance' THEN 'K-Means'
                    WHEN 'gaussian_mixture' THEN 'Gaussian Mixture Model'
                    WHEN 'pca_reconstruction' THEN 'PCA'
                    WHEN 'hbos' THEN 'HBOS'
                    WHEN 'ecod' THEN 'ECOD'
                    WHEN 'logistic_regression' THEN 'Logistic Regression'
                    WHEN 'decision_tree' THEN 'Decision Tree'
                    WHEN 'random_forest' THEN 'Random Forest'
                    WHEN 'gradient_boosting' THEN 'Gradient Boosting'
                    WHEN 'knn_classifier' THEN 'KNN Classifier'
                    ELSE 'Isolation Forest'
                END
                FROM app_settings
                WHERE key = 'active_model'
            ),
            'Isolation Forest'
        ) AS active_model
)

SELECT
    d.id AS dataset_id,
    d.name AS dataset_name,
    DATE(cm.timestamp) AS measurement_date,

    COUNT(cm.id) AS total_measurements,

    ROUND(
        AVG(cm.radiation_level)::numeric,
        4
    ) AS avg_radiation_level,

    ROUND(
        MIN(cm.radiation_level)::numeric,
        4
    ) AS min_radiation_level,

    ROUND(
        MAX(cm.radiation_level)::numeric,
        4
    ) AS max_radiation_level,

    ROUND(
        STDDEV_SAMP(cm.radiation_level)::numeric,
        4
    ) AS std_radiation_level,

    COALESCE(
        SUM(
            CASE
                WHEN cm.original_label = TRUE
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS original_anomalies,

    COALESCE(
        SUM(
            CASE
                WHEN ar.predicted_anomaly = TRUE
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS predicted_anomalies,

    COALESCE(
        SUM(
            CASE
                WHEN ar.predicted_anomaly = TRUE
                     AND cm.radiation_level >= cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS critical_events,

    COALESCE(
        SUM(
            CASE
                WHEN COALESCE(ar.predicted_anomaly, FALSE) = FALSE
                     AND cm.radiation_level >= cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS warning_events,

    COALESCE(
        SUM(
            CASE
                WHEN ar.predicted_anomaly = TRUE
                     AND cm.radiation_level < cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS ml_anomaly_events,

    COALESCE(
        SUM(
            CASE
                WHEN COALESCE(ar.predicted_anomaly, FALSE) = FALSE
                     AND cm.radiation_level < cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS normal_measurements

FROM datasets d

JOIN clean_measurements cm
    ON d.id = cm.dataset_id

LEFT JOIN feature_measurements fm
    ON cm.id = fm.clean_measurement_id

CROSS JOIN current_settings cs

LEFT JOIN anomaly_results ar
    ON fm.id = ar.feature_measurement_id
    AND ar.model_name = cs.active_model

GROUP BY
    d.id,
    d.name,
    DATE(cm.timestamp)

ORDER BY
    measurement_date;


CREATE OR REPLACE VIEW vw_hourly_radiation_summary AS

WITH current_settings AS (
    SELECT
        COALESCE(
            (
                SELECT value::double precision
                FROM app_settings
                WHERE key = 'threshold'
            ),
            0.18
        ) AS threshold,

        COALESCE(
            (
                SELECT CASE value
                    WHEN 'isolation_forest' THEN 'Isolation Forest'
                    WHEN 'lof' THEN 'Local Outlier Factor'
                    WHEN 'one_class_svm' THEN 'One-Class SVM'
                    WHEN 'dbscan' THEN 'DBSCAN'
                    WHEN 'kmeans_distance' THEN 'K-Means'
                    WHEN 'gaussian_mixture' THEN 'Gaussian Mixture Model'
                    WHEN 'pca_reconstruction' THEN 'PCA'
                    WHEN 'hbos' THEN 'HBOS'
                    WHEN 'ecod' THEN 'ECOD'
                    WHEN 'logistic_regression' THEN 'Logistic Regression'
                    WHEN 'decision_tree' THEN 'Decision Tree'
                    WHEN 'random_forest' THEN 'Random Forest'
                    WHEN 'gradient_boosting' THEN 'Gradient Boosting'
                    WHEN 'knn_classifier' THEN 'KNN Classifier'
                    ELSE 'Isolation Forest'
                END
                FROM app_settings
                WHERE key = 'active_model'
            ),
            'Isolation Forest'
        ) AS active_model
)

SELECT
    d.id AS dataset_id,
    d.name AS dataset_name,
    DATE(cm.timestamp) AS measurement_date,

    EXTRACT(
        HOUR FROM cm.timestamp
    )::integer AS hour_of_day,

    COUNT(cm.id) AS total_measurements,

    ROUND(
        AVG(cm.radiation_level)::numeric,
        4
    ) AS avg_radiation_level,

    ROUND(
        MIN(cm.radiation_level)::numeric,
        4
    ) AS min_radiation_level,

    ROUND(
        MAX(cm.radiation_level)::numeric,
        4
    ) AS max_radiation_level,

    COALESCE(
        SUM(
            CASE
                WHEN ar.predicted_anomaly = TRUE
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS predicted_anomalies,

    COALESCE(
        SUM(
            CASE
                WHEN ar.predicted_anomaly = TRUE
                     AND cm.radiation_level >= cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS critical_events,

    COALESCE(
        SUM(
            CASE
                WHEN COALESCE(ar.predicted_anomaly, FALSE) = FALSE
                     AND cm.radiation_level >= cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS warning_events,

    COALESCE(
        SUM(
            CASE
                WHEN ar.predicted_anomaly = TRUE
                     AND cm.radiation_level < cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS ml_anomaly_events

FROM datasets d

JOIN clean_measurements cm
    ON d.id = cm.dataset_id

LEFT JOIN feature_measurements fm
    ON cm.id = fm.clean_measurement_id

CROSS JOIN current_settings cs

LEFT JOIN anomaly_results ar
    ON fm.id = ar.feature_measurement_id
    AND ar.model_name = cs.active_model

GROUP BY
    d.id,
    d.name,
    DATE(cm.timestamp),
    EXTRACT(HOUR FROM cm.timestamp)

ORDER BY
    measurement_date,
    hour_of_day;


CREATE OR REPLACE VIEW vw_location_anomaly_summary AS

WITH current_settings AS (
    SELECT
        COALESCE(
            (
                SELECT value::double precision
                FROM app_settings
                WHERE key = 'threshold'
            ),
            0.18
        ) AS threshold,

        COALESCE(
            (
                SELECT CASE value
                    WHEN 'isolation_forest' THEN 'Isolation Forest'
                    WHEN 'lof' THEN 'Local Outlier Factor'
                    WHEN 'one_class_svm' THEN 'One-Class SVM'
                    WHEN 'dbscan' THEN 'DBSCAN'
                    WHEN 'kmeans_distance' THEN 'K-Means'
                    WHEN 'gaussian_mixture' THEN 'Gaussian Mixture Model'
                    WHEN 'pca_reconstruction' THEN 'PCA'
                    WHEN 'hbos' THEN 'HBOS'
                    WHEN 'ecod' THEN 'ECOD'
                    WHEN 'logistic_regression' THEN 'Logistic Regression'
                    WHEN 'decision_tree' THEN 'Decision Tree'
                    WHEN 'random_forest' THEN 'Random Forest'
                    WHEN 'gradient_boosting' THEN 'Gradient Boosting'
                    WHEN 'knn_classifier' THEN 'KNN Classifier'
                    ELSE 'Isolation Forest'
                END
                FROM app_settings
                WHERE key = 'active_model'
            ),
            'Isolation Forest'
        ) AS active_model
)

SELECT
    d.id AS dataset_id,
    d.name AS dataset_name,

    COALESCE(
        cm.location,
        'Unknown'
    ) AS location,

    COALESCE(
        cm.sensor_id,
        'UNKNOWN_SENSOR'
    ) AS sensor_id,

    COUNT(cm.id) AS total_measurements,

    ROUND(
        AVG(cm.radiation_level)::numeric,
        4
    ) AS avg_radiation_level,

    ROUND(
        MAX(cm.radiation_level)::numeric,
        4
    ) AS max_radiation_level,

    COALESCE(
        SUM(
            CASE
                WHEN cm.original_label = TRUE
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS original_anomalies,

    COALESCE(
        SUM(
            CASE
                WHEN ar.predicted_anomaly = TRUE
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS predicted_anomalies,

    COALESCE(
        SUM(
            CASE
                WHEN ar.predicted_anomaly = TRUE
                     AND cm.radiation_level >= cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS critical_events,

    COALESCE(
        SUM(
            CASE
                WHEN COALESCE(ar.predicted_anomaly, FALSE) = FALSE
                     AND cm.radiation_level >= cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS warning_events,

    COALESCE(
        SUM(
            CASE
                WHEN ar.predicted_anomaly = TRUE
                     AND cm.radiation_level < cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS ml_anomaly_events,

    COALESCE(
        SUM(
            CASE
                WHEN COALESCE(ar.predicted_anomaly, FALSE) = FALSE
                     AND cm.radiation_level < cs.threshold
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS normal_measurements

FROM datasets d

JOIN clean_measurements cm
    ON d.id = cm.dataset_id

LEFT JOIN feature_measurements fm
    ON cm.id = fm.clean_measurement_id

CROSS JOIN current_settings cs

LEFT JOIN anomaly_results ar
    ON fm.id = ar.feature_measurement_id
    AND ar.model_name = cs.active_model

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
            PARTITION BY
                mm.dataset_id,
                mm.model_name
            ORDER BY
                mm.created_at DESC
        ) AS row_number

    FROM model_metrics mm
)

SELECT
    d.id AS dataset_id,
    d.name AS dataset_name,
    rm.model_name,

    ROUND(
        rm.accuracy::numeric,
        4
    ) AS accuracy,

    ROUND(
        rm.precision_score::numeric,
        4
    ) AS precision_score,

    ROUND(
        rm.recall_score::numeric,
        4
    ) AS recall_score,

    ROUND(
        rm.f1_score::numeric,
        4
    ) AS f1_score,

    ROUND(
        rm.roc_auc::numeric,
        4
    ) AS roc_auc,

    ROUND(
        rm.pr_auc::numeric,
        4
    ) AS pr_auc,

    ROUND(
        rm.fpr::numeric,
        4
    ) AS fpr,

    ROUND(
        rm.fnr::numeric,
        4
    ) AS fnr,

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

WITH current_settings AS (
    SELECT
        COALESCE(
            (
                SELECT value::double precision
                FROM app_settings
                WHERE key = 'threshold'
            ),
            0.18
        ) AS threshold,

        COALESCE(
            (
                SELECT CASE value
                    WHEN 'isolation_forest' THEN 'Isolation Forest'
                    WHEN 'lof' THEN 'Local Outlier Factor'
                    WHEN 'one_class_svm' THEN 'One-Class SVM'
                    WHEN 'dbscan' THEN 'DBSCAN'
                    WHEN 'kmeans_distance' THEN 'K-Means'
                    WHEN 'gaussian_mixture' THEN 'Gaussian Mixture Model'
                    WHEN 'pca_reconstruction' THEN 'PCA'
                    WHEN 'hbos' THEN 'HBOS'
                    WHEN 'ecod' THEN 'ECOD'
                    WHEN 'logistic_regression' THEN 'Logistic Regression'
                    WHEN 'decision_tree' THEN 'Decision Tree'
                    WHEN 'random_forest' THEN 'Random Forest'
                    WHEN 'gradient_boosting' THEN 'Gradient Boosting'
                    WHEN 'knn_classifier' THEN 'KNN Classifier'
                    ELSE 'Isolation Forest'
                END
                FROM app_settings
                WHERE key = 'active_model'
            ),
            'Isolation Forest'
        ) AS active_model
)

SELECT
    d.id AS dataset_id,
    d.name AS dataset_name,
    ar.timestamp,
    ar.radiation_level,

    COALESCE(
        cm.sensor_id,
        'UNKNOWN_SENSOR'
    ) AS sensor_id,

    COALESCE(
        cm.location,
        'Unknown'
    ) AS location,

    cm.temperature,
    cm.humidity,
    cm.original_label,
    cm.anomaly_type,
    ar.predicted_anomaly,

    ROUND(
        ar.anomaly_score::numeric,
        4
    ) AS anomaly_score,

    CASE
        WHEN ar.predicted_anomaly = TRUE
             AND ar.radiation_level >= cs.threshold
        THEN 'Critical'

        WHEN ar.predicted_anomaly = TRUE
        THEN 'ML Anomaly'

        WHEN ar.radiation_level >= cs.threshold
        THEN 'Warning'

        ELSE 'Normal'
    END AS status,

    ar.model_name,
    ar.created_at

FROM anomaly_results ar

JOIN datasets d
    ON ar.dataset_id = d.id

JOIN feature_measurements fm
    ON ar.feature_measurement_id = fm.id

JOIN clean_measurements cm
    ON fm.clean_measurement_id = cm.id

CROSS JOIN current_settings cs

WHERE
    ar.model_name = cs.active_model
    AND (
        ar.predicted_anomaly = TRUE
        OR ar.radiation_level >= cs.threshold
    )

ORDER BY
    ar.timestamp DESC;