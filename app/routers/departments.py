import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Department, Employee
from app.schemas import DepartmentCreate, DepartmentOut, DepartmentTree, DepartmentUpdate, EmployeeCreate, EmployeeOut

router = APIRouter(prefix="/departments", tags=["departments"])
logger = logging.getLogger(__name__)


async def get_dept_or_404(db: AsyncSession, dept_id: int) -> Department:
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=404, detail=f"Department {dept_id} not found")
    return dept


async def check_name_unique(db: AsyncSession, name: str, parent_id: int | None, exclude_id: int | None = None) -> None:
    stmt = select(Department).where(and_(Department.name == name, Department.parent_id == parent_id))
    if exclude_id:
        stmt = stmt.where(Department.id != exclude_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Department '{name}' already exists under this parent",
        )


async def check_no_cycle(db: AsyncSession, dept_id: int, new_parent_id: int) -> None:
    current_id: int | None = new_parent_id
    while current_id is not None:
        if current_id == dept_id:
            raise HTTPException(status_code=409, detail="This would create a cycle in the tree")
        result = await db.execute(select(Department.parent_id).where(Department.id == current_id))
        row = result.one_or_none()
        current_id = row[0] if row else None


async def build_tree(db: AsyncSession, dept: Department, depth: int, include_employees: bool, sort_by: str) -> DepartmentTree:
    employees = []
    if include_employees:
        stmt = select(Employee).where(Employee.department_id == dept.id)
        stmt = stmt.order_by(Employee.full_name if sort_by == "full_name" else Employee.created_at)
        result = await db.execute(stmt)
        employees = [EmployeeOut.model_validate(e) for e in result.scalars().all()]

    children = []
    if depth > 0:
        result = await db.execute(select(Department).where(Department.parent_id == dept.id))
        for child in result.scalars().all():
            children.append(await build_tree(db, child, depth - 1, include_employees, sort_by))

    return DepartmentTree(id=dept.id, name=dept.name, parent_id=dept.parent_id, created_at=dept.created_at, employees=employees, children=children)


@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
async def create_department(data: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    logger.info("Creating department: %s", data.name)

    if data.parent_id is not None:
        await get_dept_or_404(db, data.parent_id)

    await check_name_unique(db, data.name, data.parent_id)

    dept = Department(name=data.name, parent_id=data.parent_id)
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    return DepartmentOut.model_validate(dept)


@router.get("/{dept_id}", response_model=DepartmentTree)
async def get_department(dept_id: int, depth: int = Query(default=1, ge=0, le=5), include_employees: bool = Query(default=True), sort_employees_by: Literal["created_at", "full_name"] = Query(default="created_at"), db: AsyncSession = Depends(get_db)):
    dept = await get_dept_or_404(db, dept_id)
    return await build_tree(db, dept, depth, include_employees, sort_employees_by)


@router.patch("/{dept_id}", response_model=DepartmentOut)
async def update_department(dept_id: int, data: DepartmentUpdate, db: AsyncSession = Depends(get_db)):
    dept = await get_dept_or_404(db, dept_id)

    if data.name is not None and data.name != dept.name:
        await check_name_unique(db, data.name, dept.parent_id, exclude_id=dept_id)
        dept.name = data.name

    if "parent_id" in data.model_fields_set:
        new_parent_id = data.parent_id
        if new_parent_id == dept_id:
            raise HTTPException(status_code=409, detail="Department cannot be its own parent")
        if new_parent_id is not None:
            await get_dept_or_404(db, new_parent_id)
            await check_no_cycle(db, dept_id, new_parent_id)
        dept.parent_id = new_parent_id

    await db.flush()
    await db.refresh(dept)
    return DepartmentOut.model_validate(dept)


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(dept_id: int, mode: Literal["cascade", "reassign"] = Query(...), reassign_to_department_id: int | None = Query(default=None), db: AsyncSession = Depends(get_db)):
    dept = await get_dept_or_404(db, dept_id)

    if mode == "reassign":
        if reassign_to_department_id is None:
            raise HTTPException(status_code=422, detail="reassign_to_department_id is required when mode=reassign")
        target = await get_dept_or_404(db, reassign_to_department_id)
        result = await db.execute(select(Employee).where(Employee.department_id == dept_id))
        for emp in result.scalars().all():
            emp.department_id = target.id
        await db.flush()

    logger.info("Deleting department %d mode=%s", dept_id, mode)
    await db.delete(dept)


@router.post("/{dept_id}/employees/", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(dept_id: int, data: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    await get_dept_or_404(db, dept_id)

    emp = Employee(department_id=dept_id, full_name=data.full_name, position=data.position, hired_at=data.hired_at)
    db.add(emp)
    await db.flush()
    await db.refresh(emp)
    return EmployeeOut.model_validate(emp)