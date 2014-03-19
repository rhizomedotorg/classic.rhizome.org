from bbcode import *
import re


class OL(MultiArgumentTagNode):
    """
    Creates an ordered list.
    
    Usage:
    
    [code lang=bbdocs linenos=0][ol]
  [*] First item
  [*] Second item
[/ol][/code]
    """
    _arguments = {'css': '',
                  'itemcss': ''}
    
    @staticmethod
    def open_pattern():
        pat = r'\[ol'
        for arg in OL._arguments:
            pat += patterns.argument
        pat += r'\]'
        return re.compile(pat)
    
    close_pattern = re.compile(patterns.closing % 'ol')
    verbose_name = 'Ordered List'
    
    def list_parse(self):
        # Parse list items ([*])
        if self.arguments.itemcss:
            css = ' class="%s"' % self.arguments.itemcss.replace(',',' ')
        else:
            css = ''
        items = self.parse_inner().split('[*]')[1:]
        real = ''
        for item in items:
            real += '<li%s>%s</li>' % (css, item)
        return real
        
    def parse(self):
        if self.arguments.css:
            css = ' class="%s"' % self.arguments.css.replace(',',' ')
        else:
            css = ''
        return '<ol%s>%s</ol>'  % (css, self.list_parse())


class UL(OL):
    """
    Creates an unordered list.
    
    Usage:
    
        [code lang=bbdocs linenos=0][ul]
  [*] First item
  [*] Second item
[/ul][/code]
    """
    @staticmethod
    def open_pattern():
        pat = r'\[ul'
        for arg in UL._arguments:
            pat += patterns.argument
        pat += r'\]'
        return re.compile(pat)
    close_pattern = re.compile(patterns.closing % 'ul') 
    verbose_name = 'Unordered List'
    
    def parse(self):
        if self.arguments.css:
            css = ' class="%s"' % self.arguments.css.replace(',',' ')
        else:
            css = ''
        return '<ul%s>%s</ul>'  % (css, self.list_parse())
register(OL)
register(UL)