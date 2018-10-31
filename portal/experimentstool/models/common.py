""" Auxiliar methods for models """

from threading import Thread
from typing import Dict, List
from django.forms.models import model_to_dict


INPUT_TAG = 'INPUT'
REPLACE_TAG = 'REPLACE'
SECRET_TAG = 'secret'
NAME_TAG = 'name'
ORDER_TAG = 'order'


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


def get_inputs_list(definition, parent_key=''):
    inputs: List = []
    if isinstance(definition, Dict):
        # For each key, process if it is an input, or call recursively if not
        for key, value in definition.items():
            if _is_input(value):
                # Key never be null in this stage
                inputs.append((parent_key+"."+key, value[INPUT_TAG]))
            else:
                # if it is no input, call recursively
                inputs += get_inputs_list(value, parent_key=parent_key+"."+key)
    elif isinstance(definition, List):
        # Call recursively for each item in the list
        for index, item in enumerate(definition):
            inputs += get_inputs_list(
                item,
                parent_key=parent_key+"."+str(index))
    else:
        pass  # If not a dictionary or a list, for sure is not an input

    if not parent_key:  # First iteration
        return sorted(
            inputs,
            key=lambda item: (
                item[1][ORDER_TAG] if ORDER_TAG in item[1] else 1000, item[1][NAME_TAG]))
    else:
        return inputs


def delete_secrets(definition, instance):
    if isinstance(definition, Dict):
        # For each key, process if it is an input, or call recursively if not
        no_secrets_instance: Dict = {}
        for key, value in definition.items():
            if _is_input(value):
                # if it is not secret put instance value, else dont't put anything
                if not _is_input_secret(value):
                    no_secrets_instance[key] = instance[key]
            else:
                # if it is no input, call recursively
                no_secrets_instance[key] = delete_secrets(value, instance[key])
        return no_secrets_instance
    if isinstance(definition, List):
        # Call recursively for each item in the list
        no_secrets_instance: List = []
        for defn, inst in zip(definition, instance):
            no_secrets_instance.append(delete_secrets(defn, inst))
        return no_secrets_instance

    # The item can be processed anymore, return the instance value
    return instance


def _is_input(entry):
    return isinstance(entry, Dict) \
        and INPUT_TAG in entry \
        and isinstance(entry[INPUT_TAG], Dict)


def _is_input_secret(entry):
    """ It assumes that the entry is an input """
    return SECRET_TAG in entry[INPUT_TAG] \
        and entry[INPUT_TAG][SECRET_TAG]
