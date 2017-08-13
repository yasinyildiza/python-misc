import argparse
import os

EMPTY = ''
SPACE = ' '
TAB = '\t'
NEW_LINE = '\n'

INDENTATION = SPACE * 2

DIRECTIVE = '#'

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'

OPEN_PARENTHESIS = '('
CLOSE_PARENTHESIS = ')'
OPEN_BRACKET = '['
CLOSE_BRACKET = ']'
OPEN_CURLY_BRACE = '{'
CLOSE_CURLY_BRACE = '}'

COMMA = ','
SEMI_COLON = ';'
QUESTION_MARK = '?'
COLON = ':'
SLASH = '/'
BACKSLASH = '\\'
ASTERIX = '*'

INLINE_COMMENT = SLASH * 2
BLOCK_COMMENT = SLASH + ASTERIX * 2 + SLASH

PLACEHOLDER = 'PLCHLDR'

BITWISE_AND = '&'
BITWISE_OR = '|'
NOT = '!'
BITWISE_XOR = '^'

ASSIGNMENT = '='
LESS_THAN = '<'
GREATER_THAN = '>'

PLUS = '+'
MINUS = '-'
MULTIPLY = '*'
DIVIDE = '/'
MODULO = '%'

LOGICAL_AND = BITWISE_AND * 2
LOGICAL_OR = BITWISE_OR * 2

AND_EQUAL = BITWISE_AND + ASSIGNMENT
OR_EQUAL = BITWISE_OR + ASSIGNMENT

EQUAL_TO = ASSIGNMENT + ASSIGNMENT
NOT_EQUAL_TO = NOT + ASSIGNMENT
LESS_THAN_OR_EQUAL_TO = LESS_THAN + ASSIGNMENT
GREATER_THAN_OR_EQUAL_TO = GREATER_THAN + ASSIGNMENT

PLUS_EQUAL = PLUS + ASSIGNMENT
MINUS_EQUAL = PLUS + ASSIGNMENT
MULTIPLY_EQUAL = MULTIPLY + ASSIGNMENT
DIVIDE_EQUAL = DIVIDE + ASSIGNMENT
MODULO_EQUAL = MODULO + ASSIGNMENT

SHIFT_LEFT = LESS_THAN * 2
SHIFT_RIGHT = GREATER_THAN * 2

PLUS_PLUS = PLUS * 2
MINUS_MINUS = MINUS * 2

POINTER_ACCESSOR = MINUS + GREATER_THAN

IF = 'if'
ELSE = 'else'
ELSE_IF = ELSE + SPACE + IF

SWITCH = 'switch'
CASE = 'case'

WHILE = 'while'
FOR = 'for'

TRY = 'try'
CATCH = 'catch'

INLINE_IF = QUESTION_MARK + COLON

DIR_INCLUDE = '#include'
DIR_DEFINE = '#define'

DIR_IFDEF = '#ifdef'
DIR_ELSE = '#else'
DIR_END = '#end'

OPEN_CURLY_BRACE_INLINE = True

def is_quoted(content, index):
    single_quote_started = False
    double_quote_started = False
    i = 0
    while True:
        if i+1 >= len(content):
            break

        if i == index:
            return single_quote_started or double_quote_started

        char = content[i]
        i += 1

        if single_quote_started:
            if char == SINGLE_QUOTE:
                single_quote_started = False
        elif double_quote_started:
            if char == DOUBLE_QUOTE:
                double_quote_started = False
        else:
            if char == SINGLE_QUOTE:
                single_quote_started = True
            elif char == DOUBLE_QUOTE:
                double_quote_started = True
            else:
                pass

    return False

def get_line_at_index(content, index):
    lines = content.splitlines()
    i = 0
    for line in lines:
        if i >= index:
            return line

        i += len(line)

    return None

def organize_if_statements(content):
    clean_content = content

    return clean_content

def organize_directives(content):
    clean_content = content

    lines = content.splitlines()
    for line in lines:
        if line.strip().startswith(DIRECTIVE):
            clean_content = clean_content.replace(line, line.strip())

    return clean_content

