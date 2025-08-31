from app.graph.state import GraphState
from app.graph.nodes import GraphNodes


class ConversationGraph:
    """Simple state machine for conversation flow"""

    def __init__(self, nodes: GraphNodes):
        self.nodes = nodes

    def run(self, state: GraphState) -> GraphState:
        """Run the conversation graph"""
        # Start with guard node
        state = self.nodes.guard_node(state)

        # Process based on next action
        while state.next_action and not state.assistant_message:
            if state.next_action == "verify":
                state = self.nodes.verify_node(state)
            elif state.next_action == "router":
                state = self.nodes.router_node(state)
            elif state.next_action == "list":
                state = self.nodes.list_node(state)
            elif state.next_action == "confirm":
                state = self.nodes.confirm_node(state)
            elif state.next_action == "cancel":
                state = self.nodes.cancel_node(state)
            elif state.next_action == "help":
                state = self.nodes.help_node(state)
            elif state.next_action == "smalltalk":
                state = self.nodes.smalltalk_node(state)
            elif state.next_action == "fallback":
                state = self.nodes.fallback_node(state)
            else:
                break

        # Clear next_action for next turn
        state.next_action = None

        return state
