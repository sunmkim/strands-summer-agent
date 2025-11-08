from strands.hooks import (
    AgentInitializedEvent, 
    HookProvider, 
    HookRegistry,
    MessageAddedEvent
)
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole
from bedrock_agentcore.memory.session import MemorySession


class MemoryHook(HookProvider):
    """
    Class to automate memory operations using the MemorySession. The MemoryHook class
    1. Loads most recent conversation (via AgentInitializedEvent)
    2. Stores the last message (via the session manager)
    """
    def __init__(self, actor_id: str, session_id: str, memory_session: MemorySession):
        self.actor_id = actor_id
        self.session_id = session_id
        self.memory_session = memory_session
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """
        Loads the most recent conversation history when agent starts using MemorySession
        """
        try:
            most_recent_convo = self.memory_session.get_last_k_turns(k=5)
            # format conversation history
            if most_recent_convo:
                context_msgs = []
                for turn in most_recent_convo:
                    print("Turn:", turn)
                    for message in turn:
                        print("- Message:", message)
                        if hasattr(message, 'role') and hasattr(message, 'content'):
                            role = message['role']
                            content = message['content']
                        else:
                            role = message.get('role', 'unknown')
                            content = message.get('content', {}).get('text', '')
                        context_msgs.append(f"{role}: {content}")
                # format context messages to single string
                context = "\n".join(context_msgs)
                # Add context to agent's system prompt
                event.agent.system_prompt += f"\n\nRecent conversation:\n{context}"
                print(f"✅ Loaded {len(most_recent_convo)} conversation turns using MemorySession")
        except Exception as e:
            print(f"Memory load error: {e}")

    def on_message_added(self, event: MessageAddedEvent):
        """
        Stores new conversational messages via MemorySession
        """
        messages = event.agent.messages

        try:
            if messages and len(messages) > 0 and messages[-1]["content"][0].get("text"):
                message_text = messages[-1]["content"][0]["text"]
                message_role = MessageRole.USER if messages[-1]["role"] == "user" else MessageRole.ASSISTANT
                # Use memory session instance to add message
                result = self.memory_session.add_turns(
                    messages=[ConversationalMessage(message_text, message_role)]
                )
                print(f"✅ Stored message with Event ID: {result['eventId']}, Role: {message_role.value}")
        except Exception as e:
            print(f"Memory save error: {e}")
            raise
    
    def register_hooks(self, registry: HookRegistry):
        """
        Register memory hooks
        """
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        print("✅ Memory hooks registered!")