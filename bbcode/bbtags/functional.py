"""
This module only handles how to define variables, their storage/resolving is in
the main module!
"""

from bbcode import *
import re

inner_re = re.compile('(?P<name>\w+)\s*=\s*(?P<value>.+)')


class BBStyleVariableDefinition(TagNode):
    """
    Stores a value in a variable.
    
    Usage:
        [code lang=bbdocs linenos=0][def]varname=value[/def][/code]
        
    The stored variable can be used in many other tags. Variables are wrapped in
    dollar signes when used.
    
    Example:
    
        [code lang=bbdocs linenos=0][def]myvar=http://www.mysite.com[/def]
[url=$myvar$/someimg.png]super cool picture[/url][/code]
    """
    open_pattern = re.compile(patterns.no_argument % 'def')
    close_pattern = re.compile(patterns.closing % 'def')
    
    def parse(self):
        inner = ''
        for node in self.nodes:
            if not node.is_text_node:
                soft_raise("def tag cannot have nested tags")
                return self.raw_content
            else:
                inner += node.raw_content
        match = inner_re.match(inner)
        if not match:
            soft_raise("invalid syntax in define tag: inner must be 'name = value'")
            return self.raw_content
        name = match.groupdict()['name']
        value = match.groupdict()['value']
        real_value = self.variables.resolve(value)
        self.variables.add(name, real_value)
        return ''
    
    
class BBStyleArguments(TagNode):
    """
    Sets default arguments for all tags within this tag.
    
    Usage:
    
        [code lang=bbdocs linenos=0][args arg1=val1]
...
[/args][/code]
        
    Example:
    
        [code lang=bbdocs linenos=0][args align=right]
[img]http://www.mysite.com/1.png[/img]
[img]http://www.mysite.com/2.png[/img]
[/args][/code]
        
    This would align both images 'right'.
    """
    open_pattern = re.compile('\[args(?P<args>(=[^\]]+)| ([^\]]+))\]')
    close_pattern = re.compile(patterns.closing % 'args')
    verbose_name = 'Arguments'
    
    def __init__(self, parent, match, content, context):
        TagNode.__init__(self, parent, match, content, context)
        arg = match.group('args')
        self.args = self.variables.lazy_resolve(arg.strip('"') if arg else '')
    
    def parse(self):
        # get the arguments
        if self.args.startswith('='):
            return self.parse_single(self.args[1:])
        else:
            return self.parse_multi(dict(map(lambda x: x.split('='), filter(bool, self.args.split(' ')))))
            
    def parse_multi(self, argdict):
        def recurse(nodes, argdict):
            for node in nodes:
                if hasattr(node, 'arguments'):
                    for key, value in node.arguments.iteritems():
                        if key in argdict:
                            node.arguments[key] = argdict[key]
                if node.nodes:
                    recurse(node.nodes, argdict)
        recurse(self.nodes, argdict)
        inner = ''
        for node in self.nodes:
            inner += node.parse()
        return inner
    
    def parse_single(self, arg):
        def recurse(nodes, argument):
            for node in nodes:
                if hasattr(node, 'argument'):
                    node.argument = argument
                if node.nodes:
                    recurse(node.nodes, argument)
        recurse(self.nodes, arg)
        inner = ''
        for node in self.nodes:
            inner += node.parse()
        return inner
    

class BBStyleRange(MultiArgumentTagNode):
    """
    A very basic numerical loop. Useful for inserting lots of numbered pictures.
    
    Usage:
    
        [code lang=bbdocs linenos=0][range start=1 end=16 name=index zeropad=3]
...
[/range][/code]
        
    Arguments:
    
        start: the first number in the loop
        end: the last number in the loop
        name: the name of the variable to assign the number to within the loop
        zeropad: enables zeropadding. eg. 1 with zeropad 3 becomes 001.
        
    Example:
    
        [code lang=bbdocs linenos=0][range end=10]
[img]http://www.mysite.com/img_$index$.png[/img]
[/range][/code]
        
        is the equivalent to:
    
        [code lang=bbdocs linenos=0][img]http://www.mysite.com/img_001.png[/img]
[img]http://www.mysite.com/img_002.png[/img]
[img]http://www.mysite.com/img_003.png[/img]
[img]http://www.mysite.com/img_004.png[/img]
[img]http://www.mysite.com/img_005.png[/img]
[img]http://www.mysite.com/img_006.png[/img]
[img]http://www.mysite.com/img_007.png[/img]
[img]http://www.mysite.com/img_008.png[/img]
[img]http://www.mysite.com/img_009.png[/img]
[img]http://www.mysite.com/img_010.png[/img][/code]
    """
    _arguments = {
        'start': '1',
        'end': '',
        'name': 'index',
        'zeropad': '3'
    }
    
    @staticmethod
    def open_pattern():
        pat = r'\[range'
        for arg in BBStyleRange._arguments:
            pat += patterns.argument
        pat += r'\]'
        return re.compile(pat)
    
    close_pattern = re.compile(patterns.closing % 'range')
    verbose_name = 'Range'
    
    def parse(self):
        if not self.arguments.end:
            return self.soft_raise('Range tag requires an end argument')
        if not self.arguments.start.isdigit() or not self.arguments.end.isdigit():
            return self.soft_raise('Range arguments must be digits')
        if not self.arguments.zeropad.isdigit():
            return self.soft_raise('Range argument zeropad must be digit')
        start = int(str(self.arguments.start))
        end   = int(str(self.arguments.end))
        zeropad = int(str(self.arguments.zeropad))
        if start < 0 or end < start:
            return self.soft_raise('Range arguments start must be positive and end must be bigger than start')
        output = ''
        for i in range(start, end + 1):
            self.variables.add(self.arguments.name, '%%0%si' % zeropad % i)
            output += self.parse_inner()
        return output
register(BBStyleArguments)
register(BBStyleVariableDefinition)
register(BBStyleRange)