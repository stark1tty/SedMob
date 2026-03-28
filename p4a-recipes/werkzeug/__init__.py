from pythonforandroid.recipe import PythonRecipe


class WerkzeugRecipe(PythonRecipe):
    version = '3.1.7'
    url = 'https://github.com/pallets/werkzeug/archive/{version}.zip'

    depends = ['setuptools']

    python_depends = ['markupsafe']

    call_hostpython_via_targetpython = False
    install_in_hostpython = False


recipe = WerkzeugRecipe()
