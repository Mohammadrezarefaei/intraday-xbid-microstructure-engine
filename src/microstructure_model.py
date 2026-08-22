import numpy as np
import pandas as pd


def compute_micro_price(best_bid: np.ndarray, best_ask: np.ndarray, bid_depth: np.ndarray, ask_depth: np.ndarray) -> np.ndarray:
    """
    Calculates L2 volume-weighted micro-price:
    MicroPrice = (BestBid * AskDepth + BestAsk * BidDepth) / (BidDepth + AskDepth)
    """
    total_depth = bid_depth + ask_depth
    return (best_bid * ask_depth + best_ask * bid_depth) / np.maximum(total_depth, 1e-6)


def compute_order_flow_imbalance(bid_depth: np.ndarray, ask_depth: np.ndarray) -> np.ndarray:
    """
    Calculates normalized Order Flow Imbalance (OFI) in range [-1, +1].
    OFI = (BidDepth - AskDepth) / (BidDepth + AskDepth)
    """
    total_depth = bid_depth + ask_depth
    return (bid_depth - ask_depth) / np.maximum(total_depth, 1e-6)
