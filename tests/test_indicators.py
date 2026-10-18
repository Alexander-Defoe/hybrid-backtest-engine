import numpy as np
import pandas as pd
import pytest

import my_cpp_module

# 300 days of made-up prices for 3 stocks, each moving about 1% a day. The seed is fixed
# so every run of the tests sees exactly the same prices.
rng = np.random.default_rng(42)
PRICES = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, (300, 3)), axis=0))


def test_sma_matches_pandas():
    window = 20
    result = my_cpp_module.calculate_smas(PRICES, window)
    expected = pd.DataFrame(PRICES).rolling(window).mean().to_numpy()

    # The days before the first full window are padded with zeros
    assert np.all(result[:window - 1] == 0.0)
    np.testing.assert_allclose(result[window - 1:], expected[window - 1:], rtol=1e-10)


def test_macd_matches_pandas():
    # The MACD line is the fast exponential average minus the slow one, both started
    # from the first day's price, which is what pandas does with adjust=False
    result = my_cpp_module.calculate_macd(PRICES, 12, 26)
    df = pd.DataFrame(PRICES)
    expected = (df.ewm(span=12, adjust=False).mean() - df.ewm(span=26, adjust=False).mean()).to_numpy()

    np.testing.assert_allclose(result, expected, rtol=1e-10, atol=1e-10)


def test_volatility_matches_pandas():
    # Standard deviation of the daily returns over the window, once a full window exists
    window = 20
    result = my_cpp_module.calculate_volatility(PRICES, window)
    expected = pd.DataFrame(PRICES).pct_change().rolling(window).std(ddof=0).to_numpy()

    np.testing.assert_allclose(result[window:], np.maximum(expected[window:], 0.001), rtol=1e-10)


def test_column_ordered_input_gives_same_result():
    # The same prices stored column by column in memory must still give the same answer,
    # rather than the C++ code reading the numbers in the wrong order
    column_ordered = np.asfortranarray(PRICES)
    assert not column_ordered.flags['C_CONTIGUOUS']

    np.testing.assert_array_equal(
        my_cpp_module.calculate_smas(column_ordered, 20),
        my_cpp_module.calculate_smas(PRICES, 20),
    )


def test_bad_input_raises_instead_of_crashing():
    # A window longer than the price history used to write past the end of the array
    with pytest.raises(ValueError):
        my_cpp_module.calculate_smas(PRICES, 1000)

    # A single list of prices has no stock columns to work through
    with pytest.raises(ValueError):
        my_cpp_module.calculate_smas(PRICES[:, 0], 20)
