"""
BB Code parser by Jonas 'Ojii' Obrist (c) 2009

USAGE:

Parsing:

parsed, errors = bbcode.parse(content, strict=True)

This might raise a bbocde.PaserError if strict is True (default). Otherwise on a
ParserError the content is returned unparsed and errors contains the reason.

Validation:

errors = bbcode.validate(content)

Returns errors caused by parsing the code or an empty sequence.

Extending:

Subclassing bbcode.TagNode and bbcode.register the class adds new BB Code Tags.
Each node must have an opening and closing pattern (open_pattern, close_pattern)
and push, pushed, pull and close methods. For further information read the doc
strings of the TagNode class.
"""
import re
import cgi

try:
    from django.utils.translation import ugettext as _
except ImportError:
    _ = lambda x: x

AUTODISCOVERED = False

LINEFEED_PATTERN = re.compile('\n\s*\n', re.MULTILINE)
def convert_linefeeds(content):
    content = LINEFEED_PATTERN.sub('<br /><br />', content)
    return content.replace('\n', '<br />')


class UnmatchablePseudoPattern(object):
    """
    A class which should look like a compiled regular expression but never match.
    """
    def match(self, content):
        return False
    
    def search(self, content):
        return False
    
    def finditer(self, content):
        return iter([])
    
    def sub(self, replacement, content):
        return content


class patterns:
    """
    This is a class for namespacing reasons
    """
    no_argument = r'\[%s\]'
    self_closing_tag = r'\[%s\s*/\]'
    single_argument = r'\[%s(\]|="?(?P<argument>[^\]]+)"?\])'
    argument = r'( (\w+)=([^\] ]+))?'
    closing = r'\[/%s\]'
    unmatchable = UnmatchablePseudoPattern()
     
def get_tag_name(klass):
    """
    Convert a class to tagname
    """
    return klass.tagname if hasattr(klass, 'tagname') else klass.__name__.lower()

class NeedsSubclassingError(Exception): pass
class ParserError(Exception): pass


class SoftException(object):
    def __init__(self, lineno, message):
        self.lineno = lineno
        self.message = message
        
    def __str__(self):
        return '<span class="bbcode-error lineno">Line %s:</span> <span class="bbcode-error message">%s</span>' % (self.lineno, self.message)
    __unicode__ = __str__


class SoftExceptionManager(object):
    """
    Allows 'soft exceptions'. Soft exceptions are exceptions which don't break
    the flow of the code but are rather stored in a list and can then be told
    given to the user.
    """
    def __init__(self):
        self.exceptions = []
        self.line_number = 1
        
    def set_line_number(self, number):
        """
        Update the line number
        """
        self.line_number = number
        
    def soft_raise(self, exception):
        """
        Soft raise an exception. Stores the line number the exception occured
        and the exception message. If deployed in django it will make the 
        message i18n ready.
        """
        self.exceptions.append(SoftException(self.line_number, _(exception)))
        
    def pull(self):
        """
        Pulls all exception since initialization or last pull. Resets exception
        list.
        """
        old = self.exceptions
        self.exceptions = []
        return old

sem = SoftExceptionManager()
soft_raise = sem.soft_raise

class VariableScope(dict):
    def add(self, name, value):
        dict.__setitem__(self, str(name), str(value))
        
    def resolve(self, context):
        context = context.strip('"')
        for var, value in dict.iteritems(self):
            context = context.replace('$%s$' % var, value)
        return context
    
    def lazy_resolve(self, context):
        class Lazy:
            def __init__(self, resolver, context):
                self.resolver = resolver
                self.context = context
                
            def __int__(self):
                self.context = self.resolver(self.context)
                return int(self.context)
                
            def __getattr__(self, attr):
                self.context = self.resolver(self.context)
                return self.context.__getattribute__(attr)
        return Lazy(self.resolve, context)


