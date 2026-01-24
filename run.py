import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QLibraryInfo
        from app.main_window import WorkoutTrackerApp
        
        # Restore Qt plugin path after OpenCV overrides it.
        qt_plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
        os.environ["QT_PLUGIN_PATH"] = qt_plugins_path
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(qt_plugins_path, "platforms")
        os.environ["OPENCV_QT_PLUGIN_PATH"] = qt_plugins_path

        app = QApplication(sys.argv)
        app.setApplicationName("AI Fitness Assistant")
        app.setApplicationVersion("1.2.0")
        
        window = WorkoutTrackerApp()
        window.show()
        
        sys.exit(app.exec_())
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed correctly")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
