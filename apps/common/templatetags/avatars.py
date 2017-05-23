# coding=UTF-8
from django.template import Library, Node, TemplateSyntaxError, Variable
from django.conf import settings

from userprofile.models import Avatar, S3BackendNotFound
from apps.router.models import User

try:
    from PIL import Image
except ImportError:
    import Image

# from PythonMagick import Image
#from apps.common.utils.utils_TuxieMagick import Image
from django.core.files.storage import default_storage
if hasattr(settings, "AWS_SECRET_ACCESS_KEY"):
    try:
        from backends.S3Storage import S3Storage
        storage = S3Storage()
    except ImportError:
        raise S3BackendNotFound
else:
    storage = default_storage

register = Library()

class ResizedThumbnailNode(Node):
    def __init__(self,id, size):

        if id:
            self.user = Variable(id)
        else:
            self.user = Variable("user")

        try:
            self.size = int(size)
        except:
            self.size = Variable(size)

    def render(self, context):
        # If size is not an int, then it's a Variable, so try to resolve it.
        if not isinstance(self.size, int):
            self.size = int(self.size.resolve(context))

        user = self.user.resolve(context)
        try:
            if isinstance(user,basestring):
                user = User.objects.get(id=user)
            avatar = Avatar.objects.get(user=user, valid=True).image
            url = avatar.url
        except Exception ,e:
            url = '/site_media/img/generic.jpg'
        if self.size!=0:
            return '''<img src="%s" width="%s" height="%s">'''%(url,self.size,self.size)
        else:
            return url

@register.tag('avatar')
def Thumbnail(parser, token):
    bits = token.contents.split()
    id,size ='','0'
    if len(bits) > 3:
        raise TemplateSyntaxError, _(u"You have to provide only the size as \
            an integer (both sides will be equal) and optionally, the \
            username.")
    elif len(bits) == 3:
        id,size = bits[1],bits[2]
    elif len(bits) == 2:
        id,size = bits[1],'0'
    elif len(bits) == 1:
        id,size = '','0'
    return ResizedThumbnailNode(id,size)