class Node(object):
    """
    This is the baseclass for all objects in a BBCode Parse Tree.
    To understand Nodes it is important to understand the Tree.
    Each Parse Tree has one, and only one, head node. This node has child nodes
    and those children have child nodes themselves. This continues until there
    are no more child nodes. In a standard Parse Tree the last leaves of a 
    branch are instances of TextNode, however since empty TextNodes are not kept
    in the Tree, they might also be missing.
    
    When the Parse Tree is generated the nodes get 'pushed', 'appended', 'pulled'
    and 'closed'. Only TextNodes can be appended to a node's nodelist. When a
    new child node is found it is 'pushed' and becomes the current node. When a
    node cannot be closed correctly it is 'pulled', which means it's unparsed
    contents are added to it's parent. Usually this causes a ParserError, which
    means the Tree is not parseable. When a node is finished parsing it's
    'closed' which normally returns the parent.
    """
    name = 'node'
    
    is_text_node = False
    
    def __init__(self, parent, match, fullcontent, context=None):
        """
        Normal nodes take their parent node as first argument, the regular
        expression match as second argument and the full context as third
        argument.
        """
        self.start = match.start()
        self.fullcontent = fullcontent
        self.raw_content = ''
        self.parent = parent
        self.match = match
        self.nodes = []
        self.context = context # for django only
        # copy the variable scope
        self.variables = parent.variables

        
    def soft_raise(self, errmsg):
        soft_raise(errmsg)
        return self.raw_content
    
    def append(self, text):
        """
        Adds a text node to the node
        """
        self.nodes.append(TextNode(self, text))
    
    def push(self, nodeklass, match, fullcontent):
        """
        Adds a nested tag node and returns that node
        """
        node = nodeklass(self, match, fullcontent, self.context)
        self.nodes.append(node)
        return node.pushed()
    
    def pushed(self):
        """
        Normal Nodes return themselves when being pushed. Self closing nodes
        can overwrite this method to handle this in another fashion.
        """
        return self
    
    def pull(self, end):
        """
        Pulls all text nodes and returns the parent
        """
        ###
        # Adding this try, except allows for errors to be returned to form -nh
        ####
        try:
            self.parent.nodes.append(TextNode(self.fullcontent[self.start:end]))
        except:
            pass
        return self.parent
    
    def close(self, end):
        """
        When closing the node just return the parent.
        """
        self.end = end
        self.raw_content = self.fullcontent[self.start:end]
        return self.parent
    
    def parse(self):
        """
        Parses the node. This is also responsible to parse child nodes. Should
        return a string and fail silently.
        """
        raise NeedsSubclassingError
        

class HeadNode(Node):
    """
    The head node of the BBCode parse tree.
    """
    name = 'head'
    def __init__(self, raw_content, context=None):
        self.raw_content = raw_content
        self.nodes = []
        self.context = context
        self.variables = VariableScope()
    
    def pull(self, end):
        raise ParserError, "Cannot pull from headnode, invalid BBCode Tree"
    
    def close(self, end):
        raise ParserError, "Cannot close headnode, invalid BBCode Tree"
    
    def parse(self):
        content = ''
        failed  = []
        for node in self.nodes:
            content += node.parse()
        return content
    
    
class TextNode(Node):
    smilie_pattern = re.compile(':(?P<name>\w+):')
    is_text_node = True
    def __init__(self, parent, text):
        self.text = text
        self.variables = parent.variables
        self.parent = parent
        self.raw_content = text
        self.nodes = []

    def append(self, text):
        raise TypeError, "TextNode does not support appending"
    
    def push(self, node):
        raise TypeError, "TextNode does not support pushing"
    
    def pull(self, end):
        raise TypeError, "TextNode does not support pulling"
    
    def close(self, end):
        raise TypeError, "TextNode does not support closing"
    
    def __repr__(self):
        return '<TextNode instance "%s">' % self.text
    
    def parse(self):
        """
        Return cgi-escaped content
        """
        return cgi.escape(self.variables.resolve(self.text))
    
    def __str__(self):
        return 'TextNode: %r' % self.text
        
    
class TagNode(Node):
    @staticmethod
    def open_pattern():
        raise NeedsSubclassingError
    @staticmethod
    def close_pattern():
        raise NeedsSubclassingError
    
    def parse_inner(self):
        """
        Shortcut for parsing all inner nodes and return their combined contents.
        """
        inner = ''
        for node in self.nodes:
            inner += node.parse()
        return inner
    
    def __str__(self):
        return self.__class__.__name__
    
    
class ReplaceTagNode(TagNode):
    """
    A specialized TagNode subclass with a predefined parse method. It allows
    easy creation of simple bbcode - html replacement tags. [tag] becomes <tag>
    and [/tag] becomes </tag>. These tags do not take any arguments and parse
    all inner content.
    Requires an explicit 'tagname' attribute, otherwise the lowered class name
    will be used as tagname
    """
    def __init__(self, parent, match, content, context):
        """
        Implicitly set tag name if not available.
        """
        if not hasattr(self, 'tagname'):
            self.tagname = self.__class__.__name__.lower()
        TagNode.__init__(self, parent, match, content, context)
        
    def parse(self):
        return '<%s>%s</%s>' % (self.tagname, self.parse_inner(), self.tagname)
    
    def __str__(self):
        return 'ReplaceTagNode: %s' % self.__class__.__name__
    
    
