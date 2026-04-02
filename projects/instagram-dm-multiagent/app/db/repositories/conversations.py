from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Conversation, ConversationState, InstagramAccount, User


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_default_account(self) -> InstagramAccount:
        result = await self.session.execute(select(InstagramAccount).limit(1))
        account = result.scalar_one_or_none()
        if account:
            return account
        account = InstagramAccount(
            ig_business_account_id="demo_ig_account",
            page_id="demo_page_id",
            account_name="Demo Brand",
        )
        self.session.add(account)
        await self.session.flush()
        return account

    async def get_or_create_user(self, external_id: str) -> User:
        result = await self.session.execute(select(User).where(User.external_id == external_id))
        user = result.scalar_one_or_none()
        if user:
            return user
        user = User(external_id=external_id)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_or_create_by_external_ids(self, thread_external_id: str, user_external_id: str) -> Conversation:
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.conversation_state))
            .where(Conversation.thread_external_id == thread_external_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            return conversation
        account = await self.get_or_create_default_account()
        user = await self.get_or_create_user(user_external_id)
        conversation = Conversation(
            thread_external_id=thread_external_id,
            instagram_account_id=account.id,
            user_id=user.id,
            user_external_id=user_external_id,
        )
        self.session.add(conversation)
        await self.session.flush()
        state = ConversationState(thread_id=conversation.id, state_json={})
        self.session.add(state)
        await self.session.flush()
        return conversation

    async def list_threads(self) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.instagram_account))
            .order_by(desc(Conversation.last_message_at))
        )
        return list(result.scalars().all())

    async def get_thread(self, thread_id: int) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation)
            .options(
                selectinload(Conversation.messages),
                selectinload(Conversation.escalations),
                selectinload(Conversation.conversation_state),
                selectinload(Conversation.instagram_account),
            )
            .where(Conversation.id == thread_id)
        )
        return result.scalar_one_or_none()

    async def update_mode(self, thread_id: int, mode: str) -> Conversation | None:
        conversation = await self.get_thread(thread_id)
        if conversation is None:
            return None
        conversation.instagram_account.auto_reply_mode = mode
        await self.session.flush()
        return conversation

    async def touch_thread(self, thread_id: int) -> None:
        conversation = await self.get_thread(thread_id)
        if conversation:
            conversation.last_message_at = datetime.now(UTC)
            await self.session.flush()
