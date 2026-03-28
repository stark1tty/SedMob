#!/usr/bin/env python3
"""Main entry point for Android APK - runs Flask in background thread with Android WebView."""
import logging
import os
import sys
import threading
import time
import traceback
import urllib.request

from kivy.app import App
from kivy.clock import Clock

from android.runnable import run_on_ui_thread
from jnius import autoclass, PythonJavaClass, java_method

PythonActivity = autoclass('org.kivy.android.PythonActivity')
AndroidWebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
WebChromeClient = autoclass('android.webkit.WebChromeClient')
Intent = autoclass('android.content.Intent')
Uri = autoclass('android.net.Uri')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('gneisswork')

# Request code for file chooser activity result
_FILE_CHOOSER_REQUEST = 1001
# Holds the pending ValueCallback from onShowFileChooser
_file_upload_callback = None


class GeoFileWebChromeClient(PythonJavaClass):
    """WebChromeClient that handles geolocation permissions and file uploads."""
    __javaclass__ = 'android/webkit/WebChromeClient'
    __javainterfaces__ = []

    @java_method('(Ljava/lang/String;Landroid/webkit/GeolocationPermissions$Callback;)V')
    def onGeolocationPermissionsShowPrompt(self, origin, callback):
        callback.invoke(origin, True, False)

    @java_method(
        '(Landroid/webkit/WebView;'
        'Landroid/webkit/ValueCallback;'
        'Landroid/webkit/WebChromeClient$FileChooserParams;)Z'
    )
    def onShowFileChooser(self, webview, value_callback, params):
        """Launch Android file picker when <input type="file"> is tapped."""
        global _file_upload_callback
        # Cancel any previous pending callback
        if _file_upload_callback is not None:
            _file_upload_callback.onReceiveValue(None)
        _file_upload_callback = value_callback
        try:
            intent = Intent(Intent.ACTION_GET_CONTENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType('*/*')
            # Allow both images and audio
            mime_types = ['image/*', 'audio/*']
            intent.putExtra(Intent.EXTRA_MIME_TYPES, mime_types)
            activity = PythonActivity.mActivity
            activity.startActivityForResult(intent, _FILE_CHOOSER_REQUEST)
        except Exception:
            log.error("File chooser launch failed:\n%s", traceback.format_exc())
            _file_upload_callback.onReceiveValue(None)
            _file_upload_callback = None
            return False
        return True


def _on_activity_result(request_code, result_code, intent):
    """Handle result from the file picker activity."""
    global _file_upload_callback
    if request_code != _FILE_CHOOSER_REQUEST:
        return
    if _file_upload_callback is None:
        return
    try:
        # RESULT_OK = -1 in Android
        if result_code == -1 and intent is not None:
            uri = intent.getData()
            if uri is not None:
                # Create a Uri[] array with one element
                UriArray = autoclass('java.lang.reflect.Array')
                uri_arr = UriArray.newInstance(Uri.getClass(uri), 1)
                UriArray.set(uri_arr, 0, uri)
                _file_upload_callback.onReceiveValue(uri_arr)
            else:
                _file_upload_callback.onReceiveValue(None)
        else:
            _file_upload_callback.onReceiveValue(None)
    except Exception:
        log.error("Activity result handling failed:\n%s", traceback.format_exc())
        try:
            _file_upload_callback.onReceiveValue(None)
        except Exception:
            pass
    finally:
        _file_upload_callback = None


def _request_location_permission():
    """Request ACCESS_FINE_LOCATION at runtime (required for Android 6+)."""
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION,
        ])
    except Exception:
        log.warning("Runtime permission request failed:\n%s", traceback.format_exc())


