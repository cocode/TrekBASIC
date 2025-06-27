from basic_statements import Keywords
from basic_types import assert_syntax, LETTERS, BasicSyntaxError, NUMBERS


def _find_initial_command(statement: str) -> tuple[str, bool]:
    """
    Find the command at the beginning of a statement.
    lines/statements in BASIC must start with a keyword, or an assignment statement (an implied LET):
    This assumes we are beyond the line number.
    Should we just be returning LET for an implied LET? Probably.
    """
    index = 0
    while index < len(statement) and statement[index].isspace():
        index += 1
    statement = statement[index:]
    for keyword in Keywords:
        if statement.startswith(keyword.name):
            return keyword, False
    else:
        # This line either starts with a variable or is a syntax error.
        # Technically, we don't have to validate the variable here.
        assert_syntax(statement[0] in LETTERS)
        assert_syntax(statement[0] in LETTERS)
        if len(statement) < 2:
            # The statement is only one character. BASIC isn't C, "A" isn't a valid statement.
            raise BasicSyntaxError(F"Statement too short: '{statement}'")
        if statement[1] in NUMBERS or statement[1] == "$":  # Variable like "A1", or "B$"
            return Keywords.LET, True

        return Keywords.LET, True