def organize_statement_spaces(content):
    clean_content = content

    clean_content = organize_directives(clean_content)
    clean_content = organize_if_statements(clean_content)

    return clean_content

def make_placeholder(sign):
    placeholder = '{0}{1}{0}'.format(PLACEHOLDER*3, sign)

    return placeholder

def organize_operator_spaces(content):
    # TODO: overall check for quoted

    clean_content = content

    clean_content = clean_content.replace(EQUAL_TO, make_placeholder('EQUAL_TO'))
    clean_content = clean_content.replace(NOT_EQUAL_TO, make_placeholder('NOT_EQUAL_TO'))
    clean_content = clean_content.replace(LESS_THAN_OR_EQUAL_TO, make_placeholder('LESS_THAN_OR_EQUAL_TO'))
    clean_content = clean_content.replace(GREATER_THAN_OR_EQUAL_TO, make_placeholder('GREATER_THAN_OR_EQUAL_TO'))

    clean_content = clean_content.replace(PLUS_EQUAL, make_placeholder('PLUS_EQUAL'))
    clean_content = clean_content.replace(MINUS_EQUAL, make_placeholder('MINUS_EQUAL'))
    clean_content = clean_content.replace(MULTIPLY_EQUAL, make_placeholder('MULTIPLY_EQUAL'))
    clean_content = clean_content.replace(DIVIDE_EQUAL, make_placeholder('DIVIDE_EQUAL'))
    clean_content = clean_content.replace(MODULO_EQUAL, make_placeholder('MODULO_EQUAL'))

    clean_content = clean_content.replace(LOGICAL_AND, make_placeholder('LOGICAL_AND'))
    clean_content = clean_content.replace(LOGICAL_OR, make_placeholder('LOGICAL_OR'))

    clean_content = clean_content.replace(PLUS_PLUS, make_placeholder('PLUS_PLUS'))
    clean_content = clean_content.replace(MINUS_MINUS, make_placeholder('MINUS_MINUS'))

    clean_content = clean_content.replace(AND_EQUAL, make_placeholder('AND_EQUAL'))
    clean_content = clean_content.replace(OR_EQUAL, make_placeholder('OR_EQUAL'))

    clean_content = clean_content.replace(SHIFT_LEFT, make_placeholder('SHIFT_LEFT'))
    clean_content = clean_content.replace(SHIFT_RIGHT, make_placeholder('SHIFT_RIGHT'))

    clean_content = clean_content.replace(POINTER_ACCESSOR, make_placeholder('POINTER_ACCESSOR'))

    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, BITWISE_XOR)

    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, ASSIGNMENT)

    # #include <lib>
    #clean_content = clean_and_add_spaces_before_and_after_char(clean_content, LESS_THAN)
    #clean_content = clean_and_add_spaces_before_and_after_char(clean_content, GREATER_THAN)

    # reference&
    #clean_content = clean_and_add_spaces_before_and_after_char(clean_content, BITWISE_AND)
    #clean_content = clean_and_add_spaces_before_and_after_char(clean_content, BITWISE_OR)

    # pointer*
    #clean_content = clean_and_add_spaces_before_and_after_char(clean_content, PLUS)
    #clean_content = clean_and_add_spaces_before_and_after_char(clean_content, MINUS)
    #clean_content = clean_and_add_spaces_before_and_after_char(clean_content, MULTIPLY)
    #clean_content = clean_and_add_spaces_before_and_after_char(clean_content, DIVIDE)
    #clean_content = clean_and_add_spaces_before_and_after_char(clean_content, MODULO)

    clean_content = clean_content.replace(make_placeholder('PLUS_PLUS'), PLUS_PLUS)
    clean_content = clean_content.replace(make_placeholder('MINUS_MINUS'), MINUS_MINUS)

    clean_content = clean_content.replace(make_placeholder('LOGICAL_AND'), LOGICAL_AND)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, LOGICAL_AND)

    clean_content = clean_content.replace(make_placeholder('LOGICAL_OR'), LOGICAL_OR)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, LOGICAL_OR)

    clean_content = clean_content.replace(make_placeholder('EQUAL_TO'), EQUAL_TO)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, EQUAL_TO)

    clean_content = clean_content.replace(make_placeholder('NOT_EQUAL_TO'), NOT_EQUAL_TO)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, NOT_EQUAL_TO)

    clean_content = clean_content.replace(make_placeholder('LESS_THAN_OR_EQUAL_TO'), LESS_THAN_OR_EQUAL_TO)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, LESS_THAN_OR_EQUAL_TO)

    clean_content = clean_content.replace(make_placeholder('GREATER_THAN_OR_EQUAL_TO'), GREATER_THAN_OR_EQUAL_TO)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, GREATER_THAN_OR_EQUAL_TO)

    clean_content = clean_content.replace(make_placeholder('PLUS_EQUAL'), PLUS_EQUAL)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, PLUS_EQUAL)

    clean_content = clean_content.replace(make_placeholder('MINUS_EQUAL'), MINUS_EQUAL)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, MINUS_EQUAL)

    clean_content = clean_content.replace(make_placeholder('MULTIPLY_EQUAL'), MULTIPLY_EQUAL)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, MULTIPLY_EQUAL)

    clean_content = clean_content.replace(make_placeholder('DIVIDE_EQUAL'), DIVIDE_EQUAL)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, DIVIDE_EQUAL)

    clean_content = clean_content.replace(make_placeholder('MODULO_EQUAL'), MODULO_EQUAL)
    clean_content = clean_and_add_spaces_before_and_after_char(clean_content, MODULO_EQUAL)

    clean_content = clean_content.replace(make_placeholder('AND_EQUAL'), AND_EQUAL)
    clean_content = clean_content.replace(make_placeholder('OR_EQUAL'), OR_EQUAL)

    clean_content = clean_content.replace(make_placeholder('SHIFT_LEFT'), SHIFT_LEFT)
    clean_content = clean_content.replace(make_placeholder('SHIFT_RIGHT'), SHIFT_RIGHT)

    clean_content = clean_content.replace(make_placeholder('POINTER_ACCESSOR'), POINTER_ACCESSOR)

    # TODO

    return clean_content

