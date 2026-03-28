from pythonforandroid.recipe import PythonRecipe


class FlaskRecipe(PythonRecipe):
    """Override p4a's built-in Flask recipe to install 3.x.

    The built-in recipe pins Flask 2.0.3 which is incompatible with
    Werkzeug 3.x.  We pull the source from GitHub and let PythonRecipe
    handle the standard install.
    """
    version = '3.1.1'
    url = 'https://github.com/pallets/flask/archive/{version}.zip'

    depends = ['setuptools', 'jinja2', 'werkzeug', 'markupsafe',
               'itsdangerous', 'click', 'blinker']

    call_hostpython_via_targetpython = False
    install_in_hostpython = False


recipe = FlaskRecipe()
