import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestCreateDepartment:
    async def test_create_root(self, client: AsyncClient):
        r = await client.post("/api/v1/departments/", json={"name": "Engineering"})
        assert r.status_code == 201
        assert r.json()["name"] == "Engineering"
        assert r.json()["parent_id"] is None

    async def test_create_child(self, client: AsyncClient):
        parent = await client.post("/api/v1/departments/", json={"name": "Product"})
        parent_id = parent.json()["id"]

        r = await client.post("/api/v1/departments/", json={"name": "Backend", "parent_id": parent_id})
        assert r.status_code == 201
        assert r.json()["parent_id"] == parent_id

    async def test_name_gets_trimmed(self, client: AsyncClient):
        r = await client.post("/api/v1/departments/", json={"name": "  HR  "})
        assert r.status_code == 201
        assert r.json()["name"] == "HR"

    async def test_empty_name_fails(self, client: AsyncClient):
        r = await client.post("/api/v1/departments/", json={"name": "   "})
        assert r.status_code == 422

    async def test_nonexistent_parent_fails(self, client: AsyncClient):
        r = await client.post("/api/v1/departments/", json={"name": "Ghost", "parent_id": 99999})
        assert r.status_code == 404

    async def test_duplicate_name_same_parent_fails(self, client: AsyncClient):
        parent = await client.post("/api/v1/departments/", json={"name": "Sales"})
        pid = parent.json()["id"]
        await client.post("/api/v1/departments/", json={"name": "Inside Sales", "parent_id": pid})
        r = await client.post("/api/v1/departments/", json={"name": "Inside Sales", "parent_id": pid})
        assert r.status_code == 409


class TestGetDepartment:
    async def test_get_with_tree_and_employees(self, client: AsyncClient):
        root = await client.post("/api/v1/departments/", json={"name": "Root"})
        root_id = root.json()["id"]
        child = await client.post("/api/v1/departments/", json={"name": "Child", "parent_id": root_id})
        await client.post(f"/api/v1/departments/{root_id}/employees/", json={"full_name": "Alice", "position": "Dev"})

        r = await client.get(f"/api/v1/departments/{root_id}?depth=2")
        assert r.status_code == 200
        data = r.json()
        assert len(data["employees"]) == 1
        assert data["children"][0]["id"] == child.json()["id"]

    async def test_not_found(self, client: AsyncClient):
        r = await client.get("/api/v1/departments/99999")
        assert r.status_code == 404

    async def test_exclude_employees(self, client: AsyncClient):
        dept = await client.post("/api/v1/departments/", json={"name": "Finance"})
        dept_id = dept.json()["id"]
        await client.post(f"/api/v1/departments/{dept_id}/employees/", json={"full_name": "Bob", "position": "CFO"})

        r = await client.get(f"/api/v1/departments/{dept_id}?include_employees=false")
        assert r.json()["employees"] == []

    async def test_depth_over_5_fails(self, client: AsyncClient):
        r = await client.get("/api/v1/departments/1?depth=10")
        assert r.status_code == 422


class TestUpdateDepartment:
    async def test_rename(self, client: AsyncClient):
        dept = await client.post("/api/v1/departments/", json={"name": "OldName"})
        dept_id = dept.json()["id"]

        r = await client.patch(f"/api/v1/departments/{dept_id}", json={"name": "NewName"})
        assert r.status_code == 200
        assert r.json()["name"] == "NewName"

    async def test_self_parent_fails(self, client: AsyncClient):
        dept = await client.post("/api/v1/departments/", json={"name": "Solo"})
        dept_id = dept.json()["id"]

        r = await client.patch(f"/api/v1/departments/{dept_id}", json={"parent_id": dept_id})
        assert r.status_code == 409

    async def test_cycle_fails(self, client: AsyncClient):
        a = await client.post("/api/v1/departments/", json={"name": "CycleA"})
        a_id = a.json()["id"]
        b = await client.post("/api/v1/departments/", json={"name": "CycleB", "parent_id": a_id})
        b_id = b.json()["id"]

        r = await client.patch(f"/api/v1/departments/{a_id}", json={"parent_id": b_id})
        assert r.status_code == 409


class TestDeleteDepartment:
    async def test_cascade_delete(self, client: AsyncClient):
        dept = await client.post("/api/v1/departments/", json={"name": "ToDelete"})
        dept_id = dept.json()["id"]
        await client.post(f"/api/v1/departments/{dept_id}/employees/", json={"full_name": "Eve", "position": "Dev"})

        r = await client.delete(f"/api/v1/departments/{dept_id}?mode=cascade")
        assert r.status_code == 204
        assert (await client.get(f"/api/v1/departments/{dept_id}")).status_code == 404

    async def test_reassign(self, client: AsyncClient):
        src = await client.post("/api/v1/departments/", json={"name": "Source"})
        src_id = src.json()["id"]
        tgt = await client.post("/api/v1/departments/", json={"name": "Target"})
        tgt_id = tgt.json()["id"]
        emp = await client.post(f"/api/v1/departments/{src_id}/employees/", json={"full_name": "Charlie", "position": "Analyst"})
        emp_id = emp.json()["id"]

        r = await client.delete(f"/api/v1/departments/{src_id}?mode=reassign&reassign_to_department_id={tgt_id}")
        assert r.status_code == 204

        tgt_data = await client.get(f"/api/v1/departments/{tgt_id}")
        assert any(e["id"] == emp_id for e in tgt_data.json()["employees"])

    async def test_reassign_without_target_fails(self, client: AsyncClient):
        dept = await client.post("/api/v1/departments/", json={"name": "Orphan"})
        r = await client.delete(f"/api/v1/departments/{dept.json()['id']}?mode=reassign")
        assert r.status_code == 422


class TestCreateEmployee:
    async def test_create(self, client: AsyncClient):
        dept = await client.post("/api/v1/departments/", json={"name": "DevTeam"})
        dept_id = dept.json()["id"]

        r = await client.post(f"/api/v1/departments/{dept_id}/employees/", json={
            "full_name": "Diana Prince", "position": "Lead", "hired_at": "2023-06-15"
        })
        assert r.status_code == 201
        assert r.json()["hired_at"] == "2023-06-15"

    async def test_nonexistent_dept_fails(self, client: AsyncClient):
        r = await client.post("/api/v1/departments/99999/employees/", json={"full_name": "Ghost", "position": "Nobody"})
        assert r.status_code == 404

    async def test_empty_name_fails(self, client: AsyncClient):
        dept = await client.post("/api/v1/departments/", json={"name": "QA"})
        r = await client.post(f"/api/v1/departments/{dept.json()['id']}/employees/", json={"full_name": "", "position": "Tester"})
        assert r.status_code == 422