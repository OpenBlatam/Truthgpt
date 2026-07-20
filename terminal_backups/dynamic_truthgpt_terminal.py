# dynamic_truthgpt_terminal.py
# Enhanced Dynamic TruthGPT Terminal with Claude-Style Interface

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt
    from rich.live import Live
    from rich.columns import Columns
    from rich.align import Align
    from rich.padding import Padding
except ImportError:
    print('Installing Rich UI components...')
    import subprocess
    subprocess.run(['pip', 'install', 'rich'], check=True)
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt
    from rich.live import Live
    from rich.columns import Columns
    from rich.align import Align
    from rich.padding import Padding

# Import local optimization modules
try:
    from papers.chain_of_draft import ChainOfDraft
    from papers.elastic_reasoning import ElasticReasoning
    from papers.fp16_stability import FP16Stability
    from latency_optimizations import apply_chain_of_draft, apply_elastic_reasoning, apply_fp16_stability
except ImportError:
    ChainOfDraft = None
    ElasticReasoning = None
    FP16Stability = None

class DynamicTruthGPTTerminal:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.session_history = []
        self.system_metrics = {}
        self.config = self.load_config()
        self.theme = self.config.get('theme', 'cyan')  # cyan por defecto, estilo Claude
        self.setup_layout()
        
    def load_config(self) -> Dict[str, Any]:
        config_file = Path('terminal_config.json')
        if config_file.exists():
            return json.loads(config_file.read_text())
        return {
            'theme': 'cyan',
            'shortcuts': {
                ':q': 'quit',
                ':h': 'help',
                ':s': 'status',
                ':p': 'papers',
                ':c': 'config',
                ':t': 'theme'
            },
            'max_history': 50
        }
    
    def save_config(self):
        config_file = Path('terminal_config.json')
        config_file.write_text(json.dumps(self.config, indent=2))
    
    def setup_layout(self):
        # Create modern split-screen layout
        self.layout.split_column(
            Layout(name='header', size=4),
            Layout(name='main'),
            Layout(name='footer', size=2)
        )
        
        self.layout['main'].split_row(
            Layout(name='sidebar', size=32),
            Layout(name='content')
        )
        
    def render_header(self) -> Panel:
        title = Text('🚀 TruthGPT Terminal', style=f'bold {self.theme}')
        subtitle = Text(f'📚 3 Papers loaded | 🎨 Theme: {self.theme} | 💬 {len(self.session_history)} commands', style='dim')
        header_content = Align.center(title + '\n' + subtitle)
        return Panel(
            header_content,
            style=self.theme,
            border_style=f'bright_{self.theme}',
            box=Panel.c.ROUNDED_EDGE
        )
    
    def render_sidebar(self) -> Panel:
        table = Table(show_header=False, box=None, expand=True)
        table.add_column('Commands', style=f'{self.theme}')
        
        commands = [
            ':h - Help',
            ':s - System Status',
            ':p - Papers List',
            ':c - Config',
            ':t - Change Theme',
            ':q - Quit',
            '',
            'infer <text>',
            'papers list',
            'status',
            'config show'
        ]
        
        for cmd in commands:
            table.add_row(Padding(cmd, (0, 2)))
        
        return Panel(
            Align.left(table),
            title='[bold]⚡ Quick Commands[/bold]',
            style=self.theme,
            border_style=f'bright_{self.theme}',
            box=Panel.c.ROUNDED_EDGE
        )
    
    def render_content(self, content: str = '') -> Panel:
        if not content:
            content = Align.center('[dim]Ready for commands. Type :h for help.[/dim]', vertical='middle')
        return Panel(
            content,
            title='[bold]🤖 Output[/bold]',
            style=self.theme,
            border_style=f'bright_{self.theme}',
            box=Panel.c.ROUNDED_EDGE,
            min_height=20
        )
    
    def render_footer(self) -> Panel:
        footer_text = f'✨ TruthGPT v5.9 | 📄 Chain-of-Draft, Elastic-Reasoning, FP16 | ⏱️ {time.strftime("%H:%M:%S")}'
        return Panel(
            Align.center(footer_text),
            style=f'dim {self.theme}',
            border_style=f'dim {self.theme}',
            box=Panel.c.ROUNDED_EDGE
        )
    
    def process_shortcut(self, command: str) -> Optional[str]:
        if command in self.config['shortcuts']:
            return self.config['shortcuts'][command]
        return None
    
    def execute_command(self, user_input: str) -> str:
        if not user_input.strip():
            return 'Enter a command or :h for help'
        
        # Handle shortcuts
        shortcut = self.process_shortcut(user_input.strip())
        if shortcut:
            user_input = shortcut
        
        # Add to history
        self.session_history.append({
            'command': user_input,
            'timestamp': time.time()
        })
        
        # Trim history
        max_hist = self.config.get('max_history', 50)
        if len(self.session_history) > max_hist:
            self.session_history = self.session_history[-max_hist:]
        
        # Aquí iría la lógica de comandos reales
        # Por ahora, devolvemos un placeholder
        if user_input == 'help':
            return '[bold]Available commands:[/bold]\n:q, :h, :s, :p, :c, :t\ninfer <text>'
        elif user_input == 'status':
            return '[bold green]System operational[/bold green]'
        elif user_input == 'papers':
            return 'Chain-of-Draft, Elastic-Reasoning, FP16-Stability'
        elif user_input == 'config':
            return json.dumps(self.config, indent=2)
        elif user_input == 'theme':
            themes = ['cyan', 'blue', 'green', 'magenta', 'yellow']
            current = self.theme
            idx = themes.index(current) if current in themes else 0
            self.theme = themes[(idx + 1) % len(themes)]
            self.config['theme'] = self.theme
            self.save_config()
            return f'Theme changed to [bold {self.theme}]{self.theme}[/bold {self.theme}]'
        else:
            return f"[dim]Unrecognized command: {user_input}[/dim]\nType :h for help."