class ArgumentTagNode(TagNode):
    """
    TagNode which takes one (or no) argument. Open pattern must have a named
    group 'argument'.
    """
    def __init__(self, parent, match, content, context):
        TagNode.__init__(self, parent, match, content, context)
        arg = match.group('argument')
        self.argument = self.variables.lazy_resolve(arg.strip('"') if arg else '')
 
    def __str__(self):
        return '%s (%s)' % (self.__class__.__name__, self.argument)


class _MultiArgs(dict):
    """
    Dictionary-like class which allows items to be accessed via attributes.
    """
    def __getattr__(self, attr):
        return dict.__getitem__(self, attr)
        
        
class MultiArgumentTagNode(TagNode):
    """
    TagNode which takes multiple (or no) arguments. Must have an attribute
    _arguments which holds key, value pairs of the arguments and their defaults.
    Open pattern should use bbcode.patterns.argument as argument matching
    expression.
    """
    _arguments   = []
    def __init__(self, parent, match, content, context):
        TagNode.__init__(self, parent, match, content, context)
        args = match.groups()
        kwargs = dict(self._arguments)
        for index, value in enumerate(filter(bool, args)):
            if not index or not index % 3:
                continue
            if not (index + 1) % 3:
                kwargs[args[index - 1]] = self.variables.lazy_resolve(value)
        self.arguments = _MultiArgs(kwargs)
        
    def __str__(self):
        args = []
        for key, value in self.arguments.iteritems():
            args.append('%s: %s' % (key, value))
        return '%s (%s)' % (self.__class__.__name__, ', '.join(args))
        
        
class SelfClosingTagNode(TagNode):
    """
    A tag which is self closed.
    """
    close_pattern = patterns.unmatchable
    
    def __init__(self, parent, match, content, context):
        self.start = match.start()
        self.context = context
        self.fullcontent = content
        self.raw_content = content[match.start():match.end()]
        self.parent = parent
        self.match = match
        self.nodes = []
        self.variables = parent.variables
    
    def pushed(self):
        """
        A self closing node returns it's parent. Thus it will never have child
        nodes!
        """
        return self.parent
    
    def __str__(self):
        return 'SelfClosingTag: %s' % self.__class__.__name__
    
    
class AutoDict(dict):
    def __init__(self, default_thing=set, *args, **kwargs):
        self.__default_thing = default_thing
        dict.__init__(self, *args, **kwargs)

    def __getitem__(self, item):
        if not dict.__contains__(self, item):
            dict.__setitem__(self, item, self.__default_thing() if callable(self.__default_thing) else self.__default_thing)
        return dict.__getitem__(self, item)
    
    
