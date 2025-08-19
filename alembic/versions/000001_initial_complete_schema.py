"""Initial complete schema migration

Revision ID: 000001
Revises: 
Create Date: 2025-01-19 00:00:00.000000

This is a complete squashed migration that includes all tables from the OriginFlow system.
All previous migrations have been consolidated into this single initial migration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON, DateTime, func


# revision identifiers, used by Alembic.
revision: str = '000001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complete OriginFlow database schema."""
    
    # 1. Users table (auth)
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('hashed_password', sa.String(length=1024), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('organization', sa.String(length=200), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('permissions', JSON, nullable=True),
        sa.Column('created_at', DateTime(timezone=True), server_default=func.now()),
        sa.Column('last_login', DateTime(timezone=True), nullable=True),
        sa.Column('is_locked', sa.Boolean(), nullable=False),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # 2. Schematic Components table (main components)
    op.create_table(
        'schematic_components',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('standard_code', sa.String(), nullable=True),
        sa.Column('x', sa.Integer(), nullable=False, default=100),
        sa.Column('y', sa.Integer(), nullable=False, default=100),
        sa.Column('layer', sa.String(), nullable=False, default='Single-Line Diagram'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schematic_components_id'), 'schematic_components', ['id'], unique=True)
    op.create_index(op.f('ix_schematic_components_name'), 'schematic_components', ['name'])
    op.create_index(op.f('ix_schematic_components_standard_code'), 'schematic_components', ['standard_code'], unique=True)
    
    # 3. Links table (connections between components)
    op.create_table(
        'links',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('path_by_layer', JSON, nullable=True),
        sa.Column('locked_in_layers', JSON, nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['schematic_components.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['schematic_components.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_links_id'), 'links', ['id'], unique=True)
    
    # 4. File Assets table
    op.create_table(
        'file_assets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('mime', sa.String(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('parent_asset_id', sa.String(), nullable=True),
        sa.Column('component_id', sa.String(), nullable=True),
        sa.Column('uploaded_at', DateTime(timezone=True), server_default=func.now()),
        sa.Column('parsed_payload', JSON, nullable=True),
        sa.Column('parsed_at', DateTime(timezone=True), nullable=True),
        sa.Column('parsing_status', sa.String(), nullable=True),
        sa.Column('parsing_error', sa.Text(), nullable=True),
        sa.Column('is_human_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_extracted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('needs_manual_name_review', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['component_id'], ['schematic_components.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_assets_id'), 'file_assets', ['id'])
    
    # 5. Component Master table
    op.create_table(
        'component_master',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('part_number', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('manufacturer', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('voltage', sa.Float(), nullable=True),
        sa.Column('current', sa.Float(), nullable=True),
        sa.Column('power', sa.Float(), nullable=True),
        sa.Column('specs', JSON, nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('availability', sa.Integer(), nullable=True),
        sa.Column('deprecated', sa.Boolean(), default=False),
        sa.Column('ports', JSON, nullable=True),
        sa.Column('dependencies', JSON, nullable=True),
        sa.Column('layer_affinity', JSON, nullable=True),
        sa.Column('sub_elements', JSON, nullable=True),
        sa.Column('series', sa.String(), nullable=True),
        sa.Column('variants', JSON, nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_component_master_part_number'), 'component_master', ['part_number'], unique=True)
    op.create_index(op.f('ix_component_master_name'), 'component_master', ['name'])
    op.create_index(op.f('ix_component_master_manufacturer'), 'component_master', ['manufacturer'])
    op.create_index(op.f('ix_component_master_category'), 'component_master', ['category'])
    
    # 6. Hierarchical Components table
    op.create_table(
        'components',
        sa.Column('base_id', sa.String(), nullable=False),
        sa.Column('variant_id', sa.String(), nullable=True),
        sa.Column('is_base_component', sa.Boolean(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('domain', JSON, nullable=False),
        sa.Column('brand', sa.String(), nullable=False),
        sa.Column('mpn', sa.String(), nullable=True),
        sa.Column('version', sa.String(), default='1.0.0'),
        sa.Column('status', sa.String(), default='Active'),
        sa.Column('trust_level', sa.String(), default='User-Added'),
        sa.Column('attributes', JSON, nullable=False),
        sa.Column('configurable_options', JSON, nullable=True),
        sa.Column('compliance_tags', JSON, nullable=True),
        sa.Column('photos_icons', JSON, nullable=True),
        sa.Column('available_regions', JSON, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=func.now()),
        sa.PrimaryKeyConstraint('base_id', 'variant_id')
    )
    
    # 7. Component Documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('base_id', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('asset_id', sa.String(), nullable=False),
        sa.Column('version', sa.String(), default='1.0.0'),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('covered_variants', JSON, nullable=True),
        sa.Column('is_shared', sa.Boolean(), default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 8. Memory table
    op.create_table(
        'memory',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.Column('tags', JSON, nullable=True),
        sa.Column('trace_id', sa.String(), nullable=True),
        sa.Column('sha256', sa.String(), nullable=True),
        sa.Column('prev_sha256', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 9. AI Action Log table
    op.create_table(
        'ai_action_log',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('prompt_text', sa.Text(), nullable=True),
        sa.Column('proposed_action', JSON, nullable=False),
        sa.Column('user_decision', sa.String(), nullable=False),
        sa.Column('timestamp', DateTime(timezone=True), server_default=func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 10. AI Action Vectors table
    op.create_table(
        'ai_action_vectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('component_type', sa.String(), nullable=True),
        sa.Column('user_prompt', sa.String(), nullable=False),
        sa.Column('anonymized_prompt', sa.String(), nullable=False),
        sa.Column('design_context', JSON, nullable=True),
        sa.Column('anonymized_context', JSON, nullable=True),
        sa.Column('session_history', JSON, nullable=True),
        sa.Column('approval', sa.Boolean(), nullable=False),
        sa.Column('confidence_shown', sa.Float(), nullable=True),
        sa.Column('confirmed_by', sa.String(), nullable=False, default='human'),
        sa.Column('timestamp', DateTime(), default=sa.func.now()),
        sa.Column('embedding', JSON, nullable=False),
        sa.Column('meta', JSON, nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 11. Design Vectors table
    op.create_table(
        'design_vectors',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('vector', JSON),
        sa.Column('meta', JSON, nullable=True),
        sa.Column('created_at', DateTime(), server_default=func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 12. Trace Event table
    op.create_table(
        'trace_event',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('trace_id', sa.String(), nullable=False),
        sa.Column('ts', DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.Column('actor', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payload', JSON, nullable=False),
        sa.Column('sha256', sa.String(), nullable=True),
        sa.Column('prev_sha256', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 13. Tenant Settings table
    op.create_table(
        'tenant_settings',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=False),
        sa.Column('auto_approve_enabled', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('risk_threshold_default', sa.Float(), server_default=sa.text('0.80')),
        sa.Column('action_whitelist', JSON, default=dict),
        sa.Column('action_blacklist', JSON, default=dict),
        sa.Column('enabled_domains', JSON, default=dict),
        sa.Column('feature_flags', JSON, default=dict),
        sa.Column('data', JSON, default=dict),
        sa.Column('version', sa.Integer(), server_default=sa.text('1')),
        sa.Column('updated_by_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ai_auto_approve', sa.Boolean(), default=False),
        sa.Column('risk_threshold_low', sa.Float(), default=0.0),
        sa.Column('risk_threshold_medium', sa.Float(), default=0.75),
        sa.Column('risk_threshold_high', sa.Float(), default=1.1),
        sa.Column('whitelisted_actions', JSON, nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenant_settings_tenant_id'), 'tenant_settings', ['tenant_id'], unique=True)
    
    # 14. Agent Catalog table
    op.create_table(
        'agent_catalog',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=120), nullable=False),
        sa.Column('domain', sa.String(length=64), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('risk_class', sa.String(length=32), nullable=True),
        sa.Column('capabilities', JSON, nullable=True),
        sa.Column('created_at', DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('name')
    )
    
    # 15. Agent Versions table
    op.create_table(
        'agent_versions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=16), default='draft'),
        sa.Column('spec', JSON, nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('validation_report', JSON, nullable=True),
        sa.Column('created_by_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', DateTime(), default=sa.func.now()),
        sa.Column('published_at', DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agent_name'], ['agent_catalog.name']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_name', 'version', name='uq_agent_versions_name_version')
    )
    op.create_index('ix_agent_versions_agent_status', 'agent_versions', ['agent_name', 'status'])
    
    # 16. Tenant Agent State table
    op.create_table(
        'tenant_agent_state',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('pinned_version', sa.Integer(), nullable=True),
        sa.Column('config_override', JSON, nullable=True),
        sa.Column('updated_by_id', sa.String(length=36), nullable=True),
        sa.Column('updated_at', DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['agent_name'], ['agent_catalog.name']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'agent_name', name='uq_tenant_agent_state_tenant_agent')
    )
    op.create_index('ix_tenant_agent_state_tenant_agent', 'tenant_agent_state', ['tenant_id', 'agent_name'])
    
    # 17. Pending Actions table
    op.create_table(
        'pending_actions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=False),
        sa.Column('project_id', sa.String(length=100), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('agent_name', sa.String(length=100), nullable=True),
        sa.Column('action_type', sa.String(length=64), nullable=False),
        sa.Column('payload', JSON, nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=16), default='pending'),
        sa.Column('reason', sa.String(length=400), nullable=True),
        sa.Column('requested_by_id', sa.String(length=36), nullable=True),
        sa.Column('approved_by_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', DateTime(), default=sa.func.now()),
        sa.Column('updated_at', DateTime(), default=sa.func.now()),
        sa.Column('applied_at', DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pending_actions_tenant_status', 'pending_actions', ['tenant_id', 'status'])
    op.create_index('ix_pending_actions_session', 'pending_actions', ['session_id'])
    op.create_index('ix_pending_actions_created_at', 'pending_actions', ['created_at'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('pending_actions')
    op.drop_table('tenant_agent_state')
    op.drop_table('agent_versions')
    op.drop_table('agent_catalog')
    op.drop_table('tenant_settings')
    op.drop_table('trace_event')
    op.drop_table('design_vectors')
    op.drop_table('ai_action_vectors')
    op.drop_table('ai_action_log')
    op.drop_table('memory')
    op.drop_table('documents')
    op.drop_table('components')
    op.drop_table('component_master')
    op.drop_table('file_assets')
    op.drop_table('links')
    op.drop_table('schematic_components')
    op.drop_table('users')
