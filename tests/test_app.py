import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "DATABASE_PATH": str(tmp_path / "expenses.db"),
        }
    )
    with app.test_client() as test_client:
        yield test_client


def add_expense(client, **overrides):
    form = {
        "name": "Bus pass",
        "amount": "25.50",
        "category": "Travel",
        "date": "2025-01-15",
    }
    form.update(overrides)
    return client.post("/expenses/add", data=form, follow_redirects=True)


def test_dashboard_shows_expense_and_category_total(client):
    add_expense(client)

    response = client.get("/")

    assert response.status_code == 200
    assert b"Bus pass" in response.data
    assert b"Travel" in response.data
    assert b"25.50" in response.data


def test_rejects_invalid_amount_without_saving(client):
    response = add_expense(client, amount="-2")

    assert b"Enter a positive amount" in response.data
    assert b"Bus pass" not in client.get("/").data


def test_rejects_amount_with_more_than_two_decimal_places(client):
    response = add_expense(client, amount="1.234")

    assert b"Enter a positive amount" in response.data
    assert b"Bus pass" not in client.get("/").data


def test_delete_removes_expense(client):
    add_expense(client)

    response = client.post("/expenses/1/delete", follow_redirects=True)

    assert response.status_code == 200
    assert b"Bus pass" not in response.data
    assert b"No expenses yet" in response.data


def test_delete_missing_expense_returns_not_found(client):
    response = client.post("/expenses/999/delete")

    assert response.status_code == 404
