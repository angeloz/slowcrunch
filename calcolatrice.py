"""Small terminal calculator with four basic operations."""


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b


def main():
    print("Simple calculator")
    first_number = float(input("Enter the first number: "))
    second_number = float(input("Enter the second number: "))
    operation = input("Choose an operation (+, -, *, /): ").strip()

    operations = {
        "+": add,
        "-": subtract,
        "*": multiply,
        "/": divide,
    }

    if operation not in operations:
        print("Invalid operation.")
        return

    try:
        result = operations[operation](first_number, second_number)
    except ValueError as error:
        print(error)
        return

    print(f"Result: {result}")


if __name__ == "__main__":
    main()
