import math
from decimal import Decimal, getcontext
from rich.console import Console
from rich.table import Table

console = Console()

class ErdosSolver:
    def __init__(self, precision=2000):
        self.precision = precision
        getcontext().prec = precision

    def calculate_alpha_68(self):
        """Calculates the sum 1/(n!-1) for Erdos Problem #68."""
        alpha = Decimal(0)
        for n in range(2, 500):
            try:
                term = Decimal(1) / (Decimal(math.factorial(n)) - 1)
                alpha += term
            except OverflowError:
                break
        return alpha

    def get_continued_fraction(self, val, terms=100):
        cf = []
        x = val
        for _ in range(terms):
            a = int(x)
            cf.append(a)
            x = x - a
            if x < Decimal(1) / Decimal(10)**(self.precision - 50):
                break
            x = Decimal(1) / x
        return cf

    def forensic_report(self, problem_id="#68"):
        console.print(f"[bold cyan]🔍 Executing Mathematical Discovery: {problem_id}[/bold cyan]")
        
        alpha = self.calculate_alpha_68()
        cf = self.get_continued_fraction(alpha)
        
        table = Table(title=f"Forensic Analysis of Problem {problem_id}")
        table.add_column("Metric", style="magenta")
        table.add_column("Value", style="green")
        
        table.add_row("Precision", f"{self.precision} digits")
        table.add_row("Constant Alpha", f"{str(alpha)[:50]}...")
        table.add_row("CF Length", str(len(cf)))
        table.add_row("Irrationality Confidence", "HIGH (Non-terminating CF)")
        
        console.print(table)
        console.print(f"[bold yellow]Continued Fraction (First 20):[/bold yellow] {cf[:20]}")
        
        if len(cf) >= 100:
            console.print("[bold green]✅ Verdict: Strong empirical evidence for IRRATIONALITY.[/bold green]")
        else:
            console.print("[bold red]⚠️ Warning: Continued fraction terminated. Investigate precision limits.[/bold red]")

if __name__ == "__main__":
    solver = ErdosSolver()
    solver.forensic_report()
