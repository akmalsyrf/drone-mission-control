"""Initial schema: drones, missions, waypoints, telemetry_records."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("adapter_type", sa.String(32), nullable=False),
        sa.Column("connection_uri", sa.Text(), nullable=False),
        sa.Column("connection_status", sa.String(32), nullable=False),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True)),
        sa.Column("current_mission_id", postgresql.UUID(as_uuid=True)),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "missions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("drone_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drones.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("progress_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "waypoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="CASCADE")),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("latitude_deg", sa.Float(), nullable=False),
        sa.Column("longitude_deg", sa.Float(), nullable=False),
        sa.Column("altitude_m", sa.Float(), nullable=False),
        sa.Column("hold_seconds", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_table(
        "telemetry_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("drone_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drones.id", ondelete="CASCADE")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude_deg", sa.Float()),
        sa.Column("longitude_deg", sa.Float()),
        sa.Column("altitude_m", sa.Float()),
        sa.Column("heading_deg", sa.Float()),
        sa.Column("speed_m_s", sa.Float()),
        sa.Column("battery_percent", sa.Float()),
        sa.Column("flight_mode", sa.String(32)),
        sa.Column("armed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_table("telemetry_records")
    op.drop_table("waypoints")
    op.drop_table("missions")
    op.drop_table("drones")
