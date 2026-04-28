from PyQt5.QtCore import QObject, pyqtSignal as Signal

class ThemeManager(QObject):
    theme_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_theme = 'light'
        self.themes = {
            'light': {
                'background': '#ffffff',
                'foreground': '#000000',
                'cell_selected': '#e8f4fd',
                'cell_border': '#1a73e8',
                'editor_background': '#ffffff',
                'editor_foreground': '#000000',
                'output_background': '#fafafa',
                'output_border': '#eee',
                'error_background': '#ffebee',
                'error_border': '#ef9a9a',
                'error_text': '#c62828',
                'markdown_background': '#ffffff',
                'button_background': '#f0f0f0',
                'button_hover': '#e0e0e0',
                'status_bar': '#f0f0f0',
                'scroll_area': '#ffffff',
                'gutter': '#f5f5f5'
            },
            'dark': {
                'background': '#1e1e1e',
                'foreground': '#d4d4d4',
                'cell_selected': '#264f78',
                'cell_border': '#569cd6',
                'editor_background': '#1e1e1e',
                'editor_foreground': '#d4d4d4',
                'output_background': '#252526',
                'output_border': '#3c3c3c',
                'error_background': '#3c1a1a',
                'error_border': '#8b4557',
                'error_text': '#ff7b72',
                'markdown_background': '#1e1e1e',
                'button_background': '#2d2d2d',
                'button_hover': '#3d3d3d',
                'status_bar': '#252526',
                'scroll_area': '#1e1e1e',
                'gutter': '#252526'
            }
        }
        
    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.theme_changed.emit(theme_name)
            
    def get_theme(self):
        return self.themes.get(self.current_theme, self.themes['light'])
    
    def get_current_theme_name(self):
        return self.current_theme