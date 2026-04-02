"""initial schema"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instagram_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ig_business_account_id", sa.String(length=255), nullable=False),
        sa.Column("page_id", sa.String(length=255), nullable=False),
        sa.Column("account_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("auto_reply_mode", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("ig_business_account_id"),
        sa.UniqueConstraint("page_id"),
    )
    op.create_table(
        "instagram_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("external_id"),
    )
    op.create_table(
        "instagram_threads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_external_id", sa.String(length=255), nullable=False),
        sa.Column("instagram_account_id", sa.Integer(), sa.ForeignKey("instagram_accounts.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("instagram_users.id"), nullable=False),
        sa.Column("user_external_id", sa.String(length=255), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("thread_status", sa.String(length=50), nullable=False),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("thread_external_id"),
    )
    op.create_table(
        "instagram_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("instagram_threads.id"), nullable=False),
        sa.Column("external_message_id", sa.String(length=255), nullable=False),
        sa.Column("direction", sa.String(length=50), nullable=False),
        sa.Column("sender_id", sa.String(length=255), nullable=False),
        sa.Column("recipient_id", sa.String(length=255), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("raw_payload_json", sa.JSON(), nullable=False),
        sa.Column("message_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivery_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("external_message_id"),
    )
    op.create_table(
        "incoming_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.UniqueConstraint("external_event_id"),
    )
    op.create_table(
        "conversation_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("instagram_threads.id"), nullable=False),
        sa.Column("state_json", sa.JSON(), nullable=False),
        sa.Column("last_classifier_output_json", sa.JSON(), nullable=True),
        sa.Column("last_policy_output_json", sa.JSON(), nullable=True),
        sa.Column("last_qa_output_json", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("thread_id"),
    )
    op.create_table(
        "knowledge_base_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("tags", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "escalations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("instagram_threads.id"), nullable=False),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("instagram_messages.id"), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("operator_summary", sa.Text(), nullable=False),
        sa.Column("suggested_reply", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("instagram_threads.id"), nullable=False),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("instagram_messages.id"), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("actor_type", sa.String(length=50), nullable=False),
        sa.Column("actor_name", sa.String(length=100), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_instagram_accounts_ig_business_account_id", "instagram_accounts", ["ig_business_account_id"])
    op.create_index("ix_instagram_accounts_page_id", "instagram_accounts", ["page_id"])
    op.create_index("ix_instagram_users_external_id", "instagram_users", ["external_id"])
    op.create_index("ix_instagram_threads_thread_external_id", "instagram_threads", ["thread_external_id"])
    op.create_index("ix_instagram_threads_user_external_id", "instagram_threads", ["user_external_id"])
    op.create_index("ix_instagram_messages_thread_id", "instagram_messages", ["thread_id"])
    op.create_index("ix_instagram_messages_sender_id", "instagram_messages", ["sender_id"])
    op.create_index("ix_instagram_messages_recipient_id", "instagram_messages", ["recipient_id"])
    op.create_index("ix_instagram_messages_message_timestamp", "instagram_messages", ["message_timestamp"])
    op.create_index("ix_incoming_events_external_event_id", "incoming_events", ["external_event_id"])
    op.create_index("ix_incoming_events_event_type", "incoming_events", ["event_type"])
    op.create_index("ix_conversation_states_thread_id", "conversation_states", ["thread_id"])
    op.create_index("ix_knowledge_base_entries_category", "knowledge_base_entries", ["category"])
    op.create_index("ix_knowledge_base_entries_language", "knowledge_base_entries", ["language"])
    op.create_index("ix_escalations_thread_id", "escalations", ["thread_id"])
    op.create_index("ix_escalations_reason", "escalations", ["reason"])
    op.create_index("ix_audit_logs_thread_id", "audit_logs", ["thread_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_thread_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_escalations_reason", table_name="escalations")
    op.drop_index("ix_escalations_thread_id", table_name="escalations")
    op.drop_table("escalations")
    op.drop_index("ix_knowledge_base_entries_language", table_name="knowledge_base_entries")
    op.drop_index("ix_knowledge_base_entries_category", table_name="knowledge_base_entries")
    op.drop_table("knowledge_base_entries")
    op.drop_index("ix_conversation_states_thread_id", table_name="conversation_states")
    op.drop_table("conversation_states")
    op.drop_index("ix_incoming_events_event_type", table_name="incoming_events")
    op.drop_index("ix_incoming_events_external_event_id", table_name="incoming_events")
    op.drop_table("incoming_events")
    op.drop_index("ix_instagram_messages_message_timestamp", table_name="instagram_messages")
    op.drop_index("ix_instagram_messages_recipient_id", table_name="instagram_messages")
    op.drop_index("ix_instagram_messages_sender_id", table_name="instagram_messages")
    op.drop_index("ix_instagram_messages_thread_id", table_name="instagram_messages")
    op.drop_table("instagram_messages")
    op.drop_index("ix_instagram_threads_user_external_id", table_name="instagram_threads")
    op.drop_index("ix_instagram_threads_thread_external_id", table_name="instagram_threads")
    op.drop_table("instagram_threads")
    op.drop_index("ix_instagram_users_external_id", table_name="instagram_users")
    op.drop_table("instagram_users")
    op.drop_index("ix_instagram_accounts_page_id", table_name="instagram_accounts")
    op.drop_index("ix_instagram_accounts_ig_business_account_id", table_name="instagram_accounts")
    op.drop_table("instagram_accounts")
