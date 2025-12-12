import re
import math

from typing import List, Tuple, Union, Dict, Callable, Optional

class Node:
    def __init__(
        self,
        node_type: str,
        value: Optional[Union[float, str]] = None,
        left: Optional['Node'] = None,
        right: Optional['Node'] = None
    ):
        self.type = node_type
        self.value = value
        self.left = left
        self.right = right

def create_token_patterns() -> List[Tuple[str, Optional[str]]]:
    return [
        (r'\d+(?:\.\d+)?', 'NUMBER'),
        (r'sin|cos|tan|sqrt|log|exp|abs', 'FUNCTION'),
        (r'pi|e', 'CONSTANT'),
        (r'[\+\-\*/\^]', 'OPERATOR'),
        (r'[\(\)]', 'PAREN'),
        (r'\s+', None),
    ]

def create_constants_map() -> Dict[str, float]:
    return {
        'pi': math.pi,
        'e': math.e
    }

def create_operations_map() -> Dict[str, Callable[[float, float], float]]:
    return {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b if b != 0 else float('inf'),
        '^': lambda a, b: a ** b
    }

def create_functions_map() -> Dict[str, Callable[[float], float]]:
    return {
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'sqrt': lambda x: math.sqrt(x) if x >= 0 else float('nan'),
        'log': math.log,
        'exp': math.exp,
        'abs': abs
    }

def create_precedence_map() -> Dict[str, int]:
    return {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3, 'u-': 4, 'u+': 4}

def create_right_associative_set() -> set:
    return {'^', 'u-', 'u+'}

def get_compiled_patterns() -> List[Tuple[re.Pattern, Optional[str]]]:
    patterns = create_token_patterns()
    return [(re.compile(pattern), token_type) for pattern, token_type in patterns]

def match_token_at_position(
    expression: str, 
    position: int, 
    patterns: List[Tuple[re.Pattern, Optional[str]]]
) -> Optional[Tuple[str, str, int]]:
    for pattern, token_type in patterns:
        match = pattern.match(expression, position)
        
        if not match:
            continue

        value = match.group()
        return token_type, value, match.end()

    return None

def create_number_node(value: str) -> Node:
    return Node('NUMBER', float(value))

def create_constant_node(value: str, constants: Dict[str, float]) -> Node:
    return Node('NUMBER', constants[value])

def should_be_unary(
    current_token_type: str,
    current_token_value: str,
    previous_token_type: Optional[str],
    previous_token_value: Optional[str]
) -> bool:
    if previous_token_type is None:
        return current_token_type == 'OPERATOR' and current_token_value in '+-'
    
    if previous_token_type == 'PAREN' and previous_token_value == '(':
        return current_token_type == 'OPERATOR' and current_token_value in '+-'
    
    if previous_token_type == 'OPERATOR':
        return current_token_type == 'OPERATOR' and current_token_value in '+-'
    
    return False

def process_unary_operator(token_value: str) -> str:
    if token_value == '-':
        return 'u-'
        
    return 'u+'

def create_operator_node(
    operator: str,
    left: Node,
    right: Node
) -> Node:
    return Node('OPERATOR', operator, left, right)

def create_function_node(
    func_name: str,
    argument: Node
) -> Node:
    return Node('FUNCTION', func_name, argument)

def create_unary_node(
    operator: str,
    argument: Node
) -> Node:
    return Node('UNARY', operator, argument)

def can_pop_operator(
    current_operator: str,
    operator_stack: List[str],
    precedence: Dict[str, int],
    right_associative: set
) -> bool:
    if not operator_stack:
        return False
    
    top_operator = operator_stack[-1]
    if top_operator == '(':
        return False
    
    if top_operator not in precedence:
        return False
    
    if precedence[top_operator] > precedence[current_operator]:
        return True
    
    if precedence[top_operator] == precedence[current_operator]:
        return current_operator not in right_associative
    
    return False

def pop_operator_and_create_node(
    operator_stack: List[str],
    output_stack: List[Node],
    functions: Dict[str, Callable],
    precedence: Dict[str, int]
) -> None:
    operator = operator_stack.pop()
    
    if operator in functions:
        arg = output_stack.pop()
        node = create_function_node(operator, arg)
    elif operator in ['u-', 'u+']:
        arg = output_stack.pop()
        node = create_unary_node(operator, arg)
    else:
        right = output_stack.pop()
        left = output_stack.pop()
        node = create_operator_node(operator, left, right)
    
    output_stack.append(node)

