from bbcode import *
import re
import urllib

class Url(TagNode):
    """
    Creates a hyperlink.
    
    Usage:
     
    [code lang=bbdocs linenos=0][url=<http://www.domain.com>]Text[/url]
    [url]http://www.domain.com[/url][/code]
    """
    verbose_name = 'Link'
    open_pattern = re.compile(r'(\[url\]|\[url="?(?P<href>[^\]]+)"?\]|\[url (?P'
                               '<arg1>\w+)="?(?P<val1>[^ ]+)"?( (?P<arg2>\w+)="'
                               '?(?P<val2>[^ ]+)"?)?\])')
    close_pattern = re.compile(patterns.closing % 'url')
    
    def parse(self):
        gd = self.match.groupdict()
        gd.update({'css':''})
        if gd['arg1']:
            gd[gd['arg1']] = gd['val1']
        if gd['arg2']:
            gd[gd['arg2']] = gd['val2']
        if gd['href']:
            href = self.variables.resolve(gd['href'])
            inner = self.parse_inner()
        else:
            inner = ''
            for node in self.nodes:
                if node.is_text_node or isinstance(node, AutoDetectURL):
                    inner += node.raw_content
                else:
                    self.soft_raise("Url tag cannot have nested tags without "
                                    "an argument.")
            href = self.variables.resolve(inner)
            inner = href
        if gd['css']:
            css = ' class="%s"' % gd['css'].replace(',',' ')
        else:
            css = ''
        raw_href = self.variables.resolve(href)
                
#         if raw_href.startswith('http://'):
#             href = raw_href[:7] + urllib.quote(raw_href[7:], safe)
#         else:
#             href = urllib.quote(raw_href, safe)        
        
        #return '<a href="%s"%s>%s</a>' % (href, css, inner)    
        
        href =  raw_href
        
        if "http://" not in href:
            return '<a target="_blank" href="http://%s"%s>%s</a>' % (href, css, inner) 
        else:
            return '<a target="_blank" href="%s"%s>%s</a>' % (href, css, inner)    


class Email(TagNode):
    """
    Creates an email link.
    
    Usage:
    
    [code lang=bbdocs linenos=0][email]name@domain.com[/email]
[email=<name@domain.com>]Text[/email][/code]
    """
    verbose_name = 'E-Mail'
    open_pattern = re.compile(r'(\[email\]|\[email=(?P<mail>[^\]]+\]))')
    close_pattern = re.compile(patterns.closing % 'email')

    def parse(self):
        gd = self.match.groupdict()
        email = gd.get('email', None)
        if email:
            inner = ''
            for node in self.nodes:
                if node.is_text_node or isinstance(node, AutoDetectURL):
                    inner += node.raw_content
                else:
                    inner += node.parse()
            return '<a href="mailto:%s">%s</a>' % (email, inner)
        else:
            inner = ''
            for node in self.nodes:
                inner += node.raw_content
            return '<a href="mailto:%s">%s</a>' % (inner, inner)

class Img(ArgumentTagNode):
    """
    Displays an image.
    
    Usage:
    
    [code lang=bbdocs linenos=0][img]http://www.domain.com/image.jpg[/img]
[img=<align>]http://www.domain.com/image.jpg[/img][/code]
    
    Arguments:
    
    Allowed values for [i]align[/i]: left, center, right. Default: None.
    """
    verbose_name = 'Image'
    open_pattern = re.compile(patterns.single_argument % 'img')
    close_pattern = re.compile(patterns.closing % 'img')
    
    def parse(self):
        inner = ''
        for node in self.nodes:    
            if node.is_text_node or isinstance(node, AutoDetectURL):
                inner += node.raw_content
            else:
                soft_raise("Img tag cannot have nested tags without an argument.")
                return self.raw_content
        inner = self.variables.resolve(inner)
        if self.argument:
            return '<img src="%s" alt="image" class="img-%s" />' % (inner, self.argument)
        else:
            return '<img src="%s" alt="image" />' % inner
    
    
class Youtube(TagNode):
    """
    Includes a youtube video. Post the URL to the youtube video inside the tag.
    
    Usage:
    
    [code lang=bbdocs linenos=0][youtube]http://www.youtube.com/watch?v=123abc456def[/youtube][/code]
    """
    verbose_name = 'Youtube'
    _video_id_pattern = re.compile('v=([-|~_0-9A-Za-z]+)&?.*?')
    open_pattern = re.compile(patterns.no_argument % 'youtube')
    close_pattern = re.compile(patterns.closing % 'youtube')
    
    def parse(self):
        url = ''
        for node in self.nodes:
            if node.is_text_node or isinstance(node, AutoDetectURL):
                url += node.raw_content
            else:
                soft_raise("Youtube tag cannot have nested tags")
                return self.raw_content
        match = self._video_id_pattern.search(url)
        if not match:
            soft_raise("'%s' does not seem like a youtube link" % url)
            return self.raw_content
        videoid = match.groups()
        
        if not videoid:
            soft_raise("'%s' does not seem like a youtube link" % url)
            return self.raw_content
        videoid = videoid[0]
        return(
            '<object><param name="movie" value="http://www.youtube.com/v/%s&amp;hl=en&amp;fs=1&amp;"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://www.youtube.com/v/%s&amp;hl=en&amp;fs=1&amp;" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true"></embed></object>' % (videoid, videoid)
            )

