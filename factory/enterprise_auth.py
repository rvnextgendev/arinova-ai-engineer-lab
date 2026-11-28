"""OIDC bearer verification and loopback-only Basic login for the local pilot."""
import os,json,base64,hashlib,hmac,secrets,logging
from contextvars import ContextVar
from fastapi import HTTPException
from fastapi.responses import JSONResponse
principal=ContextVar("principal",default=None)
log=logging.getLogger("arinova.audit")
ROLES={"admin","developer","quality","approver","release","viewer"}
def password_hash(password,salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+":"+hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
def authenticate(header):
    mode=os.getenv("ARINOVA_AUTH_MODE","local")
    if mode=="local" and header.startswith("Basic "):
        user,pw=base64.b64decode(header[6:],validate=True).decode().split(":",1)
        record=json.loads(os.environ["ARINOVA_LOCAL_USERS"])[user]
        stored=record["password_hash"]
        if not hmac.compare_digest(stored,password_hash(pw,stored.split(":")[0])):raise ValueError("Invalid credentials")
        return {"sub":user,"roles":record["roles"],"projects":record.get("projects",[])}
    if mode=="oidc" and header.startswith("Bearer "):
        import jwt
        issuer=os.environ["ARINOVA_OIDC_ISSUER"]
        client=jwt.PyJWKClient(os.environ["ARINOVA_OIDC_JWKS_URL"],timeout=5)
        token=header[7:]
        key=client.get_signing_key_from_jwt(token).key
        claims=jwt.decode(token,key,algorithms=["RS256"],issuer=issuer,audience=os.environ["ARINOVA_OIDC_AUDIENCE"],options={"require":["exp","iat","sub","iss","aud"]})
        return {"sub":claims["sub"],"roles":claims.get("roles",[]),"projects":claims.get("projects",[])}
    raise ValueError("Authentication required")
def actor():
    p=principal.get()
    if not p:raise HTTPException(401,"Authentication required")
    return p
def allowed(p,id=None,roles=()):
    if not isinstance(p["roles"],list) or not isinstance(p["projects"],list):return False
    if "admin" in p["roles"]:return True
    return (id is None or id in p["projects"]) and bool(set(p["roles"]) & set(roles))
def require(id=None,roles=()):
    p=actor()
    if not allowed(p,id,roles):
        log.warning("denied subject=%r project=%r",p["sub"],id)
        raise HTTPException(403,"Access denied")
    return p
async def middleware(request,call_next):
    try:p=authenticate(request.headers.get("authorization",""))
    except Exception:
        return JSONResponse({"detail":"Authentication required"},401,headers={"WWW-Authenticate":"Basic realm=Arinova" if os.getenv("ARINOVA_AUTH_MODE","local")=="local" else "Bearer"})
    token=principal.set(p)
    try:
        path=request.url.path
        # Legacy APIs and labs are admin-only, preventing alternate-route bypass.
        if not path.startswith("/factory") and not allowed(p,roles=("admin",)):
            return JSONResponse({"detail":"Access denied"},403)
        response=await call_next(request)
        log.info("subject=%r method=%s path=%r status=%s",p["sub"],request.method,path,response.status_code)
        return response
    finally:principal.reset(token)
if __name__=="__main__":
    import getpass
    print(password_hash(getpass.getpass("Password: ")))