def process_right_parenthesis(
    operator_stack: List[str],
    output_stack: List[Node],
    functions: Dict[str, Callable],
    precedence: Dict[str, int]
) -> None:
    while operator_stack and operator_stack[-1] != '(':
        pop_operator_and_create_node(
            operator_stack, output_stack, functions, precedence
        )
    
    if not operator_stack:
        raise ValueError("Несбалансированные скобки")
    
    operator_stack.pop()
    
    if operator_stack and operator_stack[-1] in functions:
        func = operator_stack.pop()
        argument = output_stack.pop()
        node = create_function_node(func, argument)
        output_stack.append(node)

def tokenize_expression(
    expression: str,
    patterns: List[Tuple[re.Pattern, Optional[str]]]
) -> List[Tuple[str, str]]:
    tokens = []
    position = 0
    
    while position < len(expression):
        match_result = match_token_at_position(expression, position, patterns)
        
        if match_result:
            token_type, value, new_position = match_result
            if token_type:
                tokens.append((token_type, value))
            position = new_position
        else:
            raise ValueError(f'Некорректный символ: {expression[position]}')
    
    return tokens

def build_syntax_tree(
    tokens: List[Tuple[str, str]],
    constants: Dict[str, float],
    functions: Dict[str, Callable],
    precedence: Dict[str, int],
    right_associative: set
) -> Node:
    output_stack = []
    operator_stack = []
    
    previous_token_type = None
    previous_token_value = None
    
    for token_type, token_value in tokens:
        if token_type == 'NUMBER':
            node = create_number_node(token_value)
            output_stack.append(node)
        
        elif token_type == 'CONSTANT':
            node = create_constant_node(token_value, constants)
            output_stack.append(node)
        
        elif token_type == 'FUNCTION':
            operator_stack.append(token_value)
        
        elif token_type == 'OPERATOR':
            if should_be_unary(
                token_type, token_value,
                previous_token_type, previous_token_value
            ):
                token_value = process_unary_operator(token_value)
            
            while can_pop_operator(
                token_value, operator_stack,
                precedence, right_associative
            ):
                pop_operator_and_create_node(
                    operator_stack, output_stack,
                    functions, precedence
                )
            
            operator_stack.append(token_value)
        
        elif token_value == '(':
            operator_stack.append('(')
        
        elif token_value == ')':
            process_right_parenthesis(
                operator_stack, output_stack,
                functions, precedence
            )
        
        previous_token_type = token_type
        previous_token_value = token_value
    
    while operator_stack:
        if operator_stack[-1] == '(':
            raise ValueError("Несбалансированные скобки")
        
        pop_operator_and_create_node(
            operator_stack, output_stack,
            functions, precedence
        )
    
    if len(output_stack) != 1:
        raise ValueError("Ошибка построения дерева")
    
    return output_stack[0]

def evaluate_number_node(node: Node) -> float:
    if node.value == None:
        return 0.0

    return node.value

def evaluate_operator_node(
    node: Node,
    operations: Dict[str, Callable]
) -> float:
    left_value = evaluate_expression_tree(node.left, operations, functions)
    right_value = evaluate_expression_tree(node.right, operations, functions)

    return operations[node.value](left_value, right_value)

def evaluate_function_node(
    node: Node,
    functions: Dict[str, Callable]
) -> float:
    argument_value = evaluate_expression_tree(node.left, operations, functions)

    return functions[node.value](argument_value)

def evaluate_unary_node(node: Node) -> float:
    argument_value = evaluate_expression_tree(node.left, operations, functions)

    if node.value == "u-":
        return -argument_value

    return argument_value

def evaluate_expression_tree(
    node: Node,
    operations: Dict[str, Callable],
    functions: Dict[str, Callable]
) -> float:
    if node.type == 'NUMBER':
        return evaluate_number_node(node)
    
    if node.type == 'OPERATOR':
        return evaluate_operator_node(node, operations)
    
    if node.type == 'FUNCTION':
        return evaluate_function_node(node, functions)
    
    if node.type == 'UNARY':
        return evaluate_unary_node(node)
    
    raise ValueError(f"Неизвестный тип узла: {node.type}")