class Vimeo(TagNode):
    """
    Includes a vimeo video. Post the URL to the vimeo video inside the tag.
    
    Usage:
    
    [code lang=bbdocs linenos=0][vimeo]http://vimeo.com/1234567[/vimeo][/code]
    """
    verbose_name = 'Vimeo'
    _video_id_pattern = re.compile('vimeo.com/([-|~_0-9A-Za-z]+)&?.*?')
    open_pattern = re.compile(patterns.no_argument % 'vimeo')
    close_pattern = re.compile(patterns.closing % 'vimeo')
    
    def parse(self):
        url = ''
        for node in self.nodes:
            if node.is_text_node or isinstance(node, AutoDetectURL):
                url += node.raw_content
            else:
                soft_raise("vimeo tag cannot have nested tags")
                return self.raw_content
        match = self._video_id_pattern.search(url)
        if not match:
            soft_raise("'%s' does not seem like a vimeo link" % url)
            return self.raw_content
        videoid = match.groups()
        
        if not videoid:
            soft_raise("'%s' does not seem like a vimeo link" % url)
            return self.raw_content
        videoid = videoid[0]
        return(
            '<object><param name="allowfullscreen" value="true" /><param name="allowscriptaccess" value="always" /><param name="movie" value="http://vimeo.com/moogaloop.swf?clip_id=%s&amp;server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=1&amp;color=00ADEF&amp;fullscreen=1&amp;autoplay=0&amp;loop=0" /><embed src="http://vimeo.com/moogaloop.swf?clip_id=%s&amp;server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=1&amp;color=00ADEF&amp;fullscreen=1&amp;autoplay=0&amp;loop=0" type="application/x-shockwave-flash" allowfullscreen="true" allowscriptaccess="always" width="400" height="225"></embed></object>' % (videoid, videoid)
            )

class Flash(TagNode):
    """
    Includes a flash video.
    
    [code lang=bbdocs linenos=0][flash]http://www.domain.com/flash_file.flv[/flash][/code]
    """
    verbose_name = 'Flash'
    #open_pattern = re.compile(patterns.no_argument % 'flash')
    open_pattern = re.compile(r'(\[flash\]|\[flash=\]|\[flash=([0-9]),([0-9])\])')

    close_pattern = re.compile(patterns.closing % 'flash')
    
    def parse(self):
        inner = ''
        for node in self.nodes:    
            if node.is_text_node or isinstance(node, AutoDetectURL):
                inner += node.raw_content
            else:
                soft_raise("tag cannot have nested tags.")
                return self.raw_content
        inner = self.variables.resolve(inner)
        return (
                '<object><param name="movie" value="%s"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="%s" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true"></embed></object>' % (inner,inner)
                )

class QuickTime(TagNode):
    """
    Includes a quicktime object. 
        
    [code lang=bbdocs linenos=0][qt]http://www.domain.com/quicktime_file.mp3[/qt][/code]
    """
    verbose_name = 'QuickTime'
#    open_pattern = re.compile(patterns.no_argument % 'qt')
    open_pattern = re.compile(r'(\[qt\]|\[qt=\]|\[qt=([0-9]),([0-9])\])')
    close_pattern = re.compile(patterns.closing % 'qt')
    
    def parse(self):
        inner = ''
        for node in self.nodes:    
            if node.is_text_node or isinstance(node, AutoDetectURL):
                inner += node.raw_content
            else:
                soft_raise("tag cannot have nested tags.")
                return self.raw_content
        inner = self.variables.resolve(inner)
        return (
                '<object classid="clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B" codebase="http://www.apple.com/qtactivex/qtplugin.cab"><param name="src" value="%s"><param name="autoplay" value="false"><param name="controller" value="true"><embed src="%s" autoplay="false" controller="true" pluginspage="http://www.apple.com/quicktime/download/"></embed></object>' % (inner,inner)
                )

class Director(TagNode):
    """
    Includes a director file. 
        
    Usage:
    
    [code lang=bbdocs linenos=0][director]http://www.domain.com/director_file.dcr[/director][/code]
    """
    verbose_name = 'Director'
