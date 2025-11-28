TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any

    from gluetypes.loader.types import LoaderProtocol, TypePath

__all__ = ["SpecializingLoader"]


class SpecializingLoader:
    def __init__(self, loader, specializer) -> None:
        self._loader = loader
        self._specialized_loaders: dict = {}
        self._specializer = specializer
        self._threshold: int = 3

    def __call__[T](
        self,
        value: Any,
        type_form: type[T],
        type_path: TypePath,
        loader: LoaderProtocol,
    ) -> T:
        key = (type_form, type_path)
        specialized_loader = self._specialized_loaders.get(key)
        if type(specialized_loader) is type(None) or type(specialized_loader) is int:
            if type(specialized_loader) is int and specialized_loader > 0:
                count = specialized_loader + 1
            else:
                count = 1
            self._specialized_loaders[key] = count
            specialized_loader = None

            # Specialize!
            if count > self._threshold:
                specializer_fn_code = self._specializer(*key)
                if specializer_fn_code is None:
                    # zero means we can't specialize this
                    self._specialized_loaders[key] = 0
                else:
                    globals_ = {}
                    locals_ = {}

                    exec(specializer_fn_code, globals_, locals_)

                    specialized_loader = locals_["__specialized_fn"]
                    self._specialized_loaders[key] = specialized_loader

        if specialized_loader is None:
            return self._loader(value, type_form, type_path, loader)
        else:
            return specialized_loader(value, loader)
