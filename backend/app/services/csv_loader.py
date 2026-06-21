import pandas as pd
from app.utils.paths import DEFAULT_DATASET_PATH


def load_raw_dataset() -> pd.DataFrame:
    """
    Ucitava trenutno aktivni CSV dataset.

    Sada koristimo mock CSV. Kada stigne realni CSV iz Vince,
    najcesce ce se promeniti samo fajl i mapiranje kolona u data_mapper.py.
    """
    if not DEFAULT_DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset nije pronadjen: {DEFAULT_DATASET_PATH}")

    return pd.read_csv(DEFAULT_DATASET_PATH)