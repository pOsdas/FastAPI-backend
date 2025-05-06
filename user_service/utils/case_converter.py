def camel_case_to_snake_case(input_str: str) -> str:
    """
    >>> camel_case_to_snake_case("SomeText") -> 'some_text'
    >>> camel_case_to_snake_case("RSomeText") -> 'r_some_text'
    >>> camel_case_to_snake_case("SText") -> 's_text'
    """
    result = []
    for i in range(len(input_str)):
        char = input_str[i]

        # Если текущий символ — заглавная буква
        if char.isupper() and i > 0:
            next_upper = i + 1 < len(input_str) and input_str[i + 1].isupper()
            prev_upper = input_str[i - 1].isupper()

            # Добавляем "_" только если текущий символ не первый и не часть аббревиатуры
            if not (prev_upper and next_upper):
                result.append("_")

        result.append(char.lower())

    return "".join(result)
