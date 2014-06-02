from django.utils import simplejson
from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register

@dajaxice_register
def randomize(request):
    dajax = Dajax()
    dajax.assign('#result', 'value', random.randint(1, 10))
    return dajax.json()