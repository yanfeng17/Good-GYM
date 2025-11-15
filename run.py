import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        from PyQt5.QtWidgets import QApplication
        from app.main_window import WorkoutTrackerApp
        
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