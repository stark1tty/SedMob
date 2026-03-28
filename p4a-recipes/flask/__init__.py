from pythonforandroid.recipe import PythonRecipe


class FlaskRecipe(PythonRecipe):
    """Override p4a's built-in Flask recipe to install 3.x from PyPI.

    The built-in recipe pins Flask 2.0.3 which is incompatible with
    Werkzeug 3.x.  Since Flask is pure Python we skip the source download
    and pip-install the wheel straight from PyPI.
    """
    version = '3.1.1'
    url = None                              # nothing to download
    depends = ['python3']
    python_depends = [
        'jinja2', 'werkzeug', 'markupsafe', 'itsdangerous', 'click', 'blinker',
    ]
    site_packages_name = 'flask'
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def build_arch(self, arch):
        from os import makedirs
        self.install_hostpython_prerequisites()
        # Ensure the build dir exists (p4a's env helper may reference it)
        makedirs(self.get_build_dir(arch.arch), exist_ok=True)
        env = self.get_recipe_env(arch)
        from pythonforandroid.logger import shprint
        shprint(
            self._host_recipe.pip,
            'install',
            f'flask=={self.version}',
            '--no-deps',
            '--compile',
            '--target', self.ctx.get_python_install_dir(arch.arch),
            _env=env,
        )


recipe = FlaskRecipe()
