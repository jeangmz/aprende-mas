"""Input handler para niños - entrada segura."""
import sys
if sys.platform == "win32":
    import msvcrt
else:
    import tty, termios

def get_int_valid(prompt: str, valid_min: int, valid_max: int, max_tries: int = 5) -> int:
    for _ in range(max_tries):
        try:
            user = input(prompt).strip()
            if not user:
                continue
            val = int(user)
            if valid_min <= val <= valid_max:
                return val
            print(f"Por favor, numero entre {valid_min} y {valid_max}.")
        except ValueError:
            print("Entrada invalida. Solo numeros.")
    return valid_min

def get_enter_to_continue(msg: str = "Presiona Enter para continuar") -> None:
    print(msg)
    if sys.platform == "win32":
        msvcrt.getch()
        msvcrt.getch()
    else:
        try:
            tty.setcbreak(sys.stdin.fileno())
            while True:
                ch = sys.stdin.read(1)
                if ch in ("\r", "\n"):
                    break
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, termios.tcgetattr(sys.stdin))