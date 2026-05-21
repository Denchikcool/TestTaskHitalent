from typing import Sequence, Union
from alembic import op

revision: str = "002_unique_name"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE UNIQUE INDEX uq_dept_name_parent
        ON departments (name, parent_id)
        WHERE parent_id IS NOT NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_dept_name_root
        ON departments (name)
        WHERE parent_id IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_dept_name_parent")
    op.execute("DROP INDEX IF EXISTS uq_dept_name_root")