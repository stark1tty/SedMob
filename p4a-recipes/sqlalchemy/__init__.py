import sys
from pythonforandroid.recipe import PythonRecipe


class SQLAlchemyRecipe(PythonRecipe):
    """Override p4a's built-in SQLAlchemy recipe to install 2.x.

    The built-in recipe pins SQLAlchemy 1.3.3 which is incompatible with
    Flask-SQLAlchemy 3.x (missing ``sqlalchemy.orm.DeclarativeMeta`` was
    removed in SQLAlchemy 2.0).

    SQLAlchemy 2.x has optional C extensions but works fine in pure Python
    mode.  We pip-install the wheel from PyPI which includes pre-built
    extensions for common platforms, and falls back to pure Python on
    Android where the host wheel's C extensions won't load.

    Note: p4a's hostpython does not have pip, so we use the system Python
    (sys.executable) which does.
    """
    version = '2.0.40'
    url = None
    depends = ['setuptools']
    site_packages_name = 'sqlalchemy'
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def should_build(self, arch):
        return True

    def build_arch(self, arch):
        import sh
        from os import makedirs
        from pythonforandroid.logger import shprint

        makedirs(self.get_build_dir(arch.arch), exist_ok=True)

        system_python = sh.Command(sys.executable)
        install_dir = self.ctx.get_python_install_dir(arch.arch)

        shprint(system_python, '-m', 'pip', 'install',
                f'sqlalchemy=={self.version}',
                'typing_extensions',
                '--no-deps',
                '--target', install_dir)

    def postbuild_arch(self, arch):
        pass


recipe = SQLAlchemyRecipe()