#    open_pattern = re.compile(patterns.no_argument % 'dcr')
    open_pattern = re.compile(r'(\[dcr\]|\[dcr=\]|\[dcr=([0-9]),([0-9])\])')
    close_pattern = re.compile(patterns.closing % 'dcr')
    
    def parse(self):
        inner = ''
        for node in self.nodes:    
            if node.is_text_node or isinstance(node, AutoDetectURL):
                inner += node.raw_content
            else:
                soft_raise("tag cannot have nested tags.")
                return self.raw_content
        inner = self.variables.resolve(inner)
        return (
                '<OBJECT classid="clsid:166B1BCA-3F9C-11CF-8075-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/director/sw.cab#version=8,0,0,0" ID=recursion><param name=src value="%s"><PARAM NAME=swStretchStyle VALUE=fill><param name= swRemote value="swSaveEnabled=\'true\' swVolume=\'true\' swRestart=\'true\' swPausePlay=\'true\' swFastForward=\'true\' swContextMenu=\'true\' "><EMBED SRC="%s" swRemote="swSaveEnabled=\'true\' swVolume=\'true\' swRestart=\'true\' swPausePlay=\'true\' swFastForward=\'true\' swContextMenu=\'true\' " swStretchStyle=fill  TYPE="application/x-director" PLUGINSPAGE="http://www.macromedia.com/shockwave/download/"></EMBED></OBJECT>' % (inner,inner)
                )

class Html5Audio(TagNode):
    """
    Includes an audio file using html5 markup. Notice, not all filetypes may work and may not work in all browsers. Please read up on the html5 spec for more info 
    
     Usage:
    
    [code lang=bbdocs linenos=0][html5audio]http://www.domain.com/audio_file.mp3[/html5audio][/code]

    """
    verbose_name = 'Html5Audio'
    open_pattern = re.compile(patterns.no_argument % 'html5audio')
    close_pattern = re.compile(patterns.closing % 'html5audio')
    
    def parse(self):
        inner = ''
        for node in self.nodes:    
            if node.is_text_node or isinstance(node, AutoDetectURL):
                inner += node.raw_content
            else:
                soft_raise("tag cannot have nested tags.")
                return self.raw_content
        inner = self.variables.resolve(inner)
        return ('<audio src="%s" controls="controls">' % (inner))


class Html5Video(TagNode):
    """
    Includes an video file using html5 markup. Notice, not all filetypes may work and may not work in all browsers. Please read up on the html5 spec for more info 
    
     Usage:
    
    [code lang=bbdocs linenos=0][html5video]http://www.domain.com/video_file.mp4[/html5video][/code]

    """
    verbose_name = 'Html5Video'
    open_pattern = re.compile(patterns.no_argument % 'html5video')
    close_pattern = re.compile(patterns.closing % 'html5video')
    
    def parse(self):
        inner = ''
        for node in self.nodes:    
            if node.is_text_node or isinstance(node, AutoDetectURL):
                inner += node.raw_content
            else:
                soft_raise("tag cannot have nested tags.")
                return self.raw_content
        inner = self.variables.resolve(inner)
        return ('<video src="%s" controls="controls">' % (inner))

class AutoDetectURL(SelfClosingTagNode):
    open_pattern = re.compile('[^[\]](?#Protocol)(?:(?:ht|f)tp(?:s?)\:\/\/|~/|/'
                              ')?(?#Username:Password)(?:\w+:\w+@)?(?#Subdomain'
                              's)(?:(?:[-\w]+\.)+(?#TopLevel Domains)(?:com|org'
                              '|net|gov|mil|biz|info|mobi|name|aero|jobs|museum'
                              '|travel|[a-z]{2}))(?#Port)(?::[\d]{1,5})?(?#Dire'
                              'ctories)(?:(?:(?:/(?:[-\w~!$+|.,=]|%[a-f\d]{2})+'
                              ')+|/)+|\?|#)?(?#Query)(?:(?:\?(?:[-\w~!$+|.,*:]|'
                              '%[a-f\d{2}])+=(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)('
                              '?:&(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=(?:[-\w~!$+|.'
                              ',*:=]|%[a-f\d]{2})*)*)*(?#Anchor)(?:#(?:[-\w~!$+'
                              '|.,*:=]|%[a-f\d]{2})*)?[^[\]]')
    
    open_pattern = ''
    
    def parse(self):
        url = self.match.group().replace(" ","")
        url = url.replace(" ","")
        if "http://" not in url:
            return '<a href="http://%s">%s</a>' % (url, url)    
        else:
            return '<a href="%s">%s</a>' % (url, url)    

            
register(Url)
register(Img)
register(Email)
register(Youtube)
#register(AutoDetectURL) REPLACED THIS WITH rhizomedotorg.utils.helper rhizome_urlize in bbcode.parse
register(Flash)
register(Director)
register(QuickTime)
register(Html5Video)
register(Html5Audio)
register(Vimeo)
