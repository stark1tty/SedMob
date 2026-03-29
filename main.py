#!/usr/bin/env python3
"""Main entry point for Android APK - runs Flask in background thread with Android WebView.

All pyjnius imports and autoclass lookups are deferred into methods so that
any failure is caught and displayed to the user instead of silently crashing.
"""
import logging
import os
import sys
import threading
import traceback
import urllib.request

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('gneisswork')

# ---------------------------------------------------------------------------
# Crash-log helper — writes to a file the user can retrieve via adb or share
# ---------------------------------------------------------------------------
_CRASH_LOG = None  # set once we know the writable dir


def _write_crash_log(msg):
    """Append *msg* to a persistent crash log file."""
    global _CRASH_LOG
    try:
        if _CRASH_LOG is None:
            # Best-effort: try the p4a files dir
            from jnius import autoclass
            ctx = autoclass('org.kivy.android.PythonActivity').mActivity.getApplicationContext()
            _CRASH_LOG = os.path.join(ctx.getFilesDir().getAbsolutePath(), 'crash.log')
        with open(_CRASH_LOG, 'a') as f:
            f.write(msg + '\n---\n')
    except Exception:
        pass  # truly nothing we can do


# ---------------------------------------------------------------------------
# Lazy holders — populated by _init_java()
# ---------------------------------------------------------------------------
PythonActivity = None
AndroidWebView = None
WebViewClient = None
WebChromeClient = None
Intent = None
run_on_ui_thread = None
PythonJavaClass = None
java_method = None

# Request code for file chooser activity result
_FILE_CHOOSER_REQUEST = 1001
_file_upload_callback = None


def _init_java():
    """Resolve all Java classes via pyjnius.  Called once from build()."""
    global PythonActivity, AndroidWebView, WebViewClient, WebChromeClient
    global Intent, run_on_ui_thread, PythonJavaClass, java_method

    from android.runnable import run_on_ui_thread as _rout
    from jnius import autoclass as _ac, PythonJavaClass as _pjc, java_method as _jm

    run_on_ui_thread = _rout
    PythonJavaClass = _pjc
    java_method = _jm

    PythonActivity = _ac('org.kivy.android.PythonActivity')
    AndroidWebView = _ac('android.webkit.WebView')
    WebViewClient  = _ac('android.webkit.WebViewClient')
    WebChromeClient = _ac('android.webkit.WebChromeClient')
    Intent = _ac('android.content.Intent')


# ---------------------------------------------------------------------------
# PythonJavaClass helpers — defined as functions that return classes so they
# are only created after _init_java() populates the globals.
# ---------------------------------------------------------------------------

def _make_chrome_client_class():
    """Return a WebChromeClient subclass that handles geo + file uploads."""

    class GeoFileWebChromeClient(PythonJavaClass):
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
            global _file_upload_callback
            if _file_upload_callback is not None:
                _file_upload_callback.onReceiveValue(None)
            _file_upload_callback = value_callback
            try:
                intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                intent.setType('*/*')
                intent.putExtra(Intent.EXTRA_MIME_TYPES, ['image/*', 'audio/*'])
                PythonActivity.mActivity.startActivityForResult(intent, _FILE_CHOOSER_REQUEST)
            except Exception:
                log.error("File chooser failed:\n%s", traceback.format_exc())
                _file_upload_callback.onReceiveValue(None)
                _file_upload_callback = None
                return False
            return True

    return GeoFileWebChromeClient


def _make_activity_listener_class():
    """Return an ActivityResultListener implementation."""

    class _ActivityResultListener(PythonJavaClass):
        __javaclass__ = 'org/kivy/android/PythonActivity$ActivityResultListener'
        __javainterfaces__ = ['org/kivy/android/PythonActivity$ActivityResultListener']

        @java_method('(IILandroid/content/Intent;)V')
        def onActivityResult(self, request_code, result_code, intent):
            _on_activity_result(request_code, result_code, intent)

    return _ActivityResultListener


def _on_activity_result(request_code, result_code, intent):
    global _file_upload_callback
    if request_code != _FILE_CHOOSER_REQUEST or _file_upload_callback is None:
        return
    try:
        if result_code == -1 and intent is not None:
            from jnius import autoclass
            FCP = autoclass('android.webkit.WebChromeClient$FileChooserParams')
            _file_upload_callback.onReceiveValue(FCP.parseResult(result_code, intent))
        else:
            _file_upload_callback.onReceiveValue(None)
    except Exception:
        log.error("Activity result failed:\n%s", traceback.format_exc())
        try:
            _file_upload_callback.onReceiveValue(None)
        except Exception:
            pass
    finally:
        _file_upload_callback = None


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------

def _request_location_permission():
    try:
        from android.permissions import request_permissions, Permission

        def _on_result(permissions, grant_results):
            log.info("Permission result: %s -> %s", permissions, grant_results)

        request_permissions([
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION,
        ], _on_result)
    except Exception:
        log.warning("Permission request failed:\n%s", traceback.format_exc())


# ---------------------------------------------------------------------------
# Android data directory
# ---------------------------------------------------------------------------

