'''
functions for image handling
'''

def create_thumbnail(source):
    '''
    produces 100x100 thumbnail for use in announcments, proposals
    '''
    from easy_thumbnails.files import get_thumbnailer
    thumbnail_options = dict(size=(100, 100), crop=True)
    return get_thumbnailer(source).get_thumbnail(thumbnail_options).file