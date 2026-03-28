from pythonforandroid.recipe import PythonRecipe


class FlaskRecipe(PythonRecipe):
    """Override p4a's built-in Flask recipe to install 3.x.

    The built-in recipe pins Flask 2.0.3 which is incompatible with
    Werkzeug 3.x.

    Flask 3.x uses pyproject.toml (flit), not setup.py, so the default
    PythonRecipe.install_python_package (which runs ``setup.py install``)
    silently fails.  We override it to use ``pip install`` instead.
    """
    version = '3.1.1'
    url = 'https://github.com/pallets/flask/archive/{version}.zip'

    depends = ['setuptools', 'jinja2', 'werkzeug', 'markupsafe',
               'itsdangerous', 'click', 'blinker']

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


recipe = FlaskRecipe()
