import json
import re

class Node:
    def __init__(self, node_type, left=None, right=None, value=None):
        self.node_type = node_type
        self.left = left
        self.right = right
        self.value = value

def create_rule(rule_string):
    # Normalize the rule string for parsing
    rule_string = rule_string.replace("AND", " AND ").replace("OR", " OR ")
    tokens = re.split(r'(\s+)', rule_string)  # Split by whitespace but keep it
    stack = []
    current_op = None
    for token in tokens:
        token = token.strip()
        if token == '':
            continue
        if token in ['AND', 'OR']:
            current_op = token
        else:
            if current_op:
                right = stack.pop()  # Get the last item from the stack
                node = Node("operator", left=stack.pop(), right=right, value=current_op)
                stack.append(node)
                current_op = None
            else:
                # Assume a simple condition format
                stack.append(Node("operand", value=token))

    return stack[0] if stack else None

def combine_rules(rules):
    combined = None
    for rule in rules:
        if combined is None:
            combined = create_rule(rule)
        else:
            combined = Node("operator", left=combined, right=create_rule(rule), value="OR")
    return combined

def evaluate_rule(ast, data):
    if ast.node_type == "operand":
        # Simple evaluation for conditions like "age > 30"
        # Ensure the value has the expected format
        try:
            field, op, value = ast.value.split()
            field_value = data.get(field)

            # Comparison logic
            if op == '>':
                return field_value > int(value)
            elif op == '<':
                return field_value < int(value)
            elif op == '=':
                return field_value == value.strip("'")
        except ValueError:
            print(f"Invalid condition format: {ast.value}")
            return False
    elif ast.node_type == "operator":
        left_eval = evaluate_rule(ast.left, data)
        right_eval = evaluate_rule(ast.right, data)
        if ast.value == "AND":
            return left_eval and right_eval
        elif ast.value == "OR":
            return left_eval or right_eval
    return False

# Sample rules
rule1 = "((age > 30 AND department = 'Sales') OR (age < 25 AND department = 'Marketing')) AND (salary > 50000 OR experience > 5)"
rule2 = "((age > 30 AND department = 'Marketing')) AND (salary > 20000 OR experience > 5)"

# Create individual rules
ast1 = create_rule(rule1)
ast2 = create_rule(rule2)

# Combine rules
combined_ast = combine_rules([rule1, rule2])

# Sample JSON data
user_data = {"age": 35, "department": "Sales", "salary": 60000, "experience": 3}

# Evaluate rules
print(evaluate_rule(ast1, user_data))  # Expected output: True
print(evaluate_rule(ast2, user_data))  # Expected output: False
print(evaluate_rule(combined_ast, user_data))  # Expected output: True
