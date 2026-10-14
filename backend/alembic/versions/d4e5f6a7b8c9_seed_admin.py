"""seed: usuario administrador inicial (solo si ADMIN_INITIAL_PASSWORD esta definido)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""
import os

from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    password = os.environ.get("ADMIN_INITIAL_PASSWORD")
    username = os.environ.get("ADMIN_INITIAL_USERNAME", "admin")
    if not password:
        return
    import bcrypt

    pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    op.execute(
        sa.text(
            """
            INSERT INTO config.usuarios (username, password_hash, email, rol, auth_type)
            VALUES (:u, :h, 'admin@cujae.edu.cu', 'administrador', 'local')
            ON CONFLICT (username) DO NOTHING
            """
        ).bindparams(u=username, h=pwd_hash)
    )


def downgrade() -> None:
    username = os.environ.get("ADMIN_INITIAL_USERNAME", "admin")
    op.execute(
        sa.text("DELETE FROM config.usuarios WHERE username = :u AND rol = 'administrador'").bindparams(
            u=username
        )
    )
