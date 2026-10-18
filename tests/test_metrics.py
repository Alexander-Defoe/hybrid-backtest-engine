import numpy as np

from src.metrics import summarise, buy_and_hold


def test_summarise_flat_curve():
    # An account that never moves has no profit, no risk and no drawdown
    stats = summarise([10000.0] * 10)

    assert stats['final_equity'] == 10000.0
    assert stats['total_return'] == 0.0
    assert stats['sharpe'] == 0.0
    assert stats['max_drawdown'] == 0.0


def test_summarise_total_return():
    stats = summarise([10000.0, 11000.0, 12000.0])
    assert stats['total_return'] == 0.2
    assert stats['final_equity'] == 12000.0


def test_summarise_max_drawdown():
    # Peaks at 12000 then falls to 9000, a drop of 25% from the peak
    stats = summarise([10000.0, 12000.0, 9000.0, 11000.0])
    assert stats['max_drawdown'] == -0.25


def test_summarise_handles_short_curve():
    # Should not crash when there are not enough days to measure anything
    assert summarise([10000.0])['sharpe'] == 0.0
    assert summarise([])['final_equity'] == 0.0


def test_buy_and_hold_uses_whole_shares():
    # 5000 per stock. 5000 // 100 = 50 shares of A, 5000 // 250 = 20 shares of B.
    # Final value is 50 * 150 + 20 * 250 = 12500
    close_matrix = np.array([[100.0, 250.0], [150.0, 250.0]])
    assert buy_and_hold(close_matrix, ['A', 'B'], 10000.0) == 12500.0
