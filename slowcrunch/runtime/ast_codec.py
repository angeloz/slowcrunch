from slowcrunch.core.ast import BinaryOpNode, CallNode, ListNode, NameNode, NumberNode, UnaryOpNode


def encode_node(node):
    if isinstance(node, NumberNode):
        encoded = {"type": "number", "value": node.value}
        if node.value_kind is not None:
            encoded["value_kind"] = node.value_kind
        return encoded
    if isinstance(node, NameNode):
        return {"type": "name", "name": node.name}
    if isinstance(node, ListNode):
        return {
            "type": "list",
            "items": [encode_node(item) for item in node.items],
        }
    if isinstance(node, UnaryOpNode):
        return {
            "type": "unary",
            "operator": node.operator,
            "operand": encode_node(node.operand),
        }
    if isinstance(node, BinaryOpNode):
        return {
            "type": "binary",
            "left": encode_node(node.left),
            "operator": node.operator,
            "right": encode_node(node.right),
        }
    if isinstance(node, CallNode):
        return {
            "type": "call",
            "name": node.name,
            "arguments": [encode_node(argument) for argument in node.arguments],
        }
    raise TypeError(f"Cannot encode node of type {type(node).__name__}")


def decode_node(data):
    node_type = data["type"]

    if node_type == "number":
        return NumberNode(data["value"], data.get("value_kind"))
    if node_type == "name":
        return NameNode(data["name"])
    if node_type == "list":
        return ListNode([decode_node(item) for item in data["items"]])
    if node_type == "unary":
        return UnaryOpNode(data["operator"], decode_node(data["operand"]))
    if node_type == "binary":
        return BinaryOpNode(
            decode_node(data["left"]),
            data["operator"],
            decode_node(data["right"]),
        )
    if node_type == "call":
        return CallNode(
            data["name"],
            [decode_node(argument) for argument in data["arguments"]],
        )
    raise ValueError(f"Unknown node type: {node_type}")
