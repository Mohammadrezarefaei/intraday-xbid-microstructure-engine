import numpy as np
from src.microstructure_model import compute_micro_price, compute_order_flow_imbalance
from src.orderbook_simulator import simulate_xbid_orderbook


def test_micro_price_bounded_by_spread():
    bid = np.array([80.0, 90.0])
    ask = np.array([82.0, 92.0])
    bid_d = np.array([10.0, 50.0])
    ask_d = np.array([10.0, 10.0])

    micro_p = compute_micro_price(bid, ask, bid_d, ask_d)
    assert (micro_p >= bid).all()
    assert (micro_p <= ask).all()


def test_ofi_range():
    bid_d = np.array([100.0, 0.0, 50.0])
    ask_d = np.array([0.0, 100.0, 50.0])
    ofi = compute_order_flow_imbalance(bid_d, ask_d)

    assert ofi[0] == 1.0
    assert ofi[1] == -1.0
    assert ofi[2] == 0.0


def test_orderbook_simulation_completeness():
    df = simulate_xbid_orderbook(n_minutes=60)
    assert len(df) == 60
    assert (df["spread_eur"] > 0).all()
    assert (df["vwap_eur"] > 0).all()
