from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "Student Management API"
    assert data["status"] == "running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_list_students():
    response = client.get("/students")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_student_crud_lifecycle():
    # Create a new student
    create_resp = client.post(
        "/students",
        json={"name": "Rohan", "course": "Cloud Computing", "semester": 5},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    student_id = created["id"]
    assert created["name"] == "Rohan"
    assert created["course"] == "Cloud Computing"
    assert created["semester"] == 5

    # Read the created student
    get_resp = client.get(f"/students/{student_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == student_id

    # Update the student
    update_resp = client.put(
        f"/students/{student_id}",
        json={"course": "DevOps Engineering", "semester": 6},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["course"] == "DevOps Engineering"
    assert updated["semester"] == 6

    # Delete the student
    delete_resp = client.delete(f"/students/{student_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    # Confirm deletion returns 404
    missing_resp = client.get(f"/students/{student_id}")
    assert missing_resp.status_code == 404


def test_missing_student_returns_404():
    assert client.get("/students/99999").status_code == 404
    assert client.put("/students/99999", json={"name": "Ghost"}).status_code == 404
    assert client.delete("/students/99999").status_code == 404


if __name__ == "__main__":
    test_root()
    test_health()
    test_list_students()
    test_student_crud_lifecycle()
    test_missing_student_returns_404()
    print("All API route tests passed.")
