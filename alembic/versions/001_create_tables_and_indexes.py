"""Create tables and indexes for Fleet Ops Console

Revision ID: 001
Revises:
Create Date: 2026-06-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("device_type", sa.String(), nullable=False),
        sa.Column("hardware_version", sa.String(), nullable=False),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("api_key_hash", sa.String(), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "telemetry_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id"), nullable=False, index=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("battery_level", sa.Float(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.Column("signal_strength", sa.Float(), nullable=True),
        sa.Column("cpu_temp", sa.Float(), nullable=True),
        sa.Column("payload", postgresql.JSONB, default=dict),
        sa.UniqueConstraint("device_id", "recorded_at", name="uq_telemetry_device_time"),
        sa.CheckConstraint(
            "battery_level IS NULL OR (battery_level >= 0 AND battery_level <= 100)",
            name="ck_telemetry_battery_range",
        ),
    )

    op.create_table(
        "actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False, unique=True),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB, default=dict),
        sa.Column("status", sa.String(), nullable=False, default="PENDING"),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index(
        "idx_devices_list",
        "devices",
        ["status", sa.text("last_seen DESC"), "id"],
        postgresql_where=sa.text("status != 'decommissioned'"),
    )
    op.create_index(
        "idx_devices_active",
        "devices",
        [sa.text("last_seen DESC")],
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_devices_fts",
        "devices",
        [sa.text("to_tsvector('english', name || ' ' || COALESCE(region, ''))")],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_telemetry_device_time",
        "telemetry_events",
        ["device_id", sa.text("recorded_at DESC")],
    )
    op.create_index(
        "idx_actions_device",
        "actions",
        ["device_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_table("actions")
    op.drop_table("telemetry_events")
    op.drop_table("devices")