def _android_data_dir():
    """Return a writable directory for app data on Android."""
    activity = PythonActivity.mActivity
    ctx = activity.getApplicationContext()
    files_dir = ctx.getFilesDir().getAbsolutePath()
    data_dir = os.path.join(files_dir, 'gneisswork_data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


class GneissworkApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flask_thread = None
        self.flask_app = None
        self.server_url = "http://127.0.0.1:5000"
        self.flask_error = None
        self._poll_count = 0
        self._max_polls = 60  # 30 seconds timeout
        self._webview = None

    def build(self):
        _request_location_permission()
        # Register file chooser activity result handler
        activity = PythonActivity.mActivity
        activity.registerActivityResultListener(
            _ActivityResultListener()
        )
        self.start_flask_server()
        Clock.schedule_interval(self._check_server, 0.5)
        # Handle Android back button
        from kivy.core.window import Window
        Window.bind(on_keyboard=self._on_keyboard)
        from kivy.uix.label import Label
        return Label(text="Starting Gneisswork…")

    def _on_keyboard(self, window, key, *args):
        """Handle Android back button (key 27) — navigate WebView history."""
        if key == 27 and self._webview:
            Clock.schedule_once(lambda dt: self._webview_go_back(), 0)
            return True  # consume the event so Kivy doesn't exit
        return False

    @run_on_ui_thread
    def _webview_go_back(self):
        """Go back in WebView history if possible, otherwise let the app exit."""
        try:
            if self._webview and self._webview.canGoBack():
                self._webview.goBack()
            else:
                self.stop()
        except Exception:
            log.error("Back navigation failed:\n%s", traceback.format_exc())

    def start_flask_server(self):
        """Start Flask server in a background thread with Android-safe paths."""
        def run_server():
            try:
                data_dir = _android_data_dir()
                db_path = os.path.join(data_dir, 'gneisswork.db')
                upload_dir = os.path.join(data_dir, 'uploads')
                os.makedirs(upload_dir, exist_ok=True)

                log.info("Database path: %s", db_path)
                log.info("Upload dir: %s", upload_dir)

                from sedmob.app import create_app
                self.flask_app = create_app({
                    'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
                    'UPLOAD_FOLDER': upload_dir,
                })
                log.info("Flask app created, starting server…")
                self.flask_app.run(
                    host='127.0.0.1', port=5000,
                    debug=False, use_reloader=False,
                )
            except Exception:
                self.flask_error = traceback.format_exc()
                log.error("Flask server failed:\n%s", self.flask_error)

        self.flask_thread = threading.Thread(target=run_server, daemon=True)
        self.flask_thread.start()

    def _check_server(self, dt):
        """Poll until Flask responds, then swap to Android WebView."""
        self._poll_count += 1

        if self.flask_error:
            log.error("Flask thread died, stopping poll.")
            Clock.unschedule(self._check_server)
            self._show_error(self.flask_error)
            return

        if self._poll_count > self._max_polls:
            log.error("Timed out waiting for Flask server.")
            Clock.unschedule(self._check_server)
            self._show_error("Server failed to start within 30 seconds.")
            return

        try:
            urllib.request.urlopen(self.server_url, timeout=1)
        except Exception:
            return  # not ready yet

        Clock.unschedule(self._check_server)
        log.info("Flask server is up, showing WebView.")
        self._show_webview()

    @run_on_ui_thread
    def _show_webview(self):
        """Replace the Kivy surface with a native Android WebView."""
        try:
            activity = PythonActivity.mActivity
            webview = AndroidWebView(activity)
            settings = webview.getSettings()
            settings.setJavaScriptEnabled(True)
            settings.setDomStorageEnabled(True)
            settings.setDatabaseEnabled(True)
            settings.setAllowFileAccess(True)
            settings.setGeolocationEnabled(True)
            settings.setGeolocationDatabasePath(
                PythonActivity.mActivity.getApplicationContext()
                .getFilesDir().getAbsolutePath()
            )
            webview.setWebViewClient(WebViewClient())
            webview.setWebChromeClient(GeoWebChromeClient())
            activity.setContentView(webview)
            webview.loadUrl(self.server_url)
            self._webview = webview
        except Exception:
            log.error("WebView setup failed:\n%s", traceback.format_exc())

    @run_on_ui_thread
    def _show_error(self, message):
        """Show error in a basic WebView so the user sees something."""
        try:
            activity = PythonActivity.mActivity
            webview = AndroidWebView(activity)
            webview.getSettings().setJavaScriptEnabled(False)
            activity.setContentView(webview)
            html = (
                '<html><body style="padding:20px;font-family:sans-serif;">'
                '<h2>Gneisswork failed to start</h2>'
                f'<pre style="white-space:pre-wrap;">{message}</pre>'
                '</body></html>'
            )
            webview.loadData(html, 'text/html', 'utf-8')
        except Exception:
            log.error("Even error display failed:\n%s", traceback.format_exc())


if __name__ == '__main__':
    GneissworkApp().run()
