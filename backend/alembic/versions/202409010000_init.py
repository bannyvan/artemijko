from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '202409010000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('tg_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('role', sa.Enum('employee', 'manager', 'admin', name='userrole'), nullable=False, server_default='employee'),
        sa.Column('department_id', sa.Integer, nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', name='userstatus'), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_users_tg_id', 'users', ['tg_id'])

    op.create_table(
        'projects',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(64), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true')),
    )

    op.create_table(
        'shifts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('paused_at', sa.DateTime, nullable=True),
        sa.Column('resumed_at', sa.DateTime, nullable=True),
        sa.Column('finished_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.Enum('active', 'paused', 'finished', name='shiftstatus'), nullable=False, server_default='active'),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('note', sa.String(500), nullable=True),
    )
    op.create_index('ix_shifts_started_at', 'shifts', ['started_at'])
    op.create_index('ix_shifts_finished_at', 'shifts', ['finished_at'])
    op.create_index('ix_shifts_user_status', 'shifts', ['user_id', 'status'])

    op.create_table(
        'breaks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('shift_id', sa.Integer, sa.ForeignKey('shifts.id'), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('finished_at', sa.DateTime, nullable=True),
        sa.Column('type', sa.Enum('technical', 'lunch', 'personal', name='breaktype'), nullable=False),
    )

    op.create_table(
        'requests',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.Enum('vacation', 'dayoff', 'sick', name='requesttype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='requeststatus'), nullable=False, server_default='pending'),
        sa.Column('from_date', sa.DateTime, nullable=False),
        sa.Column('to_date', sa.DateTime, nullable=False),
        sa.Column('days', sa.Integer, nullable=False),
        sa.Column('approver_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('comment', sa.String(500), nullable=True),
    )
    op.create_index('ix_requests_user_id', 'requests', ['user_id'])

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.Integer, nullable=True),
        sa.Column('payload', sa.JSON, nullable=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='WebApp'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_audit_user_action', 'audit_log', ['user_id', 'action'])

    op.create_table(
        'idempotency_keys',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('key', sa.String(128), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('user_id', 'action', 'key', name='uq_idem_user_action_key'),
    )

    # seed data
    conn = op.get_bind()
    now = datetime.utcnow()
    conn.execute(sa.text("INSERT INTO users (tg_id, role, status, created_at) VALUES (:tg1, 'admin', 'active', :now), (:tg2, 'manager', 'active', :now), (:tg3, 'employee', 'active', :now), (:tg4, 'employee', 'active', :now)"), {"tg1": "1001", "tg2": "1002", "tg3": "1003", "tg4": "1004", "now": now})
    conn.execute(sa.text("INSERT INTO projects (name, code, is_active) VALUES ('Project Alpha','ALPHA', true), ('Project Beta','BETA', true)"))


def downgrade() -> None:
    op.drop_table('idempotency_keys')
    op.drop_index('ix_audit_user_action', table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_index('ix_requests_user_id', table_name='requests')
    op.drop_table('requests')
    op.drop_table('breaks')
    op.drop_index('ix_shifts_user_status', table_name='shifts')
    op.drop_index('ix_shifts_finished_at', table_name='shifts')
    op.drop_index('ix_shifts_started_at', table_name='shifts')
    op.drop_table('shifts')
    op.drop_table('projects')
    op.drop_index('ix_users_tg_id', table_name='users')
    op.drop_table('users')