#!/usr/bin/env python3
"""Main entry point for Android APK - runs Flask in background thread with Android WebView."""
import threading
import time
import urllib.request

from kivy.app import App
from kivy.clock import Clock

from android.runnable import run_on_ui_thread
from jnius import autoclass

from sedmob.app import create_app

PythonActivity = autoclass('org.kivy.android.PythonActivity')
AndroidWebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
WebSettings = autoclass('android.webkit.WebSettings')
Intent = autoclass('android.content.Intent')
Uri = autoclass('android.net.Uri')


class GneissworkApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flask_thread = None
        self.flask_app = None
        self.server_url = "http://127.0.0.1:5000"

    def build(self):
        self.start_flask_server()
        # Poll until Flask is ready, then show WebView
        Clock.schedule_interval(self._check_server, 0.5)
        # Return a minimal Kivy widget (replaced by WebView once server is up)
        from kivy.uix.label import Label
        return Label(text="Starting Gneisswork…")

    def start_flask_server(self):
        """Start Flask server in a background thread."""
        def run_server():
            self.flask_app = create_app()
            self.flask_app.run(
                host='127.0.0.1', port=5000,
                debug=False, use_reloader=False,
            )
        self.flask_thread = threading.Thread(target=run_server, daemon=True)
        self.flask_thread.start()

    def _check_server(self, dt):
        """Poll until Flask responds, then swap to Android WebView."""
        try:
            urllib.request.urlopen(self.server_url, timeout=1)
        except Exception:
            return  # not ready yet, keep polling
        # Server is up — stop polling and show WebView
        Clock.unschedule(self._check_server)
        self._show_webview()

    @run_on_ui_thread
    def _show_webview(self):
        """Replace the Kivy surface with a native Android WebView."""
        activity = PythonActivity.mActivity
        webview = AndroidWebView(activity)
        settings = webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        settings.setDatabaseEnabled(True)
        webview.setWebViewClient(WebViewClient())
        activity.setContentView(webview)
        webview.loadUrl(self.server_url)


if __name__ == '__main__':
    GneissworkApp().run()
