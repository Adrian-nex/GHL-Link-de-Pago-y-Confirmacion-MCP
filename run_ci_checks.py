#!/usr/bin/env python3
"""
Script simple para ejecutar verificaciones de CI localmente
"""
import subprocess
import sys


def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n[INFO] {description}")
    print(f"Comando: {command}")
    print("-" * 50)

    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print("SUCCESS")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("ERROR")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Función principal"""
    print("Ejecutando verificaciones de CI localmente")
    print("=" * 60)

    # Comandos básicos
    commands = [
        ("python manage.py check", "Verificacion Django"),
        ("black --check --diff .", "Formato de codigo"),
        ("isort --check-only --diff .", "Orden de imports"),
        (
            "flake8 . --count --select=E9,F63,F7,F82 --exclude=.venv,venv,migrations",
            "Linting",
        ),
        ("pytest", "Pruebas"),
    ]

    success_count = 0
    total_count = len(commands)

    for command, description in commands:
        if run_command(command, description):
            success_count += 1

    # Resumen
    print("\n" + "=" * 60)
    print(f"SUCCESS: {success_count}/{total_count}")
    print(f"FAILED: {total_count - success_count}/{total_count}")

    if success_count == total_count:
        print("\nTodas las verificaciones pasaron!")
        return 0
    else:
        print("\nAlgunas verificaciones fallaron")
        return 1


if __name__ == "__main__":
    sys.exit(main())
