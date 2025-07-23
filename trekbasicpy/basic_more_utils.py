from trekbasicpy.basic_statements import Keywords
from trekbasicpy.basic_types import BasicSyntaxError, LETTERS, NUMBERS, assert_syntax


def _find_next_command(statement: str) -> tuple[str, bool]:
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
    # Might get A=1::B=2
    if len(statement) == 0:
        return None, False
    for keyword in Keywords:
        if statement.upper().startswith(keyword.name):
            return keyword, False
    else:
        # This line either starts with a variable or is a syntax error.
        # Technically, we don't have to validate the variable here.
        assert_syntax(statement[0] in LETTERS, "Lines must start with a letter.")
        if len(statement) < 2:
            # The statement is only one character. BASIC isn't C, "A" isn't a valid statement.
            raise BasicSyntaxError(F"Statement too short: '{statement}'")
        if statement[1] in NUMBERS or statement[1] == "$":  # Variable like "A1", or "B$"
            return Keywords.LET, True

        return Keywords.LET, True