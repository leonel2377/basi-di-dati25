from inventory_tracker.status import StatusThresholds, StockStatus, classify_stock_level


def test_classify_stock_level_green():
    thresholds = StatusThresholds(reorder_point=20, critical_point=5)
    assert classify_stock_level(50, thresholds) is StockStatus.GREEN


def test_classify_stock_level_orange():
    thresholds = StatusThresholds(reorder_point=20, critical_point=5)
    assert classify_stock_level(10, thresholds) is StockStatus.ORANGE


def test_classify_stock_level_red():
    thresholds = StatusThresholds(reorder_point=20, critical_point=5)
    assert classify_stock_level(3, thresholds) is StockStatus.RED