def align_indentation(content):
    clean_content = EMPTY

    indent_level = 0
    single_quote_started = False
    double_quote_started = False
    i = 0
    while True:
        if i+1 >= len(content):
            break

        prev_char = None
        if i > 0:
            prev_char = content[i-1]

        char = content[i]
        i += 1

        next_char = None
        if i < len(content):
            next_char = content[i]
            i += 1

        if single_quote_started:
            if char == SINGLE_QUOTE:
                single_quote_started = False
                end_index = i
            if char != NEW_LINE:
                clean_content += char
            i -= 1
        elif double_quote_started:
            if char == DOUBLE_QUOTE:
                double_quote_started = False
                end_index = i
            if char != NEW_LINE:
                clean_content += char
            i -= 1
        else:
            if char == SINGLE_QUOTE:
                single_quote_started = True
                clean_content += char
                start_index = i - 2
                i -= 1
            elif char == DOUBLE_QUOTE:
                double_quote_started = True
                clean_content += char
                start_index = i - 2
                i -= 1
            else:
                if char == OPEN_CURLY_BRACE:
                    indent_level += 1
                    while clean_content[-1] == SPACE or clean_content[-1] == NEW_LINE:
                        clean_content = clean_content[:-1]
                    if OPEN_CURLY_BRACE_INLINE:
                        clean_content += SPACE
                    else:
                        clean_content += NEW_LINE
                        clean_content += (indent_level-1) * INDENTATION
                    clean_content += char
                    if next_char == NEW_LINE:
                        clean_content += next_char
                    else:
                        clean_content += NEW_LINE
                        i -= 1
                    while content[i] == SPACE or content[i] == NEW_LINE:
                        i += 1
                    clean_content += indent_level * INDENTATION
                elif char == CLOSE_CURLY_BRACE:
                    indent_level -= 1
                    while clean_content[-1] == SPACE or clean_content[-1] == NEW_LINE:
                        clean_content = clean_content[:-1]
                    clean_content += NEW_LINE
                    clean_content += indent_level * INDENTATION
                    clean_content += char
                    if next_char != SPACE and next_char != NEW_LINE:
                        clean_content += SPACE
                    i -= 1
                elif char == NEW_LINE:
                    clean_content += char
                    i -= 1
                    while i < len(content) and (content[i] == SPACE or content[i] == NEW_LINE):
                        if content[i] == NEW_LINE:
                            clean_content += NEW_LINE
                        i += 1
                    clean_content += indent_level * INDENTATION
                elif char == OPEN_PARENTHESIS:
                    clean_content += char
                    i -= 1
                    local_level = 0
                    while True:
                        if content[i] == OPEN_PARENTHESIS:
                            local_level += 1
                        elif content[i] == CLOSE_PARENTHESIS:
                            if local_level == 0:
                                clean_content += content[i]
                                i += 1
                                break
                            local_level -= 1
                        elif content[i] == SEMI_COLON:
                            clean_content += content[i]
                            i += 1
                            while content[i] == SPACE or content[i] == NEW_LINE:
                                i += 1
                            clean_content += SPACE
                        if content[i] != NEW_LINE:
                            clean_content += content[i]
                        i += 1
                elif char == SEMI_COLON and next_char != NEW_LINE:
                    clean_content += char
                    i -= 1
                    while content[i] == SPACE:
                        i += 1
                    clean_content += NEW_LINE
                    clean_content += indent_level * INDENTATION
                elif char == MINUS and next_char == GREATER_THAN:
                    while clean_content[-1] == SPACE or clean_content[-1] == NEW_LINE:
                        clean_content = clean_content[:-1]
                    clean_content += char
                    clean_content += next_char
                    while content[i] == SPACE or content[i] == NEW_LINE:
                        i += 1
                else:
                    clean_content += char
                    i -= 1

    return clean_content

