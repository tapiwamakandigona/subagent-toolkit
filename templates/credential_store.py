#!/usr/bin/env python3
"""Private operator-provided credential storage and redacted subprocess use."""

from __future__ import annotations

import argparse
import base64
import getpass
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import urllib.parse


MAX_SECRET_BYTES = 1024 * 1024


class CredentialError(Exception):
    pass


def validate_name(name: str) -> None:
    if not re.fullmatch(r"[a-z][a-z0-9_.-]{0,63}", name):
        raise CredentialError("Use a simple credential name, not a path")


def store_path(override: str | Path | None = None) -> Path:
    candidate = Path(
        override or os.environ.get(
            "AGENT_SECRET_DIR", str(Path.home() / ".local/share/agent-secrets")
        )
    ).expanduser().absolute()
    if candidate.is_symlink():
        raise CredentialError("Credential directory cannot be a symlink")
    resolved = candidate.resolve()
    for ancestor in (resolved, *resolved.parents):
        if (ancestor / ".git").exists():
            raise CredentialError("Credential directory must be outside every repository")
    return resolved


def validate_private(path: Path, directory: bool = False) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise CredentialError("Credential is missing; provision it once") from error
    expected = 0o700 if directory else 0o600
    kind_ok = stat.S_ISDIR(metadata.st_mode) if directory else stat.S_ISREG(metadata.st_mode)
    if not kind_ok or stat.S_ISLNK(metadata.st_mode):
        raise CredentialError("Credential paths must be real directories or regular files")
    if metadata.st_uid != os.getuid():
        raise CredentialError("Credential path belongs to another user")
    if stat.S_IMODE(metadata.st_mode) != expected:
        raise CredentialError(f"Credential permissions must be {expected:o}")
    if not directory and metadata.st_nlink != 1:
        raise CredentialError("Hard-linked credential files are not accepted")


def ensure_store(override: str | Path | None = None) -> Path:
    directory = store_path(override)
    if not directory.exists():
        directory.mkdir(parents=True, mode=0o700)
    validate_private(directory, directory=True)
    return directory


def write_secret(
    name: str, value: bytes, override: str | Path | None = None,
    replace: bool = False,
) -> Path:
    validate_name(name)
    if not value or len(value) > MAX_SECRET_BYTES:
        raise CredentialError("Credential must be nonempty and at most 1 MiB")
    directory = ensure_store(override)
    destination = directory / name
    if destination.is_symlink():
        raise CredentialError("Refusing symlink credential file")
    if destination.exists():
        validate_private(destination)
        if not replace:
            raise CredentialError("Credential already exists; use --replace only to rotate it")
    descriptor, temporary = tempfile.mkstemp(prefix=".secret-", dir=directory)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, destination)
        else:
            # An atomic no-clobber installation; no accidental overwrite race.
            os.link(temporary, destination)
            os.unlink(temporary)
        validate_private(destination)
    except FileExistsError as error:
        raise CredentialError("Credential already exists; no value was overwritten") from error
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return destination


def read_secret(name: str, override: str | Path | None = None) -> bytes:
    validate_name(name)
    directory = store_path(override)
    validate_private(directory, directory=True)
    path = directory / name
    validate_private(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1
        ):
            raise CredentialError("Unsafe credential file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            value = stream.read(MAX_SECRET_BYTES + 1)
        if not value or len(value) > MAX_SECRET_BYTES:
            raise CredentialError("Credential file is empty or too large")
        return value
    finally:
        os.close(descriptor)


def list_names(override: str | Path | None = None) -> list[str]:
    directory = store_path(override)
    validate_private(directory, directory=True)
    names = []
    for path in directory.iterdir():
        if path.name.startswith(".secret-"):
            continue
        validate_name(path.name)
        validate_private(path)
        names.append(path.name)
    return sorted(names)


def redact_output(output: bytes, secrets: list[bytes]) -> bytes:
    variants: set[bytes] = set()
    for secret in secrets:
        variants.add(secret)
        variants.add(base64.b64encode(secret))
        variants.add(urllib.parse.quote_from_bytes(secret, safe="").encode())
    for value in sorted(variants, key=len, reverse=True):
        if value:
            output = output.replace(value, b"[REDACTED]")
    return output


def execute_with_secrets(
    mappings: list[str], command: list[str], override: str | Path | None = None,
    timeout: float = 120,
) -> int:
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise CredentialError("Provide the authorized command after --")
    if timeout <= 0:
        raise CredentialError("Timeout must be positive")
    environment = os.environ.copy()
    secrets: list[bytes] = []
    seen: set[str] = set()
    for mapping in mappings:
        name, separator, variable = mapping.partition("=")
        if not separator or not re.fullmatch(r"[A-Z][A-Z0-9_]*", variable):
            raise CredentialError("Use --map credential_name=ENV_VARIABLE")
        if variable in seen:
            raise CredentialError("Each destination environment variable must be unique")
        seen.add(variable)
        value = read_secret(name, override)
        try:
            environment[variable] = value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CredentialError("Environment credentials must be UTF-8 text") from error
        if "\x00" in environment[variable]:
            raise CredentialError("Environment credentials cannot contain NUL bytes")
        if any(environment[variable] in argument for argument in command):
            raise CredentialError("Do not put credential values in command arguments")
        secrets.append(value)
    try:
        process = subprocess.Popen(
            command, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            start_new_session=(os.name == "posix"),
        )
        output, errors = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        output, errors = process.communicate()
        sys.stdout.buffer.write(redact_output(output, secrets))
        sys.stderr.buffer.write(redact_output(errors, secrets))
        raise CredentialError("Authorized command timed out; no credential values printed") from None
    sys.stdout.buffer.write(redact_output(output, secrets))
    sys.stderr.buffer.write(redact_output(errors, secrets))
    return process.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, help="Private directory outside repositories")
    subcommands = parser.add_subparsers(dest="action", required=True)
    put = subcommands.add_parser("put", help="Provision once; never pass a value in argv")
    put.add_argument("name")
    sources = put.add_mutually_exclusive_group()
    sources.add_argument("--source", type=Path)
    sources.add_argument("--stdin", action="store_true")
    put.add_argument("--replace", action="store_true")
    put.add_argument("--trim-newline", action="store_true")
    subcommands.add_parser("list", help="Print names only, never values")
    check = subcommands.add_parser("check", help="Confirm availability without revealing a value")
    check.add_argument("name")
    execute = subcommands.add_parser("exec", help="Use values in a subprocess, with output redacted")
    execute.add_argument("--map", action="append", required=True)
    execute.add_argument("--timeout", type=float, default=120)
    execute.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.action == "put":
            if args.source:
                value = args.source.read_bytes()
            elif args.stdin:
                value = sys.stdin.buffer.read(MAX_SECRET_BYTES + 1)
            else:
                value = getpass.getpass("Credential (hidden): ").encode()
            if args.trim_newline:
                value = value.removesuffix(b"\n").removesuffix(b"\r")
            write_secret(args.name, value, args.store, args.replace)
            print(f"Stored {args.name}: private 700/600, outside repositories")
        elif args.action == "list":
            print("\n".join(list_names(args.store)))
        elif args.action == "check":
            read_secret(args.name, args.store)
            print(f"Available: {args.name} (value not displayed)")
        else:
            return execute_with_secrets(args.map, args.command, args.store, args.timeout)
        return 0
    except (CredentialError, OSError) as error:
        print(f"Credential action blocked: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
