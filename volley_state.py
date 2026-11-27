import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import base64

def cipher(secret,salt):
    if not secret:
        raise ValueError("Missing encryption secret")
    key=Scrypt(salt=salt,length=32,n=2**14,r=8,p=1).derive(secret.encode())
    return Fernet(base64.urlsafe_b64encode(key))

def load(path,secret,initialize=False):
    path=Path(path)
    if not path.exists():
        if initialize:
            return {}
        raise RuntimeError("Encrypted state missing; refusing to reset")
    raw=path.read_bytes()
    if len(raw)<17:
        raise ValueError("Invalid encrypted state")
    state=json.loads(cipher(secret,raw[:16]).decrypt(raw[16:]))
    if not isinstance(state,dict):
        raise ValueError("Invalid state structure")
    return state

def save(path,secret,state):
    path=Path(path)
    salt=os.urandom(16)
    raw=salt+cipher(secret,salt).encrypt(json.dumps(state,allow_nan=False).encode())
    tmp=path.with_suffix(".tmp")
    with os.fdopen(os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),"wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp,path)
