from django import template
from django.utils.safestring import mark_safe
from utils.helpers import strip_bbcode 

bbmodule = __import__('bbcode',level=0)

register = template.Library()

class PseudoVar(object):
    def __init__(self, content):
        self.content = content
        self.var = content
        
    def resolve(self, context):
        return self.content


class BBCodeNode(template.Node):
    def __init__(self, content, namespaces, varname):
        self.content = template.Variable(content)
        self.namespaces = []
        for ns in namespaces:
            if ns[0] == ns[-1] and ns[0] in ('"',"'"):
                self.namespaces.append(PseudoVar(ns[1:-1]))
            else:
                self.namespaces.append(template.Variable(ns))
        self.varname = varname

    def render(self, context):
        try:
            content = self.content.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        namespaces = set()
        for obj in self.namespaces:
            ns = obj.resolve(context)
            if type(ns) in (list, tuple):
                namespaces = namespaces.union(ns)
            else:
                namespaces.add(ns)
        
        try:
            parsed, errors = bbmodule.parse(content, namespaces, False, True, context)
            
            if self.varname:
                context[self.varname] = mark_safe(parsed)
                return ''
            else:
                return mark_safe(parsed)
        except:
            return strip_bbcode(content)

@register.tag
def bbcode(parser, token):
    """
    Parses a context with the bbcode markup.
    
    Usage:
        
        {% bbcode <content> [<namespace1>, [<namespace2>...]] %}
        
    Params:
    
        <content> either a string of content or a template variable holding the
        content.
        
        <namespaceX> either a string or a template variable holding a string,
        list or tuple.
    
    WARNING: Errors are explicitly silenced in this tag because errors should be
    raised when 'content' is saved to the database (or where ever it is saved to).
    
    Please use bbcode.validate(...) on your content before saving it.
    """
    bbmodule.autodiscover()
    bits = token.contents.split()
    tag_name = bits.pop(0)
    try:
        content = bits.pop(0)
    except ValueError:
        raise template.TemplateSyntaxError, "bbcode tag requires at least one argument"
    varname = None
    if len(bits) > 1:
        if bits[-2] == 'as':
            varname = bits[-1]
        bits = bits[:-2]
    return BBCodeNode(content, bits, varname)


class BBHelpVarnameNode(template.Node):
    def __init__(self, tags, varname):
        self.tags = tags
        self.varname = varname
            
    def render(self, context):
        context[self.varname] = bbmodule.get_help(*self.tags)
        return ''
    
    
class BBHelpTemplateNode(template.Node):
    def __init__(self, tags, tplfile):
        self.tags = tags
        if tplfile[0] == tplfile[-1] and tplfile[0] in ('"',"'"):
            self.tplfile = PseudoVar(tplfile[1:-1])
        else:
            self.tplfile = template.Variable(tplfile)
            
    def render(self, context):
        try:
            realtplfile = self.tplfile.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        rendered_tags = []
        tpl = template.loader.get_template(realtplfile)
        for tag in bbmodule.get_help(*self.tags):
            rendered_tags.append(tpl.render(template.Context({'tag': tag})))
        return '\n'.join(rendered_tags)
        


@register.tag
def bbhelp(parser, token):
    """
    Renders help about the bbcode system
    
    Usage:
    
        {% bbhelp [tag1, tag2 ...] [in namespace1, namespace2] using template.htm|as varname %}
        
    Params:
        
        <tagX> optional list of tags to return help about
        <namespaceX> optional list of namespaces to return help about
        <template.htm> template to render the help with
        <varname> varname to store the help in
        
    Either 'using template' or 'as varname' must be present. 
    """
    bbmodule.autodiscover()
    bits = token.contents.split()
    tag_name = bits.pop(0)
    raw_tags = []
    raw_namespaces = []
    bit = None
    tplfile = None
    varname = None
    while bits:
        bit = bits.pop(0)
        if bit in ('in', 'using', 'as'):
            break
        raw_tags.append(bit)
    # Namespace check
    if bit == 'in':
        while bits:
            bit = bits.pop(0)
            if bit in ('using', 'as'):
                break
            raw_namespaces.append(bit)
    # template check
    if bit == 'using':
        tplfile = bits.pop(0)
    # varname check 
    elif bit == 'as':
        varname = bits.pop(0)
    else:
        raise template.TemplateSyntaxError, "bbhelp requires either an 'as varname' or 'using template' argument"
    # convert raw_tags/raw_namespaces to list of tags
    tags = set()
    if raw_namespaces or raw_tags:
        for ns in raw_namespaces:
            tags.update(bbmodule.lib.tags[ns])
        for tg in raw_tags:
            tginfo = bbmodule.lib.names[tg]
            if tginfo:
                tags.add(tginfo['class'])
    else:
        tags = bbmodule.lib.get_tags()
    if not tags:
        raise template.TemplateSyntaxError, "bbhelp requires tags."
    tags = sorted(tags, key=lambda x: x.namespaces)
    # Get the Node
    if tplfile:
        return BBHelpTemplateNode(tags, tplfile)
    else:
        return BBHelpVarnameNode(tags, varname)