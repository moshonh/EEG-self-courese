"""Run locally; paste the printed TOML into Streamlit Secrets."""
import hashlib
import secrets
code=secrets.token_urlsafe(12)
print('Entry code (send privately to residents):',code)
print('\nPaste into Streamlit Secrets:\n')
print('[access]')
print('code_hashes = ["'+hashlib.sha256(code.encode()).hexdigest()+'"]')