def print_number_node(node: Node, indent: str) -> None:
    print(f"{indent}NUMBER: {node.value}")

def print_function_node(node: Node, indent: str) -> None:
    print(f"{indent}FUNCTION: {node.value}")
    print_tree_structure(node.left, len(indent) + 2)

def print_unary_node(node: Node, indent: str) -> None:
    print(f"{indent}UNARY: {node.value}")
    print_tree_structure(node.left, len(indent) + 2)

def print_operator_node(node: Node, indent: str) -> None:
    print(f"{indent}OPERATOR: {node.value}")
    print_tree_structure(node.left, len(indent) + 2)
    print_tree_structure(node.right, len(indent) + 2)

def print_tree_structure(node: Node, level: int = 0) -> None:
    indent = " " * level
    
    if node.type == 'NUMBER':
        return print_number_node(node, indent)
    
    if node.type == 'FUNCTION':
        return print_function_node(node, indent)
    
    if node.type == 'UNARY':
        return print_unary_node(node, indent)
    
    return print_operator_node(node, indent)

def calculate_expression(
    expression: str,
    patterns: List[Tuple[re.Pattern, Optional[str]]],
    constants: Dict[str, float],
    functions: Dict[str, Callable],
    operations: Dict[str, Callable],
    precedence: Dict[str, int],
    right_associative: set
) -> float:
    tokens = tokenize_expression(expression, patterns)
    
    tree = build_syntax_tree(
        tokens, constants, functions,
        precedence, right_associative
    )

    return evaluate_expression_tree(tree, operations, functions)

def run_test_cases(
    test_expressions: List[str],
    patterns: List[Tuple[re.Pattern, Optional[str]]],
    constants: Dict[str, float],
    functions: Dict[str, Callable],
    operations: Dict[str, Callable],
    precedence: Dict[str, int],
    right_associative: set
) -> None:
    for expr in test_expressions:
        try:
            result = calculate_expression(
                expr, patterns, constants, functions,
                operations, precedence, right_associative
            )
            print(f"{expr} = {result}")

            if expr != test_expressions[0]:
                continue
                
            print("\nДерево для '3 + 5 * 2':")
            tokens = tokenize_expression(expr, patterns)
            tree = build_syntax_tree(
                tokens, constants, functions,
                precedence, right_associative
            )
            print_tree_structure(tree)
            print()
        except Exception as error:
            print(f"Ошибка в '{expr}': {error}")

def run_interactive_mode(
    patterns: List[Tuple[re.Pattern, Optional[str]]],
    constants: Dict[str, float],
    functions: Dict[str, Callable],
    operations: Dict[str, Callable],
    precedence: Dict[str, int],
    right_associative: set
) -> None:
    print("\n" + "="*40)
    print("Калькулятор готов. Введите выражение:")
    print("(для выхода введите 'exit')")
    print("="*40)
    
    while True:
        try:
            expression = input("> ")
     
            if expression.lower() == 'exit':
                break
            
            result = calculate_expression(
                expression, patterns, constants, functions,
                operations, precedence, right_associative
            )
            print(f"= {result}")
            
        except KeyboardInterrupt:
            print("\nВыход...")
            break
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    patterns = get_compiled_patterns()
    constants = create_constants_map()
    operations = create_operations_map()
    functions = create_functions_map()
    precedence = create_precedence_map()
    right_associative = create_right_associative_set()
    
    test_expressions = [
        "3 + 5 * 2",
        "(3 + 5) * 2",
        "10 / 2 - 3",
        "2 ^ 3 + 1",
        "1.5 * 2 + 3",
        "((2 + 3) * 4) ^ 2",
        "-5 + 3",
        "sin(0) + cos(0)",
        "sqrt(16) * 2",
        "pi * 2",
        "e ^ 2",
        "abs(-5) * 2",
        "3 + -2",
        "-sin(pi/2)"
    ]
    
    run_test_cases(
        test_expressions, patterns, constants,
        functions, operations, precedence, right_associative
    )
    
    run_interactive_mode(
        patterns, constants, functions,
        operations, precedence, right_associative
    )