import string
import random

from django.shortcuts import render_to_response

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User


def make_username(length=20):
    return ''.join([random.choice(string.ascii_letters) for _ in xrange(length)])

def index(request):
    user = User.objects.create(
        username = make_username()
    )
    user.username = make_username()
    User.objects.filter(pk=user.pk).delete()
    return render_to_response('index.html')
