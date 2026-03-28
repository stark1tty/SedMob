from pythonforandroid.recipe import PythonRecipe


class WerkzeugRecipe(PythonRecipe):
    """Override p4a's built-in Werkzeug recipe to install 3.x from PyPI.

    The built-in recipe pins an old 2.x version that is incompatible with
    Flask 3.x (missing ``url_quote`` in ``werkzeug.urls``).  Since Werkzeug
    is pure Python we skip the source download entirely and pip-install the
    wheel straight from PyPI.
    """
    version = '3.1.7'
    url = None                              # nothing to download
    depends = ['python3']
    site_packages_name = 'werkzeug'
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
            f'werkzeug=={self.version}',
            '--no-deps',
            '--compile',
            '--target', self.ctx.get_python_install_dir(arch.arch),
            _env=env,
        )


recipe = WerkzeugRecipe()
