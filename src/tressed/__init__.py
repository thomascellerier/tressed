TYPE_CHECKING = False
if TYPE_CHECKING:
    from tressed.dumper.dumper import Dumper
    from tressed.loader.loader import Loader
    from tressed.type_form import TypeForm
    from tressed.type_path import TypePath


__all__ = ["Loader", "Dumper", "load", "dump", "TypeForm", "TypePath"]


if TYPE_CHECKING:
    _default_loader = Loader()
    load = _default_loader.load

    _default_dumper = Dumper()
    dump = _default_dumper.dump

else:

    def __getattr__(name: str):
        match name:
            case "Loader":
                from tressed.loader.loader import Loader

                return Loader

            case "Dumper":
                from tressed.dumper.dumper import Dumper

                return Dumper

            case "load":
                if "_default_loader" not in globals():
                    global _default_loader
                    from tressed.loader.loader import Loader

                    _default_loader = Loader()
                return _default_loader.load

            case "dump":
                if "_default_dumper" not in globals():
                    global _default_dumper
                    from tressed.dumper.dumper import Dumper

                    _default_dumper = Dumper()
                return _default_dumper.dump

            case "TypeForm":
                from tressed.type_form import TypeForm

                return TypeForm

            case "TypePath":
                from tressed.type_path import TypePath

                return TypePath

            case _:
                raise AttributeError(
                    f"Package '{__package__}' has no attribute '{name}'"
                )
