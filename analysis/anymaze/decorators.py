import os
import pathlib
import functools
from typing import Any
from collections.abc import Callable

def repeat(method : Callable) -> list:
    @functools.wraps(method)
    def wrapper_repeat(self, *args, **kwargs) -> list:
        ret = []
        for _iter in range(self.iters):
            ret.append(method(self, _iter, *args, **kwargs))
        return ret
    return wrapper_repeat


def validate_file(method : Callable) -> bool:
    @functools.wraps(method)
    def wrapper_validate_file(self, _iter : int, *args, **kwargs) -> Any:
        if hasattr(self, 'file_names'):
            os.makedirs(os.path.dirname(self.file_names[_iter]),exist_ok=True)
            if pathlib.Path(self.file_names[_iter]).is_file():
                raise OSError(('Test data already exists with colliding name. '
                               'New data cannot be saved.'))
            return method(self, _iter, *args, **kwargs)
        raise FileNotFoundError(('Class does not have `file_name` attribute '
                                 'or `file_name` is not valid.'))
    return wrapper_validate_file