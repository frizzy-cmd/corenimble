import sys, os, json, urllib.request, ctypes, time, psutil, platform, subprocess
from PyQt6.QtCore import QEvent, QUrl, Qt, QTimer, QStandardPaths, qVersion
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QLineEdit, QPushButton, QTabWidget,
    QLabel, QToolButton, QMenu, QSystemTrayIcon, QStyle, 
    QProgressBar, QComboBox, QMessageBox, QScrollArea,
    QCheckBox, QSpinBox
)
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence, QDesktopServices
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings, qWebEngineChromiumVersion
from PyQt6.QtGui import QFontDatabase

VERSION = "1.0.0-release"

# Core Nimble Browser - v1.0.1 Release
# Developed by Frizzy (2026)
# Licensed under GNU GPL v3.0
# "Nimble" and the custom scheme nimble:// are property of the developer.

bundle_dir = None
_settings_dir = None
CONFIG_FILE = None

DEFAULT_SETTINGS = {
    "homepage": "https://google.com",
    "user_agent": "default",
    "custom_ua": "",
    "software_rendering": False,
    "disable_sandbox": True,
    "extra_flags": "",
    "ram_limit_mb": 2048,
    "tab_suspend_enabled": True,
    "tab_suspend_min": 15,
    "panic_enabled": True,
    "history": [],
    "bookmarks": [],
    "downloads": []
}

def load_settings():
    if not os.path.exists(CONFIG_FILE): return DEFAULT_SETTINGS.copy()
    with open(CONFIG_FILE, "r") as f: 
        try:
            data = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data: data[k] = v
            return data
        except: return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(CONFIG_FILE, "w") as f: json.dump(settings, f, indent=4)

UA_PRESETS = {
    "default": "",
    "chrome_windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "firefox_linux": "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "iphone": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "custom": "manual"
}

class BrosterPage(QWebEnginePage):
    def __init__(self, profile, parent=None, browser_main=None):
        super().__init__(profile, parent)
        self.browser_main = browser_main

    def createWindow(self, _type): 
        return self.browser_main.add_new_tab(QUrl("")).page()

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if url.scheme() not in ["http", "https", "file", "nimble", "about", "data"]:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)

STYLESHEET = """
* { 
    font-family: 'Inter', 'Segoe UI', sans-serif; 
}

QMainWindow, QWidget#main_bg, QMessageBox, QScrollArea { 
    background-color: #202124; 
    color: #f1f3f4; 
}

QTabWidget::pane { border: none; background-color: #202124; }

QTabBar::tab { 
    background: #202124; color: #9aa0a6; padding:8px 15px; 
    border-top-left-radius:8px; border-top-right-radius:8px; 
    min-width:100px; margin-right: 2px; 
}

QTabBar::tab:selected { 
    background: #323639; color: white; border-bottom: 2px solid #8ab4f8; 
}

#nav_container { background-color:#202124; border-top:1px solid #3c4043; padding:5px; }

QLineEdit, QComboBox, QSpinBox { 
    background:#171717; color:#f1f3f4; border:1px solid #3c4043; 
    border-radius:12px; padding:6px 15px; 
}

#status_label, #zoom_label { 
    font-family: 'Fira Code', 'Consolas', monospace; 
    font-size: 11px;
}

QCheckBox { color: #f1f3f4; spacing: 5px; }

QPushButton, QToolButton { 
    background:#3c4043; color:#e8eaed; font-size:14px; 
    padding:5px 10px; border-radius:10px; font-weight: bold; 
}

QPushButton:hover, QToolButton:hover { background:#4f5256; }

QLabel { color: #f1f3f4; }

QProgressBar { 
    max-height: 14px; border: 1px solid #3c4043; background: #171717; 
    border-radius: 7px; text-align: center; color: white; 
    font-size: 10px; font-weight: bold; 
}

QProgressBar::chunk { background-color: #8ab4f8; border-radius: 7px; }
"""