class Library(object):
    """
    The core of the BBCode parser. Keeps track of all bbcode tags and text
    parsers. Also handles building BBCode Parse Trees and the automated help
    generation.
    """
    name_pat1 = re.compile('([a-z0-9])([A-Z])')
    name_pat2 = re.compile('(.)([A-Z][a-z]+)')
    
    def __init__(self):
        self.names = AutoDict(None)
        self.raw_names = {}
        self.tags = AutoDict(set)
        self.klasses = AutoDict(None)
    
    def convert(self, name):
        """
        Convert a class name to something a bit more readable
        """
        return  self.name_pat1.sub(r'\1 \2', self.name_pat2.sub(r'\1 \2', name))
    
    def dsparse(self, docs):
        """
        Parse docstrings
        """
        content, errors = parse(docs, strict=False, auto_discover=True)
        return content
    
    def get_default_namespaces(self, klass):
        bits = klass.__module__.split('.')
        return (bits[-1], bits[-3], klass.__name__.lower())
        
    def register(self, klass):
        """
        Register a BBCode Tag Node
        """
        # Add the class to their namespaces.
        if hasattr(klass, 'namespaces'):
            for ns in klass.namespaces:
                self.tags[ns].add(klass)
                if not hasattr(klass, 'not_in_all') or not klass.not_in_all:
                    self.tags['__all__'].add(klass)
        elif not hasattr(klass, 'not_in_all') or not klass.not_in_all:
            self.tags['__all__'].add(klass)
        if not hasattr(klass, 'namespaces'):
            setattr(klass, 'namespaces', [])
        d_namespaces = self.get_default_namespaces(klass)
        for default in d_namespaces:
            self.tags[default].add(klass)
        for ns in reversed(d_namespaces):
            klass.namespaces.insert(0, ns)
        # Register documentation
        docstrings = klass.__doc__
        if hasattr(klass, 'tagname'):
            tagname = klass.tagname
        else:
            tagname = klass.__name__.lower()
        if docstrings:
            if hasattr(klass, 'verbose_name'):
                verbose_name = klass.verbose_name
            else:
                verbose_name = self.convert(klass.__name__)
            self.names[tagname] = {'docs': docstrings.strip(),
                                   'name': verbose_name,
                                   'class': klass}
            self.klasses[klass] = self.names[tagname]
        self.raw_names[klass.__name__] = klass
        
    def add_namespace(self, klass, *namespaces):
        """
        Add a tag to a namespace or several namespaces
        """
        if isinstance(klass, TagNode):
            for namespace in namespaces:
                self.tags[namespace].add(klass)
        elif isinstance(klass, basestring):
            if klass in self.raw_names:
                self.add_namespace(self.raw_names[klass], *namespaces)
            elif klass in self.names:
                self.add_namespace(self.names[klass]['class'], *namespaces)
                
    def remove_namespace(self, klass, *namespaces):
        """
        Remove a tag from a namespace or several namespaces
        """
        if isinstance(klass, TagNode):
            for namespace in namespaces:
                if klass in self.tags[namespace]:
                    self.tags[namespace].remove(klass)
        elif isinstance(klass, basestring):
            if klass in self.raw_names:
                self.add_namespace(self.raw_names[klass], *namespaces)
            elif klass in remove_namespace.names:
                self.remove_namespace(self.names[klass]['class'], *namespaces)
                
    def set_not_in_all(self, klass, flag=True):
        """
        Set 'not_in_all' for a tag.
        """
        if flag:
            self.remove_namespace(klass, '__all__')
        else:
            self.add_namespace(klass, '__all__')
            
    def get_help(self, *tags):
        """
        Get help for a tag or for all tags.
        
        Returns a dictionary with keys 'name', 'tag', 'docstring'.
        """
        if not tags:
            tags = self.get_tags()
        help_objects = []
        for tag in tags:
            if issubclass(tag, Node):
                obj = self.klasses[tag]
                if obj is None:
                    continue
            else:
                obj = self.names[tag]
                if obj is None:
                    continue
            help_objects.append({'name': obj['name'],
                                 'docstring': parse(obj['docs'], strict=False, auto_discover=True)[0],
                                 'obj': obj['class']})
        return help_objects
    
    def get_tags(self, namespaces=None):
        """
        Get a list of tag classes for the namespaces
        """
        if namespaces is None:
            namespaces = get_default_namespaces()
        tags = set()
        exclude = []
        include = []
        # Split the 'namespaces' into exclude and include namespaces
        for ns in namespaces:
            if ns.startswith('no-'):
                _ns = ns[3:]
                if _ns in self.tags:
                    exclude.append(_ns)
            elif ns in self.tags:
                include.append(ns)
        # Include first
        if not include or '__all__' in include:
            tags = set(self.tags['__all__'])
        else:
            if 'base' in include:
                tags = set(self.tags['__all__'])
            for ns in include:
                tags = tags.union(self.tags[ns])
        # Then exclude
        for ns in exclude:
            tags = tags.difference(self.tags[ns])
        return tags
    
    def get_taglist(self, content, namespaces=None):
        """
        Get the tag-match list of a content for given namespaces
        """
        if namespaces is None:
            namespaces = get_default_namespaces()
        tags = self.get_tags(namespaces)
        # Build tag list
        taglist = []
        for tagklass in tags:
            op = tagklass.open_pattern
            if callable(op):
                op = op()
            i = 1
            for match in op.finditer(content):
                i += 1
                taglist.append((match.start(), match, tagklass, True))
            cp = tagklass.close_pattern
            if callable(cp):
                cp = cp()
            for match in cp.finditer(content):
                taglist.append((match.start(), match, tagklass, False))
        # Sort by position
        return sorted(taglist)
    
    def get_parse_tree(self, content, namespaces=None, context=None):
        """
        Prepare content for parsing.
        Returns a HeadNode instance
        """
        if namespaces is None:
            namespaces = get_default_namespaces()
        taglist = self.get_taglist(content, namespaces)
        
        # Get headnode
        headnode = HeadNode(content, context)
        
        lastpos = 0
        currentnode = headnode
        # Loop over tag matches
        for pos, match, tagklass, opener in taglist:
            start, end = match.span()
            # Prevent tags matching within other tags (eg AutoDetectURL)
            if start < lastpos:
                continue
            # Append text between last tag and this one
            text = content[lastpos:start]
            if text:
                currentnode.append(text)
            # Set new position
            lastpos = end
            # Get line number for soft exceptions
            lineno = content[:start].count('\n') + 1
            sem.set_line_number(lineno)
            # if opener, push new node
            if opener:
                currentnode = currentnode.push(tagklass, match, content)
            # else close the tag
            else:
                # pull all unclosed child tags of the current node
                while tagklass != currentnode.__class__:
                    try:
                        currentnode = currentnode.pull(end)
                    except ParserError:
                        sem.soft_raise("Error: BBCode could not be parsed. There are probably unclosed or uneven tags!")
                        raise ParserError, "Failed to find matching opening tag for closing tag '%s' in line %s."  % (get_tag_name(tagklass), lineno)
                # close the node
                currentnode = currentnode.close(end)
        text = content[lastpos:]
        if text:
            headnode.append(text)
        # Return the head node
        return headnode
    
    def get_visual_parse_tree(self, content, namespaces=None, indent=4):
        if namespaces is None:
            namespaces = get_default_namespaces()
        def recurse(nodes, level, indent):
            cindent = level * indent
            sindent = ' ' * cindent
            next = level + 1
            l = []
            for node in nodes:
                l.append('%s-%s' % (sindent, str(node)))
                l += recurse(node.nodes, next, indent)
            return l
        try:
            head = self.get_parse_tree(content, namespaces)
        except ParserError:
            return '-Parse Error'
        visuals = ['-HeadNode']
        visuals += recurse(head.nodes, 1, indent)
        return '\n'.join(visuals)
    
    def validate(self, content, namespaces=None, auto_discover=False):
        """
        Validates a given content and returns the errors or an empty sequence.
        """
        if namespaces is None:
            namespaces = get_default_namespaces()
        if auto_discover:
            autodiscover()
        try:
            headnode = self.get_parse_tree(content, namespaces)
        except ParserError:
            return sem.pull()
        parsed = headnode.parse()
        return sem.pull()


