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
from jnius import autoclass

PythonActivity = autoclass('org.kivy.android.PythonActivity')
AndroidWebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
WebSettings = autoclass('android.webkit.WebSettings')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('gneisswork')


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

    def build(self):
        self.start_flask_server()
        Clock.schedule_interval(self._check_server, 0.5)
        from kivy.uix.label import Label
        return Label(text="Starting Gneisswork…")

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
            webview.setWebViewClient(WebViewClient())
            activity.setContentView(webview)
            webview.loadUrl(self.server_url)
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
