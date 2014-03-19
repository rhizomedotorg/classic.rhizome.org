"""
CLI app (for debugging really) for django-bbcode.

Usage: python cli.py -i <input> [-o <output> -v -n <namespaces]

    -i, --input-file    source to parse
    -o, --output-file   output file (defaults to stdout)
    -v, --visual-only   only get bbcode.get_visual
    -n, --namespaces    list of namespaces to use (defaults to all)
    -s, --strict        on error only display errors.
    -f, --full          full. Include get_visual, errors, source and result.
"""
from optparse import OptionParser, Option
from copy import copy
import StringIO
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bbcode
bbcode.autodiscover()

def check_list(option, opt, value):
    return value.split(',')

class MyOption(Option):
    TYPES = Option.TYPES + ("list",)
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    TYPE_CHECKER["list"] = check_list
    
class MyStringIO(StringIO.StringIO):
    def close(self):
        print self.getvalue()
        
def get_errors(content, namespaces):
    errors = bbcode.validate(content, namespaces)
    output = ''
    lines = content.splitlines()
    if errors:
        for error in errors:
            output += '%s: %s\n' % error
            output += '  %s\n' % lines[error[0]]
    else:
        output += 'None\n'
    return output
        
def get_output(content, namespaces, visonly, full, strict):
    output = ''
    if visonly:
        return bbcode.get_visual(content)
    elif strict:
        output += 'Errors:\n-------\n\n'
        output += get_errors(content, namespaces)
        return output
    elif full:
        output += 'Arguments:\n----------\n\n'
        output += '  namespaces: %s\n' % namespaces
        output += '  visonly:    %s\n' % visonly
        output += '  full:       %s\n' % full
        output += '  strict:     %s\n' % strict
        output += '\nVisual:\n-------\n\n'
        output += bbcode.get_visual(content, namespaces)
        output += '\n\nTags:\n-----\n\n'
        for tag in bbcode.lib.get_tags(namespaces):
            output += '  %s\n' % tag.__name__ 
        output += '\nErrors:\n-------\n\n'
        output += get_errors(content, namespaces)
        output += '\nInput:\n------\n\n'
        output += content
        output += '\nOutput:\n-------\n\n'
    parsed, errors = bbcode.parse(content, namespaces, strict=False)
    output += parsed
    return output
    
def do_parse(infile, outfile, namespaces, visonly, full, strict):
    content = infile.read()
    output = get_output(content, namespaces, visonly, full, strict)
    outfile.write(output)
    outfile.close()

def main():
    parser = OptionParser(option_class=MyOption)
    parser.add_option('-i', '--input-file', action="store", type="string",
                      dest="infile")
    parser.add_option('-o', '--output-file', action="store", type="string",
                      dest="outfile")
    parser.add_option('-v', '--visual-only', action="store_true",
                      dest="visonly", default=False)
    parser.add_option('-n', '--namespaces', action='store', type='list',
                      dest='namespaces', default=['__all__'])
    parser.add_option('-f', '--full', action='store_true', dest='full',
                      default=False)
    parser.add_option('-s', '--strict', action='store_true', dest='strict',
                      default=False)
    options, args = parser.parse_args()
    if not options.infile:
        infile = StringIO.StringIO(' '.join(args))
    else:
        infile = open(options.infile, 'r')
    if not options.outfile:
        outfile = MyStringIO()
    else:
        outfile = open(options.outfile, 'w')
    do_parse(infile, outfile, options.namespaces, options.visonly, options.full,
             options.strict)
if __name__ == '__main__':
    main()