lib = Library()
register = lib.register
validate = lib.validate
get_help = lib.get_help
get_visual = lib.get_visual_parse_tree

def get_default_namespaces():
    from django.conf import settings
    if hasattr(settings, 'BBCODE_DEFAULT_NAMESPACES'):
        return settings.BBCODE_DEFAULT_NAMESPACES
    return ['__all__']
    
def parse(content, namespaces=None, strict=False, auto_discover=False,
          context=None):
    """
    Parse a content with the BBCodes
    """
    if auto_discover:
        autodiscover()
    if namespaces is None:
        namespaces = get_default_namespaces()
    # Fix windows linefeeds
    content = content.replace('\r','')
    # Get head node
    if strict:
        head = lib.get_parse_tree(content, namespaces, context)
    else:
        try:
            head = lib.get_parse_tree(content, namespaces, context)
        except ParserError:
            return convert_linefeeds(content), sem.pull()
    # parse BB Codes
    content = head.parse()
    # fix urls
    from utils.helpers import rhizome_urlize
    content = rhizome_urlize(content)
    # Replace linefeeds
    content = convert_linefeeds(content)
    return content, sem.pull()
    
def autodiscover():
    """
    Automatically register all bbcode tags. This searches the 'bbtags' modules
    of all INSTALLED_APPS if available.
    """
    global AUTODISCOVERED
    if AUTODISCOVERED:
        return
    import imp
    from django.conf import settings
    import os

    for app in settings.INSTALLED_APPS:
        try:
            module = __import__(app, {}, {}, [app.split('.')[-1]])
            app_path = module.__path__
        except AttributeError:
            continue
        try:
            imp.find_module('bbtags', app_path)
        except ImportError:
            continue
        for f in os.listdir(os.path.join(os.path.dirname(os.path.abspath(module.__file__)), 'bbtags')):
            mod_name, ext = os.path.splitext(f)
            if ext == '.py':
                __import__("%s.bbtags.%s" % (app, mod_name))
    AUTODISCOVERED = True