def _android_data_dir():
    activity = PythonActivity.mActivity
    files_dir = activity.getApplicationContext().getFilesDir().getAbsolutePath()
    data_dir = os.path.join(files_dir, 'gneisswork_data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


# ---------------------------------------------------------------------------
# Kivy App
# ---------------------------------------------------------------------------
from kivy.app import App
from kivy.clock import Clock


class GneissworkApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flask_thread = None
        self.flask_app = None
        self.server_url = "http://127.0.0.1:5000"
        self.flask_error = None
        self._poll_count = 0
        self._max_polls = 60  # 30s timeout
        self._webview = None
        # Strong refs to prevent pyjnius GC
        self._activity_listener = None
        self._chrome_client = None
        self._ChromeClientClass = None

    def build(self):
        try:
            log.info("build(): initialising Java classes…")
            _init_java()
            log.info("build(): Java classes ready")

            # Build the PythonJavaClass subclasses now that pyjnius is ready
            self._ChromeClientClass = _make_chrome_client_class()
            ListenerClass = _make_activity_listener_class()

            self._activity_listener = ListenerClass()
            PythonActivity.mActivity.registerActivityResultListener(
                self._activity_listener
            )
            log.info("build(): activity listener registered")
        except Exception:
            msg = traceback.format_exc()
            log.error("build() init failed:\n%s", msg)
            _write_crash_log("build() init failed:\n" + msg)
            # Fall through — Flask + error display may still work

        self.start_flask_server()
        Clock.schedule_interval(self._check_server, 0.5)

        from kivy.core.window import Window
        Window.bind(on_keyboard=self._on_keyboard)
        from kivy.uix.label import Label
        return Label(text="Starting Gneisswork…")

    def _on_keyboard(self, window, key, *args):
        if key == 27 and self._webview:
            Clock.schedule_once(lambda dt: self._webview_go_back(), 0)
            return True
        return False

    def _webview_go_back_impl(self):
        try:
            if self._webview and self._webview.canGoBack():
                self._webview.goBack()
            else:
                self.stop()
        except Exception:
            log.error("Back nav failed:\n%s", traceback.format_exc())

    def _webview_go_back(self):
        if run_on_ui_thread:
            run_on_ui_thread(self._webview_go_back_impl)()
        else:
            self._webview_go_back_impl()

    def start_flask_server(self):
        def run_server():
            try:
                data_dir = _android_data_dir()
                db_path = os.path.join(data_dir, 'gneisswork.db')
                upload_dir = os.path.join(data_dir, 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                log.info("DB: %s  Uploads: %s", db_path, upload_dir)

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
                log.error("Flask failed:\n%s", self.flask_error)
                _write_crash_log("Flask failed:\n" + self.flask_error)

        self.flask_thread = threading.Thread(target=run_server, daemon=True)
        self.flask_thread.start()

    def _check_server(self, dt):
        self._poll_count += 1

        if self.flask_error:
            Clock.unschedule(self._check_server)
            self._show_error(self.flask_error)
            return

        if self._poll_count > self._max_polls:
            Clock.unschedule(self._check_server)
            self._show_error("Server failed to start within 30 seconds.")
            return

        try:
            urllib.request.urlopen(self.server_url, timeout=1)
        except Exception:
            return

        Clock.unschedule(self._check_server)
        log.info("Flask is up — showing WebView")
        self._show_webview_safe()

    def _show_webview_safe(self):
        """Schedule WebView creation on the UI thread."""
        if run_on_ui_thread:
            run_on_ui_thread(self._show_webview_impl)()
        else:
            self._show_webview_impl()

    def _show_webview_impl(self):
        try:
            activity = PythonActivity.mActivity
            webview = AndroidWebView(activity)
            ws = webview.getSettings()
            ws.setJavaScriptEnabled(True)
            ws.setDomStorageEnabled(True)
            ws.setDatabaseEnabled(True)
            ws.setAllowFileAccess(True)
            ws.setGeolocationEnabled(True)
            ws.setGeolocationDatabasePath(
                activity.getApplicationContext()
                .getFilesDir().getAbsolutePath()
            )
            webview.setWebViewClient(WebViewClient())
            if self._ChromeClientClass:
                self._chrome_client = self._ChromeClientClass()
                webview.setWebChromeClient(self._chrome_client)
            activity.setContentView(webview)
            webview.loadUrl(self.server_url)
            self._webview = webview
            log.info("WebView displayed")
            Clock.schedule_once(lambda dt: _request_location_permission(), 1.0)
        except Exception:
            msg = traceback.format_exc()
            log.error("WebView setup failed:\n%s", msg)
            _write_crash_log("WebView setup failed:\n" + msg)

    def _show_error(self, message):
        _write_crash_log("Showing error to user:\n" + message)
        if run_on_ui_thread:
            run_on_ui_thread(lambda: self._show_error_impl(message))()
        else:
            self._show_error_impl(message)

    def _show_error_impl(self, message):
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
            log.error("Error display failed:\n%s", traceback.format_exc())


# ---------------------------------------------------------------------------
# Entry point — wrapped so even top-level crashes are visible
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        GneissworkApp().run()
    except Exception:
        msg = traceback.format_exc()
        log.error("FATAL top-level crash:\n%s", msg)
        _write_crash_log("FATAL:\n" + msg)
        # Last-resort: try to show error via basic Android TextView
        try:
            from jnius import autoclass
            act = autoclass('org.kivy.android.PythonActivity').mActivity
            TextView = autoclass('android.widget.TextView')
            tv = TextView(act)
            tv.setText("Gneisswork crashed:\n\n" + msg)
            tv.setPadding(40, 40, 40, 40)
            act.setContentView(tv)
        except Exception:
            pass
