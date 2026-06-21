from functools import lru_cache
import pandas as pd

from app.services.csv_loader import load_raw_dataset
from app.services.data_mapper import (
    map_to_standard_measurements)


@lru_cache(maxsize=1)
def get_measurements_df() -> pd.DataFrame:
    raw_df = load_raw_dataset()
    return map_to_standard_measurements(raw_df)


def refresh_dataset_cache() -> None:
    get_measurements_df.cache_clear()