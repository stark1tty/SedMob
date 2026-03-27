#!/usr/bin/env python3
"""Main entry point for Android APK - runs Flask in background thread with Kivy UI."""
import threading
import webbrowser
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from android.runnable import run_on_ui_thread
from jnius import autoclass

# Import the Flask app
from sedmob.app import create_app


class GneissworkApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flask_thread = None
        self.flask_app = None
        self.server_url = "http://127.0.0.1:5000"
        
    def build(self):
        # Start Flask in background thread
        self.start_flask_server()
        
        # Create simple UI with WebView
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        status_label = Label(
            text=f'Gneisswork Server Running\n{self.server_url}',
            size_hint=(1, 0.2)
        )
        
        # Button to open in default browser
        open_button = Button(
            text='Open Gneisswork',
            size_hint=(1, 0.2),
            on_press=self.open_browser
        )
        
        # Import WebView
        from kivy.uix.webview import WebView
        webview = WebView(url=self.server_url)
        
        layout.add_widget(status_label)
        layout.add_widget(open_button)
        layout.add_widget(webview)
        
        return layout
    
    def start_flask_server(self):
        """Start Flask server in a background thread."""
        def run_server():
            self.flask_app = create_app()
            self.flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        
        self.flask_thread = threading.Thread(target=run_server, daemon=True)
        self.flask_thread.start()
    
    @run_on_ui_thread
    def open_browser(self, instance):
        """Open the Flask app in the default browser."""
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        intent = Intent()
        intent.setAction(Intent.ACTION_VIEW)
        intent.setData(Uri.parse(self.server_url))
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        currentActivity = PythonActivity.mActivity
        currentActivity.startActivity(intent)


if __name__ == '__main__':
    GneissworkApp().run()
