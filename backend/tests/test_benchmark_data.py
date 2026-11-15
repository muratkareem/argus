"""Small explicit fixtures verify adapters; they are never benchmark evidence."""

import numpy as np
import pandas as pd
import pytest
from app.benchmark_data import merge_identity, prepare, preprocessor, read_source


def paysim_fixture(n=120):
    return pd.DataFrame(
        {
            "step": np.arange(n) // 3,
            "type": ["TRANSFER", "PAYMENT"] * (n // 2),
            "amount": np.arange(n) + 1.0,
            "nameOrig": [f"C{i}" for i in range(n)],
            "nameDest": [f"D{i}" for i in range(n)],
            "oldbalanceOrg": 999.0,
            "newbalanceOrig": 0.0,
            "oldbalanceDest": 0.0,
            "newbalanceDest": 999.0,
            "isFraud": np.arange(n) % 3 == 0,
            "isFlaggedFraud": 0,
        }
    ).astype({"isFraud": int})


def ieee_fixture():
    return pd.DataFrame(
        {
            "TransactionID": [1, 2, 3],
            "TransactionDT": [1.0, 2.0, 3.0],
            "TransactionAmt": [1.0, 9.0, 10000.0],
            "ProductCD": ["W", "W", "X"],
            "isFraud": [0, 1, 0],
            "V1": [np.nan, 2.0, np.nan],
        }
    )


def test_paysim_excludes_post_outcome_balances_policy_and_identifiers():
    raw = paysim_fixture()
    data = prepare(raw, "paysim")
    assert list(data.x) == ["amount", "log_amount", "type"]
    altered = raw.copy()
    altered["newbalanceOrig"] = 1e9
    altered["isFlaggedFraud"] = 1
    pd.testing.assert_frame_equal(data.x, prepare(altered, "paysim").x)
    duplicate = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
    assert prepare(duplicate, "paysim").duplicates_removed == 1
    duplicate.loc[len(raw), "isFraud"] = 1 - raw.isFraud.iloc[0]
    with pytest.raises(ValueError, match="Conflicting"):
        prepare(duplicate, "paysim")


def test_ieee_preprocessing_is_train_only_and_unseen_categories_are_safe():
    data = prepare(ieee_fixture(), "ieee_cis")
    transform = preprocessor(data)
    transform.fit(data.x.iloc[:2])
    imputer = transform.named_transformers_["numeric"].named_steps["simpleimputer"]
    assert list(imputer.statistics_) == [5.0, 2.0]
    encoder = transform.named_transformers_["categorical"].named_steps["onehotencoder"]
    assert list(encoder.categories_[0]) == ["W"]
    assert transform.transform(data.x.iloc[[2]]).shape[1] == 3
    assert "TransactionID" not in data.x and "TransactionDT" not in data.x


def test_identity_join_is_one_to_one_and_missing_identities_are_allowed():
    frame = ieee_fixture()
    identity = pd.DataFrame({"TransactionID": [1], "DeviceInfo": ["device"]})
    joined = merge_identity(frame, identity)
    assert len(joined) == 3 and joined.DeviceInfo.isna().sum() == 2
    assert prepare(joined, "ieee_cis").x.DeviceInfo.notna().sum() == 1
    with pytest.raises(ValueError, match="unique"):
        merge_identity(frame, pd.concat([identity, identity]))
    with pytest.raises(ValueError, match="overlap"):
        merge_identity(frame, frame[["TransactionID", "isFraud"]])


@pytest.mark.parametrize("dataset", ["paysim", "ieee_cis"])
def test_invalid_labels_and_times_rejected(dataset):
    frame = paysim_fixture() if dataset == "paysim" else ieee_fixture()
    frame.loc[0, "isFraud"] = 2
    with pytest.raises(ValueError, match="binary"):
        prepare(frame, dataset)
    frame.loc[0, "isFraud"] = 0
    frame.loc[0, "step" if dataset == "paysim" else "TransactionDT"] = -1
    with pytest.raises(ValueError, match="nonnegative"):
        prepare(frame, dataset)


def test_uniform_sampling_reproducible_scans_complete_source(tmp_path):
    frame = paysim_fixture(120)
    path = tmp_path / "data.csv"
    frame.to_csv(path, index=False)
    first, audit = read_source(path, 30)
    second, _ = read_source(path, 30)
    pd.testing.assert_frame_equal(first, second)
    assert audit["rows"] == 120 and audit["fraud_rows"] == 40
    assert len(first) == 30 and first.step.astype(int).max() > 30
    assert len(audit["csv_sha256"]) == 64
    assert path.read_text().startswith("step,")


def test_chunked_paysim_matches_full_adapter_and_catches_cross_chunk_conflicts(tmp_path):
    from app.benchmark_data import read_paysim

    raw = paysim_fixture()
    raw = pd.concat([raw, raw.iloc[[0, 5]]], ignore_index=True)
    path = tmp_path / "raw.csv"
    raw.to_csv(path, index=False)
    expected = prepare(read_source(path)[0], "paysim")
    streamed, audit = read_paysim(path, chunksize=23)
    pd.testing.assert_frame_equal(
        streamed.x.assign(type=streamed.x.type.astype(object)), expected.x
    )
    pd.testing.assert_series_equal(streamed.fingerprints, expected.fingerprints)
    pd.testing.assert_series_equal(streamed.y, expected.y)
    assert streamed.duplicates_removed == 2 and audit["rows"] == 122
    assert audit["fraud_rows"] == int(raw.isFraud.sum())
    assert audit["prepared_bytes"] < 10000
    raw.loc[120, "isFraud"] = 1 - raw.loc[120, "isFraud"]
    raw.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Conflicting.*across chunks"):
        read_paysim(path, chunksize=23)