class CoreNimble(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.history_items = self.settings.get("history", [])
        self.bookmarks = self.settings.get("bookmarks", [])
        self.downloads = self.settings.get("downloads", [])
        self.active_downloads = []
        
        icon_path = os.path.join(bundle_dir, "iconn.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle(f"Nimble {VERSION}")
        self.setStyleSheet(STYLESHEET)
        
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon))
        self.tray.show()

        self.profile = QWebEngineProfile("CoreNimbleUser", self)
        self.profile.setPersistentStoragePath(os.path.join(_settings_dir, "nimble_data"))
        self.ghost_profile = QWebEngineProfile(self)
        
        self.apply_user_agent()
        self.profile.downloadRequested.connect(self.handle_download)
        self.ghost_profile.downloadRequested.connect(self.handle_download)
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True); self.tabs.setMovable(True)
        
        
 #       def tab_mouse_press(event):
  #          if event.button() == Qt.MouseButton.MiddleButton:
  #              index = self.tabs.tabBar().tabAt(event.pos())
    #            if index != -1:
    #                self.close_tab(index)

     #       QTabBar.mousePressEvent(self.tabs.tabBar(), event)

     #   self.tabs.tabBar().mousePressEvent = tab_mouse_press

        self.tabs.tabBar().installEventFilter(self)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.handle_tab_change)

        self.setup_ui()
        self.setup_shortcuts()
        
        self.ui_timer = QTimer(); self.ui_timer.timeout.connect(self.refresh_downloads_ui)
        self.sus_timer = QTimer(); self.sus_timer.timeout.connect(self.check_suspension); self.sus_timer.start(30000)

        self.add_new_tab(QUrl(self.settings.get("homepage", "https://google.com")))

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, lambda: self.add_new_tab(QUrl(self.settings.get("homepage"))))
        QShortcut(QKeySequence("Ctrl+Shift+D"), self, self.duplicate_tab)
        QShortcut(QKeySequence("Ctrl+Shift+P"), self, self.panic_button)
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self.close_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+L"), self, self.url_bar.setFocus)
        QShortcut(QKeySequence("Ctrl+Shift+M"), self, self.toggle_mute)
        QShortcut(QKeySequence("Ctrl+="), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.zoom_reset)

    def closeEvent(self, event):
        for i in range(self.tabs.count()):
            self.tabs.widget(i).deleteLater()
        event.accept()

    def save_nimble_data(self):
        self.settings["history"] = self.history_items
        self.settings["bookmarks"] = self.bookmarks
        self.settings["downloads"] = self.downloads

        try:
            save_settings(self.settings)
            print(f"Nimble: Data saved to {CONFIG_FILE}")
        except Exception as e:
            print(f"Nimble: Save failed: {e}")

    def add_bookmark(self):
        u = self.tabs.currentWidget().url().toString()
        if u and u not in self.bookmarks: 
            self.bookmarks.append(u)
            self.save_nimble_data()

    def remove_bookmark(self, url):
        if url in self.bookmarks: 
            self.bookmarks.remove(url)
            self.save_nimble_data()

    def zoom_in(self):
        w = self.tabs.currentWidget()
        if isinstance(w, QWebEngineView):
            w.setZoomFactor(w.zoomFactor() + 0.1)
            self.update_zoom_label(w.zoomFactor())

    def zoom_out(self):
        w = self.tabs.currentWidget()
        if isinstance(w, QWebEngineView):
            w.setZoomFactor(max(0.2, w.zoomFactor() - 0.1))
            self.update_zoom_label(w.zoomFactor())

    def zoom_reset(self):
        w = self.tabs.currentWidget()
        if isinstance(w, QWebEngineView):
            w.setZoomFactor(1.0)
            self.update_zoom_label(1.0)

    def update_zoom_label(self, factor):
        #if hasattr(self, 'zoom_label'):
            self.zoom_label.setText(f"Zoom: {int(factor * 100)}%")

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def make_zoom_scroll(self, browser):
        def scroll_logic(event):
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                delta = event.angleDelta().y()
                step = 0.15 if delta > 0 else -0.15
                new_zoom = max(0.2, min(5.0, browser.zoomFactor() + step))
                
                browser.setZoomFactor(new_zoom)
                self.update_zoom_label(new_zoom)
                self.zoom_label.repaint() 
                event.accept()
            else:
                type(browser).wheelEvent(browser, event)
        return scroll_logic

    def duplicate_tab(self):
        curr = self.tabs.currentWidget()
        if isinstance(curr, QWebEngineView): self.add_new_tab(curr.url())

    def eventFilter(self, obj, event):
        try:
            if not self.tabs or event is None:
                return False

            if obj == self.tabs.tabBar() and event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.MiddleButton:
                    index = self.tabs.tabBar().tabAt(event.pos())
                    if index != -1:
                        self.close_tab(index)
                        return True
        except (RuntimeError, AttributeError):
            return False
            
        return super().eventFilter(obj, event)

    def handle_middle_click(self, index):
        if QApplication.mouseButtons() == Qt.MouseButton.MiddleButton:
            self.close_tab(index)

    def panic_button(self):
        if not self.settings.get("panic_enabled", True): return
        while self.tabs.count() > 0:
            w = self.tabs.widget(0)
            self.tabs.removeTab(0)
            w.deleteLater()
        self.add_new_tab(QUrl("https://google.com"))

    def toggle_mute(self):
        browser = self.tabs.currentWidget()
        if isinstance(browser, QWebEngineView):
            is_muted = not browser.page().isAudioMuted()
            browser.page().setAudioMuted(is_muted)
            
            idx = self.tabs.currentIndex()
            current_text = self.tabs.tabText(idx)
            
            if is_muted:
                if "🔇" not in current_text:
                    self.tabs.setTabText(idx, f"🔇 {current_text}")
            else:
                self.tabs.setTabText(idx, current_text.replace("🔇 ", ""))

    def check_for_updates(self):
        import urllib.request
        url = "https://raw.githubusercontent.com/frizzy-cmd/corenimble/refs/heads/main/version.txt"
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                latest_version = response.read().decode('utf-8').strip()
                
            if latest_version != VERSION:
                msg = f"Update available!\n\nCurrent: {VERSION}\nLatest: {latest_version}\n\nGo to GitHub to download?"
                res = QMessageBox.information(self, "Nimble Update", msg, 
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if res == QMessageBox.StandardButton.Yes:
                    QDesktopServices.openUrl(QUrl("https://github.com/frizzy-cmd/corenimble"))
            else:
                QMessageBox.information(self, "Nimble Update", "You're on the latest version! Nice job!")
        except Exception as e:
            QMessageBox.warning(self, "Update Error", f"Couldn't reach GitHub. You may be offline, or it's our end.\nError: {e}")

    def setup_ui(self):
        self.corner_widget = QWidget()
        cl = QHBoxLayout(self.corner_widget); cl.setContentsMargins(0,0,5,0); cl.setSpacing(2)
        self.ghost_btn = QToolButton(); self.ghost_btn.setText("👻")
        self.new_tab_btn = QToolButton(); self.new_tab_btn.setText("+")
        self.ghost_btn.clicked.connect(lambda: self.add_new_tab(QUrl("https://duckduckgo.com"), ghost=True))
        self.new_tab_btn.clicked.connect(lambda: self.add_new_tab(QUrl(self.settings.get("homepage"))))
        cl.addWidget(self.ghost_btn); cl.addWidget(self.new_tab_btn)
        self.tabs.setCornerWidget(self.corner_widget, Qt.Corner.TopRightCorner)

        nav = QWidget(); nav.setObjectName("nav_container"); nl = QHBoxLayout(nav)
        self.back_btn = QPushButton("←"); self.forward_btn = QPushButton("→"); self.refresh_btn = QPushButton("↻")
        self.url_bar = QLineEdit(); self.book_btn = QToolButton(); self.book_btn.setText("★")
        self.dl_btn = QPushButton("⭳"); self.hist_btn = QPushButton("⏱︎"); self.sett_btn = QPushButton("⚙")
        
        self.handoff_btn = QPushButton("↗")
        self.handoff_btn.setToolTip("Open in Chrome/Edge for DRM Media")
        self.handoff_btn.clicked.connect(self.open_in_competitor)
        
        self.url_bar.returnPressed.connect(self.navigate)
        self.book_btn.clicked.connect(self.show_bookmarks_menu)
        self.back_btn.clicked.connect(lambda: self.tabs.currentWidget().back() if isinstance(self.tabs.currentWidget(), QWebEngineView) else None)
        self.forward_btn.clicked.connect(lambda: self.tabs.currentWidget().forward() if isinstance(self.tabs.currentWidget(), QWebEngineView) else None)
        self.refresh_btn.clicked.connect(lambda: self.tabs.currentWidget().reload() if isinstance(self.tabs.currentWidget(), QWebEngineView) else None)
        self.dl_btn.clicked.connect(lambda: self.add_special_tab("nimble://downloads"))
        self.hist_btn.clicked.connect(lambda: self.add_special_tab("nimble://history"))
        self.sett_btn.clicked.connect(lambda: self.add_special_tab("nimble://settings"))

        nl.addWidget(self.handoff_btn)
        for b in [self.back_btn, self.forward_btn, self.refresh_btn, self.url_bar, self.book_btn, self.dl_btn, self.hist_btn, self.sett_btn]: 
            nl.addWidget(b)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFixedHeight(1) # AHTE YOU PYTHON LET ME MAKE IT THINNAAAAHHHH
        self.progress_bar.hide()
        self.progress_bar.setFormat("")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: transparent;
            }
             QProgressBar::chunk {
                background-color: #8ab4f8;
                margin: 0px;
            }
        """)

        self.status_bar = QWidget()
        self.status_bar.setFixedHeight(25)
        self.status_bar.setStyleSheet("background: #171717; border-top: 1px solid #3c4043;")
        sl = QHBoxLayout(self.status_bar)
        sl.setContentsMargins(10, 0, 10, 0)

        self.status_label = QLabel(f"Nimble {VERSION} | Ready")
        self.status_label.setObjectName("status_label")
        self.status_label.setStyleSheet("font-size: 11px; color: #9aa0a6;")
        sl.addWidget(self.status_label)
        sl.addStretch()

        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setObjectName("zoom_label")
        self.zoom_label.setStyleSheet("font-size: 11px; color: #8ab4f8;")
        sl.addWidget(self.zoom_label)

        central = QWidget()
        central.setObjectName("main_bg")
        l = QVBoxLayout(central)
        l.setContentsMargins(0,0,0,0)
        l.setSpacing(0)
        
        l.addWidget(nav)                # Top
        l.addWidget(self.progress_bar)  # Under nav
        l.addWidget(self.tabs)          # Browser stuff
        l.addWidget(self.status_bar)    # Bottom

        self.setCentralWidget(central)
        self.resize(1280, 720)

    def apply_user_agent(self):
        ua_mode = self.settings.get("user_agent", "default")
        ua_str = UA_PRESETS.get(ua_mode, "") if ua_mode != "custom" else self.settings.get("custom_ua", "")
        self.profile.setHttpUserAgent(ua_str); self.ghost_profile.setHttpUserAgent(ua_str)

    def handle_tab_change(self, idx):
        w = self.tabs.widget(idx)
        if isinstance(w, QWebEngineView):
            self.url_bar.setText(w.url().toString())
            w.last_active = time.time()
            if getattr(w, 'is_suspended', False):
                w.is_suspended = False; w.setUrl(w.original_url) 

    def add_new_tab(self, url, ghost=False):
        browser = QWebEngineView()

        s = browser.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)

        browser.setPage(BrosterPage(self.ghost_profile if ghost else self.profile, browser, self))
        
        browser.is_ghost, browser.is_suspended, browser.last_active = ghost, False, time.time()
        idx = self.tabs.addTab(browser, "👻 mode" if ghost else "Loading..")
        browser.urlChanged.connect(lambda u: self.handle_url_change(browser, u))
        browser.titleChanged.connect(lambda t: self.tabs.setTabText(
            self.tabs.indexOf(browser), 
            (f"🔇 " if browser.page().isAudioMuted() else "") + (f"👻 {t[:12]}" if ghost else t[:15])
        ))
        browser.setUrl(url); self.tabs.setCurrentIndex(idx)
        browser.wheelEvent = self.make_zoom_scroll(browser)
        browser.page().contentsSizeChanged.connect(lambda: self.update_zoom_label(browser.zoomFactor()))

        browser.loadStarted.connect(self.progress_bar.show)
        browser.loadProgress.connect(self.progress_bar.setValue)
        browser.loadFinished.connect(self.progress_bar.hide)

        browser.urlChanged.connect(lambda u: self.status_label.setText(f"Nimble {VERSION} | Fetching {u.host()}..."))
        browser.loadStarted.connect(lambda: self.status_label.setText(f"Nimble {VERSION} | Fetching {browser.url().host()}..."))
        browser.loadFinished.connect(lambda: self.status_label.setText(f"Nimble {VERSION} | Ready"))
        return browser

    def check_suspension(self):
        if not self.settings.get("tab_suspend_enabled", True): return
        limit_s = self.settings.get("tab_suspend_min", 15) * 60
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if i != self.tabs.currentIndex() and isinstance(w, QWebEngineView) and not w.is_suspended:
                if time.time() - getattr(w, 'last_active', 0) > limit_s:
                    w.is_suspended = True; w.original_url = w.url()
                    w.setHtml("<html><body style='background:#202124;color:#8ab4f8;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;'><div><h2>Tab Sleeping...</h2><p>Click tab to wake up</p></div></body></html>")

    def show_bookmarks_menu(self):
        menu = QMenu(self); menu.setStyleSheet("background:#323639;color:white;")
        curr_w = self.tabs.currentWidget()
        curr_url = curr_w.url().toString() if isinstance(curr_w, QWebEngineView) else ""
        if curr_url and not curr_url.startswith("nimble://"):
            if curr_url not in self.bookmarks: menu.addAction("Bookmark Page", self.add_bookmark)
            else: menu.addAction("Remove Bookmark", lambda: self.remove_bookmark(curr_url))
        menu.addSeparator()
        for u in self.bookmarks: menu.addAction(u[:50]).triggered.connect(lambda _, url=u: self.add_new_tab(QUrl(url)))
        menu.exec(self.book_btn.mapToGlobal(self.book_btn.rect().bottomLeft()))

    def add_bookmark(self):
        u = self.tabs.currentWidget().url().toString()
        if u and u not in self.bookmarks: self.bookmarks.append(u)

    def remove_bookmark(self, url):
        if url in self.bookmarks: self.bookmarks.remove(url)

    def add_special_tab(self, url):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == url or (url == "nimble://specs" and self.tabs.tabText(i) == "System Specs"): 
                self.tabs.setCurrentIndex(i); return
        
        if url == "nimble://specs":
            try:
                gpu_info = "Unknown"
                if platform.system() == "Windows":
                    try:
                        r = subprocess.check_output("wmic path win32_VideoController get name", shell=True)
                        gpu_info = r.decode().strip().split('\n')[1]
                    except: pass
                
                mem = psutil.virtual_memory()
                proc = psutil.Process()
                ram_usage = f"{proc.memory_info().rss / 1024 / 1024:.1f} MB"
                total_ram = f"{mem.total / 1024 / 1024 / 1024:.1f} GB"
                
                html = f"""
                <html><head><style>
                    body {{ background-color: #202124; color: #f1f3f4; font-family: 'Inter', sans-serif; padding: 40px; }}
                    h1 {{ color: #8ab4f8; border-bottom: 1px solid #3c4043; padding-bottom: 15px; }}
                    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }}
                    .card {{ background: #292a2d; padding: 20px; border-radius: 12px; border: 1px solid #3c4043; }}
                    .label {{ color: #9aa0a6; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; font-weight: bold; }}
                    .value {{ font-size: 15px; font-family: 'Fira Code', monospace; color: #e8eaed; }}
                    .full {{ grid-column: 1 / -1; }}
                </style></head><body>
                    <h1>System specifications</h1>
                    <div class="grid">
                        <div class="card"><div class="label">CPU</div><div class="value">{platform.processor()}</div></div>
                        <div class="card"><div class="label">GPU renderer</div><div class="value">{gpu_info}</div></div>
                        <div class="card"><div class="label">Memory (App / Total)</div><div class="value">{ram_usage} / {total_ram}</div></div>
                        <div class="card"><div class="label">Engine versions</div><div class="value">Qt: {qVersion()}<br>Chromium: {qWebEngineChromiumVersion()}</div></div>
                        <div class="card full"><div class="label">Application path</div><div class="value">{bundle_dir}</div></div>
                        <div class="card full"><div class="label">Active flags</div><div class="value" style="font-size:12px; word-break: break-all;">{os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "None")}</div></div>
                    </div>
                </body></html>
                """
                
                view = QWebEngineView()
                view.setHtml(html)
                self.tabs.addTab(view, "System Specs")
                self.tabs.setCurrentWidget(view)
                return
            except Exception as e:
                print(f"Specs Error: {e}")

        container = QWidget(); container.setObjectName("main_bg"); l = QVBoxLayout(container); l.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(container); scroll.setObjectName("main_bg")
        if "history" in url:
            l.addWidget(QLabel("<h2>History</h2>"))
            btn_clr = QPushButton("Clear History"); btn_clr.clicked.connect(self.clear_history); l.addWidget(btn_clr)
            self.hist_container = QVBoxLayout(); l.addLayout(self.hist_container); self.refresh_history_ui()
        elif "downloads" in url:
            l.addWidget(QLabel("<h2>Downloads</h2>"))
            self.dl_container = QVBoxLayout(); l.addLayout(self.dl_container); self.refresh_downloads_ui(); self.ui_timer.start(1000)
        elif "settings" in url:
            l.addWidget(QLabel("<h2>Settings</h2>"))
            
            h = QLineEdit(self.settings.get("homepage"))
            l.addWidget(QLabel("Homepage:")); l.addWidget(h)
            
            ua_box = QComboBox()
            ua_box.addItems(UA_PRESETS.keys())
            ua_box.setCurrentText(self.settings.get("user_agent"))
            l.addWidget(QLabel("User Agent Preset:")); l.addWidget(ua_box)

            cua_input = QLineEdit(self.settings.get("custom_ua", ""))
            cua_input.setPlaceholderText("Mozilla/5.0... (only works if Preset is 'custom')")
            l.addWidget(QLabel("Custom User Agent string:")); l.addWidget(cua_input)
            
            ram_spin = QSpinBox(); ram_spin.setRange(512, 64000)
            ram_spin.setValue(self.settings.get("ram_limit_mb"))
            l.addWidget(QLabel("RAM Limit (MB):")); l.addWidget(ram_spin)
            
            soft_gpu = QCheckBox("Software Rendering (Restart required)")
            soft_gpu.setChecked(self.settings.get("software_rendering")); l.addWidget(soft_gpu)
            
            pan_toggle = QCheckBox("Enable Ctrl+Shift+P Panic Reset")
            pan_toggle.setChecked(self.settings.get("panic_enabled")); l.addWidget(pan_toggle)
            
            sus_toggle = QCheckBox("Suspend Tabs")
            sus_toggle.setChecked(self.settings.get("tab_suspend_enabled")); l.addWidget(sus_toggle)
            
            sus_min = QSpinBox(); sus_min.setRange(1, 1440)
            sus_min.setValue(self.settings.get("tab_suspend_min"))
            l.addWidget(QLabel("Suspend after (min):")); l.addWidget(sus_min)

            update_btn = QPushButton("Check for updates")
            update_btn.setStyleSheet("background-color: #34a853; color: white;")
            l.addWidget(update_btn)
            update_btn.clicked.connect(self.check_for_updates)
            
            save_btn = QPushButton("Save and Apply"); l.addWidget(save_btn)
            
            save_btn.clicked.connect(lambda: self.save_all(
                h.text(), 
                ua_box.currentText(), 
                cua_input.text(), 
                soft_gpu.isChecked(), 
                ram_spin.value(), 
                sus_toggle.isChecked(), 
                sus_min.value(), 
                pan_toggle.isChecked()
            ))

        self.tabs.addTab(scroll, url); self.tabs.setCurrentIndex(self.tabs.indexOf(scroll))

    def refresh_history_ui(self):
        if not hasattr(self, 'hist_container') or self.hist_container is None: return
        while self.hist_container.count():
            it = self.hist_container.takeAt(0).widget()
            if it: it.deleteLater()
        for u in self.history_items[:100]:
            row = QWidget(); rl = QHBoxLayout(row); rl.addWidget(QLabel(u[:90]))
            btn = QPushButton("Open"); btn.clicked.connect(lambda _, url=u: self.add_new_tab(QUrl(url))); rl.addWidget(btn)
            self.hist_container.addWidget(row)

    def refresh_downloads_ui(self):
        try:
            if not hasattr(self, 'dl_container') or self.dl_container is None:
                return
            if self.dl_container.count() > len(self.active_downloads):
                while self.dl_container.count() > len(self.active_downloads):
                    w = self.dl_container.takeAt(0).widget()
                    if w: w.deleteLater()
            
            for i, dl in enumerate(self.active_downloads):
                path = dl.downloadFileName()
                if i >= self.dl_container.count():
                    row = QWidget(); rl = QHBoxLayout(row)
                    name_btn = QPushButton(os.path.basename(path or "file"))
                    name_btn.setStyleSheet("QPushButton { border: none; color: #8ab4f8; text-decoration: underline; background: transparent; text-align: left; }")
                    name_btn.clicked.connect(lambda _, p=path: QDesktopServices.openUrl(QUrl.fromLocalFile(p)))
                    rl.addWidget(name_btn); rl.addWidget(QProgressBar()); self.dl_container.addWidget(row)
                
                row_w = self.dl_container.itemAt(i).widget()
                if row_w:
                    p_bar = row_w.findChild(QProgressBar)
                    if p_bar:
                        prog = int(dl.receivedBytes()/dl.totalBytes()*100) if dl.totalBytes() > 0 else 0
                        p_bar.setValue(prog)
                        
        except RuntimeError:
            self.ui_timer.stop()
            return

    def handle_download(self, d):
            fn = d.downloadFileName()
            path = os.path.join(os.path.expanduser("~"), "Downloads", fn)
            d.setDownloadFileName(path)
            d.accept()
            

            self.active_downloads.append(d)
            
            def on_finished():
                if d.isFinished():
                    if path not in self.downloads:
                        self.downloads.append(path)
                        self.save_nimble_data()
                    
                    self.tray.showMessage("Nimble", f"Finished: {fn}")
                    self.refresh_downloads_ui()

            d.isFinishedChanged.connect(on_finished)
            self.add_special_tab("nimble://downloads")

    def save_all(self, home, ua, cua, soft, ram, sus, sus_m, pan):
        self.settings.update({
            "homepage": home, 
            "user_agent": ua, 
            "custom_ua": cua, 
            "software_rendering": soft, 
            "ram_limit_mb": ram, 
            "tab_suspend_enabled": sus, 
            "tab_suspend_min": sus_m, 
            "panic_enabled": pan
        })
        save_settings(self.settings)
        
        self.apply_user_agent() 
        
        QMessageBox.information(self, "Nimble", "Settings saved!")

    def handle_url_change(self, browser, url):
            u = url.toString()
            
            if self.tabs.currentWidget() == browser: 
                self.url_bar.setText(u)
                if hasattr(browser, 'history'):
                    self.back_btn.setEnabled(browser.history().canGoBack())
                    self.forward_btn.setEnabled(browser.history().canGoForward())
            
            # PLS WORK
            if not getattr(browser, 'is_ghost', False) and not u.startswith("nimble://") and u != "about:blank":
                if u in self.history_items: 
                    self.history_items.remove(u)
                
                self.history_items.insert(0, u)
                
                self.history_items = self.history_items[:500]
                
                self.save_nimble_data()

    def update_progress(self, browser, p):
        if self.tabs.currentWidget() == browser:
            self.progress_bar.setVisible(p < 100); self.progress_bar.setValue(p)

    def navigate(self):
        t = self.url_bar.text().strip(); w = self.tabs.currentWidget()
        if t == "nimble://specs":
            self.add_special_tab(t)
            return
        if t and isinstance(w, QWebEngineView):
            u = QUrl(t if "://" in t else "https://"+t) if "." in t else QUrl(f"https://google.com/search?q={t}")
            w.setUrl(u)

    def clear_history(self):
        self.history_items = []; self.refresh_history_ui()

    def close_tab(self, i):
        if self.tabs.tabText(i) == "nimble://downloads":
            self.ui_timer.stop()
            
        if self.tabs.count() > 1: 
            self.tabs.widget(i).deleteLater()
            self.tabs.removeTab(i)
        else: 
            self.close()

    def open_in_competitor(self):
        curr_url = self.tabs.currentWidget().url().toString()
        if curr_url and not curr_url.startswith("nimble://"):
            QDesktopServices.openUrl(QUrl(curr_url))
    


if __name__ == "__main__":
    import traceback
    from pathlib import Path
    import glob
    import random

    os.environ["QT_OPENGL_BACKEND"] = "desktop"
    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
    
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        internal_path = os.path.join(base_path, "_internal")
        bundle_dir = internal_path if os.path.exists(internal_path) else base_path
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    _settings_dir = os.path.join(local_app_data, "CoreNimble")
    if not os.path.exists(_settings_dir): os.makedirs(_settings_dir)
    CONFIG_FILE = os.path.join(_settings_dir, "nimble_settings.json")

    _settings = load_settings()
    limit = _settings.get("ram_limit_mb", 2048)
    user_extra = _settings.get("extra_flags", "")
    
    def get_widevine_path():
        local_wv = os.path.join(bundle_dir, "WidevineCdm")
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        
        potential_patterns = [
            local_wv,
            os.path.join(local_app_data, r"Google\Chrome\User Data\WidevineCdm\*\_platform_specific\win_x64"),
            os.path.join(program_files, r"Microsoft\Edge\Application\*\WidevineCdm\*\_platform_specific\win_x64"),
            os.path.join(local_app_data, r"Microsoft\Edge\User Data\WidevineCdm\*\_platform_specific\win_x64")
        ]
        for pattern in potential_patterns:
            if pattern == local_wv and os.path.exists(pattern): return pattern
            found = glob.glob(pattern)
            if found: return found[-1]
        return None

    wv_path = get_widevine_path()
    wv_flags = f"--widevine-path=\"{wv_path}\" --enable-widevine-cdm --enable-features=WidevineCdm " if wv_path else ""

    base_flags = (
        f"{wv_flags}--ignore-gpu-blocklist --js-flags='--max-old-space-size={limit}' "
        f"--enable-gpu-rasterization --enable-zero-copy {user_extra}"
    )

    if _settings.get("software_rendering"):
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = f"--disable-gpu --disable-software-rasterizer {base_flags}"
    else:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = base_flags

    APP_ID = "frizzy.corenimble.browser.v1"
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except:
        pass

    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

    app = QApplication(sys.argv)
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("frizzy.corenimble.browser.v1")

    icon_path = os.path.join(bundle_dir, "iconn.ico")
    app.setWindowIcon(QIcon(icon_path))

    app.setApplicationName("Nimble")
    app.setStyle('Fusion')

    font_dir = os.path.join(bundle_dir, "fonts")
    for font_name in ["InterRegular.ttf", "FiraCodeRegular.ttf"]:
        f_path = os.path.join(font_dir, font_name)
        if os.path.exists(f_path):
            QFontDatabase.addApplicationFont(f_path)
        else:
            print(f"⚠️ Failed to load {font_name} at {f_path}")

    try:
        window = CoreNimble() 
        window.show()
        sys.exit(app.exec())

    except Exception as e:
        quips = [
            "OW! I tripped! That really hurt!",
            "Whoops... Think i just messed up..",
            "Dooooooohhhh.... I'm gonna take a nap..",
            "Whoops, my bad dude.",
            "I've fallen and I can't get up!",
            "OWWWWWWWWW THAT REALLY REALY HURT!!!",
            "Everything was fine... until it wasn't.",
            "What the hell man??",
        ]
        
        chosen_quip = random.choice(quips)
        error_msg = f"{chosen_quip}\n\nError: {str(e)}\n\nA crash report is on your desktop, Show this to a developer!"
        
        if QApplication.instance():
            QMessageBox.critical(None, "Nimble Error", error_msg)
        
        desktop = Path.home() / "Desktop"
        try:
            with open(desktop / "crashdump.txt", "w") as f:
                f.write(f"--- {chosen_quip} ---\n\n{traceback.format_exc()}")
        except:
            pass