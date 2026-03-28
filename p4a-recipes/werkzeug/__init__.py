from pythonforandroid.recipe import PythonRecipe


class WerkzeugRecipe(PythonRecipe):
    """Override p4a's built-in Werkzeug recipe to install 3.x.

    The built-in recipe pins an old 2.x version that is incompatible with
    Flask 3.x (missing ``url_quote`` in ``werkzeug.urls``).

    Werkzeug 3.x is pure Python but uses pyproject.toml (flit), which
    PythonRecipe cannot handle (it expects setup.py).  We bypass the
    source-based workflow entirely and pip-install the wheel from PyPI
    directly into the target site-packages.
    """
    version = '3.1.7'
    url = None
    depends = ['setuptools', 'markupsafe']
    site_packages_name = 'werkzeug'
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def should_build(self, arch):
        return True

    def build_arch(self, arch):
        import sh
        from os import makedirs
        from pythonforandroid.logger import shprint

        # Ensure build dir exists (p4a internals may reference it)
        makedirs(self.get_build_dir(arch.arch), exist_ok=True)

        hostpython = sh.Command(self.hostpython_location)
        install_dir = self.ctx.get_python_install_dir(arch.arch)

        shprint(hostpython, '-m', 'pip', 'install',
                f'werkzeug=={self.version}',
                '--no-deps',
                '--target', install_dir)

    def postbuild_arch(self, arch):
        pass


recipe = WerkzeugRecipe()
