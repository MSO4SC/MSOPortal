""" Auxiliar methods for models """

from threading import Thread
from django.forms.models import model_to_dict


def backend(function):
    """ decorator to run in another thread """
    def decorator(*args, **kwargs):
        """ decorator function """
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator


def _to_dict(model_instance):
    if model_instance is None:
        return None
    else:
        return model_to_dict(model_instance)