def remove_multiple_char(content, char):
    clean_content = content

    while char*2 in clean_content:
        clean_content = clean_content.replace(char*2, char)

    return clean_content

def remove_multiple_semi_colons(content):
    clean_content = content

    clean_content = remove_multiple_char(content, SEMI_COLON)

    return clean_content

def clean_spaces_before_char(content, char):
    clean_content = content

    while SPACE+char in clean_content:
        clean_content = clean_content.replace(SPACE+char, char)

    return clean_content

def clean_spaces_after_char(content, char):
    clean_content = content

    while char+SPACE in clean_content:
        clean_content = clean_content.replace(char+SPACE, char)

    return clean_content

def clean_spaces_before_and_after_char(content, char):
    clean_content = content

    clean_content = clean_spaces_before_char(clean_content, char)
    clean_content = clean_spaces_after_char(clean_content, char)

    return clean_content

def add_spaces_before_char(content, char):
    clean_content = content.replace(char, SPACE+char)

    return clean_content

def add_spaces_after_char(content, char):
    clean_content = content.replace(char, char+SPACE)

    return clean_content

def add_spaces_before_and_after_char(content, char):
    clean_content = content

    clean_content = add_spaces_before_char(clean_content, char)
    clean_content = add_spaces_after_char(clean_content, char)

    return clean_content

def clean_and_add_spaces_before_and_after_char(content, char):
    clean_content = content

    clean_content = clean_spaces_before_and_after_char(clean_content, char)
    clean_content = add_spaces_before_and_after_char(clean_content, char)

    return clean_content

def clean_spaces_before(content):
    clean_content = content
    clean_content = clean_spaces_before_char(clean_content, CLOSE_PARENTHESIS)
    clean_content = clean_spaces_before_char(clean_content, CLOSE_BRACKET)
    clean_content = clean_spaces_before_char(clean_content, COMMA)
    clean_content = clean_spaces_before_char(clean_content, SEMI_COLON)

    return clean_content

def clean_spaces_after(content):
    clean_content = content
    clean_content = clean_spaces_after_char(clean_content, OPEN_PARENTHESIS)
    clean_content = clean_spaces_after_char(clean_content, OPEN_BRACKET)
    clean_content = clean_spaces_after_char(clean_content, COMMA)
    #clean_content = clean_spaces_after_char(clean_content, SEMI_COLON)

    return clean_content

