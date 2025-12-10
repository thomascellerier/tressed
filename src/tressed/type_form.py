__all__ = [
    "TypeForm",
    "type_form_repr",
]
TYPE_CHECKING = False
if TYPE_CHECKING:
    # TODO: Import from typing once PEP-747 is approved.
    # See https://peps.python.org/pep-0747/
    from typing_extensions import TypeForm

else:

    def __getattr__(name: str):
        match name:
            case "TypeForm":
                from typing_extensions import TypeForm

                return TypeForm
        raise AttributeError(f"Package '{__package__}' has no attribute '{name}'")


def type_form_repr(type_form: TypeForm) -> str:
    from tressed.predicates import get_args, is_union_type

    if name := getattr(type_form, "__name__", None):
        if type_params := getattr(type_form, "__type_params__", None):
            # C[T1=V1, .., Tn=?]
            params = []

            if args := get_args(type_form):
                num_args = len(args)
                for i, arg in enumerate(args):
                    params.append(
                        f"{type_form_repr(type_params[i])}={type_form_repr(arg)}"
                    )
            else:
                num_args = 0
            for type_param in type_params[num_args:]:
                params.append(f"{type_form_repr(type_param)}=?")
            return f"{name}[{', '.join(params)}]"

        if args := get_args(type_form):
            if len(args) > 1 and is_union_type(type_form):
                # T1 | .. | Tn
                return " | ".join(map(type_form_repr, args))
            # C[T1, .., Tn]
            return f"{name}[{', '.join(map(type_form_repr, args))}]"
        return name
    return repr(type_form)
