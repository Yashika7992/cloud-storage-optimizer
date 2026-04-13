from backend.cost_calculator import calculate_cost

def test_cost():
    current, ia, glacier = calculate_cost(10)

    assert round(current, 2) == 0.23
    assert round(ia, 2) == 0.12   # ✅ fixed
    assert round(glacier, 2) == 0.04