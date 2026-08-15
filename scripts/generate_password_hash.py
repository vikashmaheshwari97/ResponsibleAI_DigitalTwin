from __future__ import annotations

from getpass import getpass

import bcrypt


def main() -> None:
    password = getpass("Password to hash: ")
    confirm = getpass("Confirm password: ")
    if not password:
        raise SystemExit("Password cannot be empty.")
    if password != confirm:
        raise SystemExit("Passwords do not match.")
    encoded = password.encode("utf-8")
    print(bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8"))


if __name__ == "__main__":
    main()
