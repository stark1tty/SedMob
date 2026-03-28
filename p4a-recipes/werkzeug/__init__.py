from pythonforandroid.recipe import PythonRecipe


class WerkzeugRecipe(PythonRecipe):
    """Override p4a's built-in Werkzeug recipe to install 3.x.

    The built-in recipe pins an old 2.x version that is incompatible with
    Flask 3.x (missing ``url_quote`` in ``werkzeug.urls``).  We pull the
    source from GitHub and let PythonRecipe handle the standard install.
    """
    version = '3.1.7'
    url = 'https://github.com/pallets/werkzeug/archive/{version}.zip'

    depends = ['setuptools', 'markupsafe']

    call_hostpython_via_targetpython = False
    install_in_hostpython = False


recipe = WerkzeugRecipe()
