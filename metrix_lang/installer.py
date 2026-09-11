import os
import platform
import shutil
import subprocess
import sys
from urllib.parse import urlparse


METRIX_PACKAGE_DIR = os.path.expanduser("~/.metrix-packages")


def detect_package_manager():
    system = platform.system().lower()
    if system == "linux":
        if shutil.which("apt"):
            return "apt"
        if shutil.which("dnf"):
            return "dnf"
        if shutil.which("pacman"):
            return "pacman"
        if shutil.which("zypper"):
            return "zypper"
        if shutil.which("apk"):
            return "apk"
    elif system == "darwin":
        if shutil.which("brew"):
            return "brew"
    elif system == "windows":
        if shutil.which("winget"):
            return "winget"
        if shutil.which("choco"):
            return "choco"
    return None


def detect_easy_venv():
    candidates = [
        os.environ.get("VIRTUAL_ENV"),
        os.path.join(os.path.dirname(sys.executable), "pip"),
        os.path.join(os.path.dirname(sys.executable), "pip3"),
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return os.path.dirname(candidate) if os.path.isfile(candidate) else candidate
    return None


def pip_install(target):
    easy_venv = detect_easy_venv()
    if easy_venv:
        pip = os.path.join(easy_venv, "bin", "pip")
        if os.path.exists(pip):
            subprocess.run([pip, "install", target], check=True)
            return

    pip_candidates = [
        os.path.join(sys.prefix, "bin", "pip"),
        os.path.join(sys.prefix, "bin", "pip3"),
        shutil.which("pip"),
        shutil.which("pip3"),
        sys.executable,
    ]
    pip = next((c for c in pip_candidates if c), None)
    if pip is None:
        raise RuntimeError("pip is not available")

    cmd = [pip, "install", target]
    if sys.executable not in (pip, None):
        cmd = [sys.executable, "-m", "pip", "install", target]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if "--break-system-packages" not in cmd:
            cmd.append("--break-system-packages")
            subprocess.run(cmd, check=True)
        else:
            raise


def is_python_package(name):
    if not name or name.startswith("-"):
        return False
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception:
        return False


def is_npm_package(name):
    if not name or name.startswith("-"):
        return False
    if name.startswith("@") or "/" in name:
        return True
    if shutil.which("npm") is None:
        return False
    try:
        result = subprocess.run(
            ["npm", "info", name, "--json"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def is_github_url(url):
    try:
        parsed = urlparse(url)
        return parsed.hostname in ("github.com", "raw.githubusercontent.com")
    except Exception:
        return False


def install_system_package(name):
    manager = detect_package_manager()
    if manager is None:
        raise RuntimeError("No supported system package manager found")

    commands = {
        "apt": ["sudo", "apt", "install", "-y", name],
        "dnf": ["sudo", "dnf", "install", "-y", name],
        "pacman": ["sudo", "pacman", "-S", "--noconfirm", name],
        "zypper": ["sudo", "zypper", "install", "-y", name],
        "apk": ["sudo", "apk", "add", name],
        "brew": ["brew", "install", name],
        "winget": ["winget", "install", name],
        "choco": ["choco", "install", "-y", name],
    }

    cmd = commands.get(manager)
    if cmd is None:
        raise RuntimeError(f"Unsupported package manager: {manager}")
    subprocess.run(cmd, check=True)


def install_npm_package(name):
    if shutil.which("npm") is None:
        raise RuntimeError("npm is not installed")
    subprocess.run(["npm", "install", "-g", name], check=True)


def _ensure_pyproject_fix(dest):
    pyproject = os.path.join(dest, "pyproject.toml")
    if not os.path.exists(pyproject):
        return
    with open(pyproject, "r", encoding="utf-8") as f:
        content = f.read()
    if "[tool.setuptools.packages.find]" in content:
        return
    if "error: Multiple top-level packages discovered" in content:
        return
    with open(pyproject, "a", encoding="utf-8") as f:
        f.write('\n[tool.setuptools.packages.find]\nwhere = ["."]\ninclude = ["metrix_lang*"]\nexclude = ["install*", "tests*"]\n')


def install_github_repo(url, target_name=None):
    if shutil.which("git") is None:
        raise RuntimeError("git is not installed")

    parsed = urlparse(url)
    path = parsed.path.strip("/")
    parts = path.split("/")

    if len(parts) < 2:
        raise RuntimeError(f"Invalid GitHub URL: {url}")

    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    target = target_name or repo
    clone_url = f"https://github.com/{owner}/{repo}.git"
    dest = os.path.join(METRIX_PACKAGE_DIR, target)

    if os.path.exists(dest):
        subprocess.run(["git", "-C", dest, "pull", "--ff-only"], check=True)
    else:
        os.makedirs(METRIX_PACKAGE_DIR, exist_ok=True)
        subprocess.run(["git", "clone", clone_url, dest], check=True)

    _ensure_pyproject_fix(dest)

    install_script = os.path.join(dest, "install", "install.sh")
    if os.path.exists(install_script):
        env = os.environ.copy()
        env["METRIX_INSTALL_DIR"] = os.path.expanduser("~/.metrix-lang")
        env["METRIX_BIN_DIR"] = os.path.join(os.path.expanduser("~"), ".local", "bin")
        subprocess.run(["bash", install_script], check=True, env=env)
        return dest

    pyproject = os.path.join(dest, "pyproject.toml")
    setup_py = os.path.join(dest, "setup.py")
    if os.path.exists(pyproject) or os.path.exists(setup_py):
        cmd = [sys.executable, "-m", "pip", "install", "-e", dest]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            try:
                subprocess.run(cmd + ["--break-system-packages"], check=True)
            except subprocess.CalledProcessError:
                venv_dir = os.path.join(dest, ".venv")
                if not os.path.exists(venv_dir):
                    subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
                venv_pip = os.path.join(venv_dir, "bin", "pip")
                subprocess.run([venv_pip, "install", "-e", dest], check=True)

    return dest


def install_from_url(url, target_name=None):
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or target_name or "download"
    dest_dir = os.path.join(METRIX_PACKAGE_DIR, target_name or filename)
    os.makedirs(dest_dir, exist_ok=True)

    if shutil.which("curl"):
        subprocess.run(["curl", "-fsSL", url, "-o", os.path.join(dest_dir, filename)], check=True)
    elif shutil.which("wget"):
        subprocess.run(["wget", url, "-O", os.path.join(dest_dir, filename)], check=True)
    else:
        raise RuntimeError("Neither curl nor wget is available to download the URL")

    return dest_dir


def install(target):
    if not target:
        raise RuntimeError("No install target provided")

    if is_github_url(target):
        print(f"Installing GitHub repo: {target}")
        return install_github_repo(target)

    if target.startswith("http://") or target.startswith("https://"):
        print(f"Installing from URL: {target}")
        return install_from_url(target)

    if "/" in target and not target.startswith("-") and "://" not in target:
        parts = target.split("/")
        if len(parts) == 2 and all(parts):
            owner, repo = parts
            local_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_name = os.path.basename(local_root)
            if repo == local_name and owner.lower() == "dxn1-ubuntu":
                print(f"Installing local METRIX source: {local_root}")
                return _install_local(local_root)
            print(f"Installing GitHub repo: {target}")
            return install_github_repo(f"https://github.com/{target}")

    if is_python_package(target):
        print(f"Installing Python package: {target}")
        pip_install(target)
        return target

    if is_npm_package(target):
        print(f"Installing npm package: {target}")
        install_npm_package(target)
        return target

    manager = detect_package_manager()
    if manager:
        print(f"Installing system package via {manager}: {target}")
        install_system_package(target)
        return target

    raise RuntimeError(f"Could not determine how to install: {target}")


def _install_local(dest):
    cmd = [sys.executable, "-m", "pip", "install", "-e", dest]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        subprocess.run(cmd + ["--break-system-packages"], check=True)
    return dest
