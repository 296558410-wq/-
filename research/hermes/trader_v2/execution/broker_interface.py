# -*- coding: utf-8 -*-
"""V2 Broker 抽象接口（模块 2）。

只定义标准接口; 具体实现见 paper_executor / fxtm_demo_adapter。
- 当前 Phase-1 只启用 LOCAL PAPER。
- 任何 broker 实现在未满足安全门时, 方法必须 raise RefuseConnection。
"""
from __future__ import annotations


class BrokerError(Exception):
    pass


class RefuseConnection(BrokerError):
    """安全门未满足 / 未启用 → 拒绝连接或下单。"""


class BrokerInterface:
    """所有执行后端(paper / broker demo)的统一接口。"""

    backend = "abstract"

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def get_account(self):
        raise NotImplementedError

    def get_balance(self):
        raise NotImplementedError

    def get_equity(self):
        raise NotImplementedError

    def get_quote(self, symbol):
        raise NotImplementedError

    def place_market_order(self, symbol, side, qty_lots, sl=None, tp=None):
        raise NotImplementedError

    def close_position(self, position_id, qty_lots=None):
        raise NotImplementedError

    def get_positions(self):
        raise NotImplementedError

    def get_order_status(self, order_id):
        raise NotImplementedError
