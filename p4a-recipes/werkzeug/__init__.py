from pythonforandroid.recipe import PythonRecipe


class WerkzeugRecipe(PythonRecipe):
    """Override p4a's built-in Werkzeug recipe to install 3.x.

    The built-in recipe pins an old 2.x version that is incompatible with
    Flask 3.x (missing ``url_quote`` in ``werkzeug.urls``).

    Werkzeug 3.x uses pyproject.toml (flit), not setup.py, so the default
    PythonRecipe.install_python_package (which runs ``setup.py install``)
    silently fails.  We override it to use ``pip install`` instead.
    """
    version = '3.1.7'
    url = 'https://github.com/pallets/werkzeug/archive/{version}.zip'

    depends = ['setuptools', 'markupsafe']

    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def install_python_package(self, arch, name=None, env=None,
                               is_dir=True):
        """Use pip to install from source (handles pyproject.toml)."""
        from pythonforandroid.logger import shprint
        import sh

        hostpython = sh.Command(self.hostpython_location)
        env = env or self.get_recipe_env(arch)
        install_dir = self.ctx.get_python_install_dir(arch.arch)
        build_dir = self.get_build_dir(arch.arch)

        shprint(hostpython, '-m', 'pip', 'install', '.',
                '--no-deps', '--no-build-isolation',
                '--target', install_dir,
                _cwd=build_dir, _env=env)


recipe = WerkzeugRecipe()
