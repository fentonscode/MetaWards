
__all__ = ["mix_custom",
           "mixer_needs_setup",
           "build_custom_mixer"]


def mixer_needs_setup(mixer):
    """Return whether or not the passed mixer function has
       a "setup" argument, and thus needs to be setup before
       it can be used
    """
    import inspect
    return "setup" in inspect.signature(mixer).parameters


def build_custom_mixer(custom_function, parent_name="__main__"):
    """Build and return a custom mixer from the passed
       function. This will wrap 'extract_mixer' around
       the function to double-check that the custom
       function is doing everything correctly

       Parameters
       ----------
       custom_function
         This can either be a function, which will be wrapped and
         returned, or it can be a string. If it is a string then
         we will attempt to locate or import the function associated
         with that string. The search order is;

         1. Is this 'metawards.mixers.custom_function'?
         2. Is this 'custom_function' that is already imported'?
         3. Is this a file name in the current path, if yes then
            find the function in that file (either the first function
            called 'extractXXX' or the specified function if
            custom_function is in the form module::function)

        parent_name: str
          This should be the __name__ of the calling function, e.g.
          call this function as build_custom_mover(func, __name__)

        Returns
        -------
        extractor
          The wrapped mixer that is suitable for using in the move
          function.
    """
    if isinstance(custom_function, str):
        print(f"Importing a custom mixer from {custom_function}")

        # we need to find the function
        import metawards.mixers

        # is it metawards.mixers.{custom_function}
        try:
            func = getattr(metawards.mixers, custom_function)
            return build_custom_mixer(func)
        except Exception:
            pass

        # do we have the function in the current namespace?
        import sys
        try:
            func = getattr(sys.modules[__name__], custom_function)
            return build_custom_mixer(func)
        except Exception:
            pass

        # how about the __name__ namespace of the caller
        try:
            func = getattr(sys.modules[parent_name], custom_function)
            return build_custom_mixer(func)
        except Exception:
            pass

        # how about the __main__ namespace (e.g. if this was loaded
        # in a script)
        try:
            func = getattr(sys.modules["__main__"], custom_function)
            return build_custom_mixer(func)
        except Exception:
            pass

        # can we import this function as a file - need to check that
        # the user hasn't written this as module::function
        if custom_function.find("::") != -1:
            parts = custom_function.split("::")
            func_name = parts[-1]
            func_module = "::".join(parts[0:-1])
        else:
            func_name = None
            func_module = custom_function

        from ..utils._import_module import import_module

        module = import_module(func_module)

        if module is None:
            # we cannot find the extractor
            print(f"Cannot find the mixer '{custom_function}'."
                  f"Please make sure this is spelled correctly and "
                  f"any python modules/files needed are in the "
                  f"PYTHONPATH or current directory")
            raise ImportError(f"Could not import the mover "
                              f"'{custom_function}'")

        if func_name is None:
            # find the first function that starts with 'mix'
            import inspect
            for name, value in inspect.getmembers(module):
                if name.startswith("mix"):
                    if hasattr(value, "__call__"):
                        # this is a function
                        return build_custom_mixer(getattr(module, name))

            print(f"Could not find any function in the module "
                  f"{custom_function} that has a name that starts "
                  f"with 'mix'. Please manually specify the "
                  f"name using the '{custom_function}::your_function syntax")

            raise ImportError(f"Could not import the mixer "
                              f"{custom_function}")

        else:
            if hasattr(module, func_name):
                return build_custom_mixer(getattr(module, func_name))

            print(f"Could not find the function {func_name} in the "
                  f"module {func_module}. Check that the spelling "
                  f"is correct and that the right version of the module "
                  f"is being loaded.")
            raise ImportError(f"Could not import the mixer "
                              f"{custom_function}")

    if not hasattr(custom_function, "__call__"):
        print(f"Cannot build a mixer for {custom_function} "
              f"as it is missing a __call__ function, i.e. it is "
              f"not a function.")
        raise ValueError(f"You can only build custom mixers for "
                         f"actual functions... {custom_function}")

    print(f"Building a custom mixer for {custom_function}")

    return lambda **kwargs: mix_custom(custom_function=custom_function,
                                       **kwargs)


def mix_custom(custom_function, setup=False, **kwargs):
    """This returns the default list of 'merge_XXX' functions that
       are called in sequence to merge data from the outbreak,
       e.g. fois, from across multiple demographics and to
       merge that back to the overall population

       This mixer provides a custom mixer that uses
       'custom_function' passed from the user. This
       mixer makes sure that 'custom_function' does everything
       it should

       Parameters
       ----------
       custom_function
         A custom user-supplied function that returns the
         functions that the user would like to be called for
         each step.
       setup: bool
         Whether or not to return the functions used to setup the
         space and input for the merge_XXX functions returned by
         this mixer. This is called once at the start of a run
         to return the functions that must be called to setup the
         movers. Note that most mixers shouldn't need any setup.

       Returns
       -------
       funcs: List[function]
         The list of functions that ```merge``` will call in sequence
    """

    from ._merge_core import merge_core

    if setup:
        # Return the functions needed to initialise this extractor
        kwargs["setup"] = setup
        core_funcs = merge_core(**kwargs)

        if mixer_needs_setup(custom_function):
            custom_funcs = custom_function(**kwargs)
        else:
            custom_funcs = None

    else:
        core_funcs = merge_core(**kwargs)
        custom_funcs = custom_function(**kwargs)

    # make sure that the core functions are called, and that
    # their call is before the custom function (unless the user
    # has moved them, which we hope was for a good reason!)
    if core_funcs is None or len(core_funcs) == 0:
        if custom_funcs is None:
            return []
        else:
            return custom_funcs

    elif custom_funcs is None or len(custom_funcs) == 0:
        return core_funcs

    else:
        for i in range(len(core_funcs)-1, -1, -1):
            # move backwards so that the first custom function
            # is prepended last
            if core_funcs[i] not in custom_funcs:
                custom_funcs.insert(0, core_funcs[i])

        return custom_funcs