from bbcode import *
import re
import cgi

def parseout(bfcode):
    try:
        output = parsebf(bfcode)
    except (UnknownLanguageCommand, DataPointerError, UnevenSquareBracketsError, ValueError, NotImplementedError), e:
        return e.message
    return output

def parsebf(bfcode):
    code_end = len(bfcode)
    instruction_pointer = 0
    data_pointer = 0
    cells = [0]
    output = ''
    def jump(pointer, opener, closer, direction):
        start = pointer + 1
        opened = 1
        while opened:
            if direction == '+':
                pointer += 1
            else:
                pointer -= 1
            if pointer == code_end or pointer < 0:
                raise UnevenSquareBracketsError, "Uneven square brackets (@%s)" % start
            if bfcode[pointer] == opener:
                opened += 1
            elif bfcode[pointer] == closer:
                opened -= 1
        return pointer
    while instruction_pointer < code_end:
        current = bfcode[instruction_pointer]
        verbose_pointer = instruction_pointer + 1
        if current == '>':
            data_pointer += 1
            if len(cells) == data_pointer:
                cells.append(0)
        elif current == '<':
            if data_pointer == 0:
                raise DataPointerError, "Data pointer cannot be zero (@%s)" % verbose_pointer
            data_pointer -= 1
        elif current == '+':
            if cells[data_pointer] == 255:
                raise ValueError, "Byte cannot exceed 255 (@%s)" % verbose_pointer
            cells[data_pointer] += 1
        elif current == '-':
            if cells[data_pointer] == 0:
                raise ValueError, "Byte cannot be negative (@%s)" % verbose_pointer
            cells[data_pointer] -= 1
        elif current == '.':
            output += chr(cells[data_pointer])
        elif current == ',':
            raise NotImplementedError, "Input (',') is not implemented yet (@%s)" % verbose_pointer
        elif current == '[':
            if cells[data_pointer] == 0:
                instruction_pointer = jump(instruction_pointer, '[',']','+')
        elif current == ']':
            if cells[data_pointer] != 0:
                instruction_pointer = jump(instruction_pointer, ']','[','-')
        else:
            raise UnknownLanguageCommand, "Unknown language command: '%s' (@%s)" % (current, verbose_pointer)
        instruction_pointer += 1
    return output

class Brainfuck(SelfClosingTagNode):
    """
    Executes a brainfuck statement
    
    Usage:
    
    [code lang=bbdocs linenos=0][brainfuck]++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>.[/brainfuck][/code]
    
    Note: this brainfuck implementation does not support the , command.
    """
    open_pattern = re.compile(r'\[brainfuck\](?P<bfcode>[+-\[\].><]+)\[/brainfuck\]')
    
    def parse(self):
        bfcode = self.match.group('bfcode')
        parsed = cgi.escape(parseout(bfcode))
        return """<p style="font-weight: bold;">Brainfuck</p>
                  <code class="code">%s</code>
                  <p style="font-weight: bold;">Output</p>
                  <pre class="code">%s</pre>""" % (bfcode, parsed)
        
    
register(Brainfuck)