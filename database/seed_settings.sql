INSERT INTO app_settings (key, value)
VALUES
    ('threshold', '0.18'),
    ('active_dataset_id', '1'),
    ('active_model', 'Isolation Forest')
    ON CONFLICT (key) DO UPDATE
                             SET
                             value = EXCLUDED.value,
                             updated_at = CURRENT_TIMESTAMP;