def add_spaces_before(content):
    clean_content = content

    return clean_content

def add_spaces_after(content):
    clean_content = content

    clean_content = add_spaces_after_char(clean_content, COMMA)

    return clean_content

def clean_spaces_in_the_middle(content):
    lines = content.splitlines()

    clean_lines = []
    for line in lines:
        lline = line.lstrip()
        indent = (SPACE*(len(line) - len(lline)))
        while INDENTATION in lline:
            lline = lline.replace(INDENTATION, SPACE)
        clean_line = indent + lline
        clean_lines.append(clean_line)

    clean_content = NEW_LINE.join(clean_lines)

    return clean_content

def clean_spaces_at_line_ends(content):
    clean_content = content.lstrip(SPACE)

    while SPACE+NEW_LINE in clean_content:
        clean_content = clean_content.replace(SPACE+NEW_LINE, NEW_LINE)

    return clean_content

def clean_multiple_new_lines(content, n):
    clean_content = content.lstrip(NEW_LINE)

    while NEW_LINE*n in clean_content:
        clean_content = clean_content.replace(NEW_LINE*n, NEW_LINE*(n-1))

    return clean_content

def clean_triple_new_lines(content):
    clean_content = clean_multiple_new_lines(content, 3)

    return clean_content

def clean_comments(content):
    clean_content = EMPTY

    single_quote_started = False
    double_quote_started = False
    block_comment_started = False
    inline_comment_started = False
    i = 0
    while True:
        if i+1 >= len(content):
            break

        char = content[i]
        i += 1

        next_char = None
        if i < len(content):
            next_char = content[i]
            i += 1

        if single_quote_started:
            if char == SINGLE_QUOTE:
                single_quote_started = False
                end_index = i
            clean_content += char
            i -= 1
        elif double_quote_started:
            if char == DOUBLE_QUOTE:
                double_quote_started = False
                end_index = i
            clean_content += char
            i -= 1
        elif block_comment_started:
            if char == BLOCK_COMMENT[2] and next_char == BLOCK_COMMENT[3]:
                block_comment_started = False
                end_index = i
            else:
                i -= 1
        elif inline_comment_started:
            if char == NEW_LINE:
                inline_comment_started = False
                end_index = i - 1
            i -= 1
        else:
            if char == SINGLE_QUOTE:
                single_quote_started = True
                clean_content += char
                start_index = i - 2
                i -= 1
            elif char == DOUBLE_QUOTE:
                double_quote_started = True
                clean_content += char
                start_index = i - 2
                i -= 1
            elif char == BLOCK_COMMENT[0] and next_char == BLOCK_COMMENT[1]:
                block_comment_started = True
                start_index = i - 2
            elif char == INLINE_COMMENT[0] and next_char == INLINE_COMMENT[1]:
                inline_comment_started = True
                start_index = i - 2
            else:
                clean_content += char
                i -= 1

    return clean_content

def replace_indentation(content):
    clean_content = content.replace(TAB, INDENTATION)

    return clean_content

def process_content(content):
    operations = [
        replace_indentation,
        clean_comments,
        remove_multiple_semi_colons,
        align_indentation,
        clean_spaces_at_line_ends,
        clean_spaces_in_the_middle,
        clean_spaces_before,
        clean_spaces_after,
        add_spaces_before,
        add_spaces_after,
        organize_operator_spaces,
        organize_statement_spaces,
        clean_triple_new_lines,
    ]

    clean_content = content
    for operation in operations:
        clean_content = operation(clean_content)

    return clean_content

def process_file(path, extension):
    with open(path) as fileobj:
        content = fileobj.read()
    clean_content = process_content(content)
    with open(path+extension, 'w') as fileobj:
        fileobj.write(clean_content)

def process_directory(path, extension):
    for subpath in os.listdir(path):
        process_path(os.path.join(path, subpath), extension)

def process_path(path, extension):
    if os.path.isdir(path):
        process_directory(path, extension)
    elif os.path.isfile(path):
        process_file(path, extension)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str)
    parser.add_argument('extension', type=str)
    args = parser.parse_args()

    process_path(args.path, args.extension)

if __name__ == '__main__':
    main()
