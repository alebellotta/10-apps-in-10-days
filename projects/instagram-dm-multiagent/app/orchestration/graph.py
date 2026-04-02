from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestration.nodes import NodeFactory, critic_router, policy_router
from app.orchestration.state import GraphState


def build_graph(session: AsyncSession):
    nodes = NodeFactory(session)
    graph = StateGraph(GraphState)
    graph.add_node("load_context_node", nodes.load_context_node)
    graph.add_node("classifier_node", nodes.classifier_node)
    graph.add_node("retrieval_node", nodes.retrieval_node)
    graph.add_node("policy_node", nodes.policy_node)
    graph.add_node("draft_node", nodes.draft_node)
    graph.add_node("critic_node", nodes.critic_node)
    graph.add_node("escalation_node", nodes.escalation_node)
    graph.add_node("dispatch_node", nodes.dispatch_node)
    graph.add_node("persist_node", nodes.persist_node)

    graph.add_edge(START, "load_context_node")
    graph.add_edge("load_context_node", "classifier_node")
    graph.add_edge("classifier_node", "retrieval_node")
    graph.add_edge("retrieval_node", "policy_node")
    graph.add_conditional_edges("policy_node", policy_router)
    graph.add_edge("draft_node", "critic_node")
    graph.add_conditional_edges("critic_node", critic_router)
    graph.add_edge("escalation_node", "persist_node")
    graph.add_edge("dispatch_node", "persist_node")
    graph.add_edge("persist_node", END)
    return graph.compile()
