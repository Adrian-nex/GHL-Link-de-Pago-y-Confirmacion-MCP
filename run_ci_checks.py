#!/usr/bin/env python3
"""
Script robusto para ejecutar verificaciones de CI localmente
Incluye mejor manejo de errores y información de debug
"""
import os
import subprocess
import sys
import time
from pathlib import Path


def print_header(title):
    """Imprime un encabezado formateado"""
    print(f"\n{'='*60}")
    print(f"[INFO] {title}")
    print(f"{'='*60}")


def print_step(step, description):
    """Imprime un paso del proceso"""
    print(f"\n[STEP {step}] {description}")
    print("-" * 50)


def run_command(command, description, allow_failure=False):
    """Ejecuta un comando y muestra el resultado con mejor manejo de errores"""
    print(f"\n[INFO] {description}")
    print(f"Comando: {command}")
    print("-" * 50)

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos timeout
        )
        print("[SUCCESS] Comando ejecutado correctamente")
        if result.stdout and result.stdout.strip():
            print("[OUTPUT]:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("[ERROR] Comando falló")
        if e.stdout and e.stdout.strip():
            print("[STDOUT]:")
            print(e.stdout)
        if e.stderr and e.stderr.strip():
            print("[STDERR]:")
            print(e.stderr)
        if not allow_failure:
            return False
        else:
            print("[WARNING] Error permitido")
            return True
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] Comando tardó más de 5 minutos")
        return False
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        return False


def check_environment():
    """Verifica el entorno de desarrollo"""
    print_header("VERIFICACIÓN DEL ENTORNO")

    # Verificar Python
    print_step(1, "Verificando Python")
    run_command("python --version", "Versión de Python")
    run_command("pip --version", "Versión de pip")

    # Verificar archivos necesarios
    print_step(2, "Verificando archivos del proyecto")
    required_files = [
        "manage.py",
        "requirements.txt",
        "backend/settings.py",
        "payments/models.py",
    ]

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"[OK] {file_path}")
        else:
            print(f"[MISSING] {file_path} - FALTANTE")
            return False

    # Verificar directorio de logs
    print_step(3, "Creando directorio de logs")
    os.makedirs("logs", exist_ok=True)
    print("[OK] Directorio de logs creado")

    return True


def setup_database():
    """Configura la base de datos"""
    print_header("CONFIGURACIÓN DE BASE DE DATOS")

    # Migrar base de datos
    print_step(1, "Ejecutando migraciones")
    if not run_command("python manage.py migrate", "Aplicando migraciones"):
        return False

    # Verificar migraciones pendientes
    print_step(2, "Verificando migraciones pendientes")
    if not run_command(
        "python manage.py makemigrations --check --dry-run", "Verificando migraciones"
    ):
        return False

    return True


def run_quality_checks():
    """Ejecuta las verificaciones de calidad de código"""
    print_header("VERIFICACIONES DE CALIDAD")

    # Comandos de calidad
    quality_commands = [
        ("python manage.py check", "Verificación Django", False),
        ("black --check --diff .", "Formato de código (Black)", False),
        ("isort --check-only --diff .", "Orden de imports (isort)", False),
        (
            "flake8 . --count --select=E9,F63,F7,F82 --exclude=.venv,venv,migrations,__pycache__",
            "Linting (flake8)",
            False,
        ),
    ]

    success_count = 0
    total_count = len(quality_commands)

    for command, description, allow_failure in quality_commands:
        if run_command(command, description, allow_failure):
            success_count += 1

    return success_count, total_count


def run_tests():
    """Ejecuta las pruebas unitarias"""
    print_header("EJECUCIÓN DE PRUEBAS")

    # Ejecutar pytest con cobertura
    print_step(1, "Ejecutando pruebas unitarias")
    test_command = "pytest --cov=. --cov-report=term-missing --cov-report=xml -v"

    if run_command(test_command, "Ejecutando pytest con cobertura"):
        print("[SUCCESS] Todas las pruebas pasaron")
        return True
    else:
        print("[ERROR] Algunas pruebas fallaron")
        return False


def main():
    """Función principal mejorada"""
    start_time = time.time()

    print_header("INICIANDO VERIFICACIONES DE CI")
    print(f"[TIME] Iniciado en: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Verificar entorno
    if not check_environment():
        print("\n[ERROR] Verificación del entorno falló")
        return 1

    # Configurar base de datos
    if not setup_database():
        print("\n[ERROR] Configuración de base de datos falló")
        return 1

    # Ejecutar verificaciones de calidad
    quality_success, quality_total = run_quality_checks()

    # Ejecutar pruebas
    tests_passed = run_tests()

    # Resumen final
    end_time = time.time()
    duration = end_time - start_time

    print_header("RESUMEN FINAL")
    print(f"[DURATION] Duración total: {duration:.2f} segundos")
    print(f"[QUALITY] Verificaciones de calidad: {quality_success}/{quality_total}")
    print(f"[TESTS] Pruebas: {'PASARON' if tests_passed else 'FALLARON'}")

    total_success = quality_success + (1 if tests_passed else 0)
    total_checks = quality_total + 1

    print(f"\n[RESULT] RESULTADO FINAL: {total_success}/{total_checks}")

    if total_success == total_checks:
        print("\n[SUCCESS] ¡TODAS LAS VERIFICACIONES PASARON!")
        print("[READY] El código está listo para CI/CD")
        return 0
    else:
        print(f"\n[WARNING] {total_checks - total_success} verificaciones fallaron")
        print("[ERROR] Revisa los errores antes de hacer commit")
        return 1


if __name__ == "__main__":
    sys.exit(main())
