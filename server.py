import os
import secrets
import random
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
#from main import find_restaurant_by_id
from webauthn import (
    generate_registration_options,
    generate_authentication_options,
    verify_registration_response,
    verify_authentication_response,
    options_to_json )
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, PublicKeyCredentialType
from webauthn.helpers import parse_registration_credential_json, parse_authentication_credential_json

rest_api = FastAPI()

one_time_codes = {}
class BookingRequest(BaseModel):
    restaurant_id: str

class EmailRequest(BaseModel):
    email: EmailStr

class WebAuthNRequest(BaseModel):
    email: str

class SecurityToken(BaseModel):
    token: str

class VerifyRequest(BaseModel):
    email: EmailStr
    credential: dict

class CodeVerification(BaseModel):
    email: EmailStr
    code: str
    redirect_uri: str
    state: str

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS").lower() == 'true',
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS").lower() == 'true',
)

# Function to generate a random 6-digit code
def generate_code():
    return str(random.randint(100000, 999999))

async def send_code_email(recipient: str, code: str):
    subject = "Your One-Time Verification Code"
    body = f"Your one-time code is: **{code}**"

    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype="html"
    )

    print(f'The email configuration is {conf}')
    fm = FastMail(conf)
    await fm.send_message(message)

OAUTH_URL = "https://tgallant-mcp-server.ngrok.app"
LOGIN_URL= f"{OAUTH_URL}/login"
ORIGIN = OAUTH_URL # The domain name of your site
RP_NAME = "Restaurant Assistant"
RP_ID = "tgallant-mcp-server.ngrok.app"

users_db = {}
pending_registrations = {}
pending_authentication_challenges = {}
temp_token_store = {}

rest_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allow all origins
    allow_credentials=True,        # Allow cookies, authorization headers, etc.
    allow_methods=["*"],           # Allow all standard HTTP methods (GET, POST, etc.)
    allow_headers=["*"],           # Allow all headers
)

STATIC_CLIENT_DIR = "./client/dist"
rest_api.mount("/login", StaticFiles(directory=STATIC_CLIENT_DIR, html=True), name="login")


@rest_api.get("/oauth2/authorize")
async def authorize(
        request: Request,
        client_id: str,
        redirect_uri: str,
        state: str,
        response_type: str = "code",
    ):
        """Redirects to login page when the user visits /oauth2/authorize."""
        CLIENT_LOGIN_URL = f"{LOGIN_URL}?redirect={redirect_uri}&state={state}"
        return RedirectResponse(url=CLIENT_LOGIN_URL, status_code=302)

@rest_api.get("/health")
async def health():
    return {"status": "ok"}

@rest_api.get("/.well-known/openid-configuration")
async def openid_configuration():
    config = {
        "issuer": f"{OAUTH_URL}",
        "authorization_endpoint": f"{OAUTH_URL}/oauth2/authorize",
        "token_endpoint": f"{OAUTH_URL}/oauth2/token",
        "registration_endpoint": f"{OAUTH_URL}/oauth2/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["token"],
        "claims_supported": ["sub", "api_token"]
    }
    return config

@rest_api.get("/.well-known/oauth-authorization-server")
async def openid_auth_configuration():
    config = {
        "issuer": f"{OAUTH_URL}",
        "authorization_endpoint": f"{OAUTH_URL}/oauth2/authorize",
        "token_endpoint": f"{OAUTH_URL}/oauth2/token",
        "registration_endpoint": f"{OAUTH_URL}/oauth2/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["token"],
        "claims_supported": ["sub", "api_token"]
    }
    return config

@rest_api.post("/oauth2/register")
async def oauth_register():
    """
     Handles the dynamic client registration request from ChatGPT.
     We can just return a static response.
    """
    # In a real app, you might inspect request.json['redirect_uris']
    # but for this purpose, a static response is fine.

    response = {
        "client_id": "chatgpt-test-connector-client",
        "redirect_uris": [
            "https://chatgpt.com/connector_platform_oauth_redirect"
        ],
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "application_type": "web"
    }
    return response

@rest_api.post("/register/authn")
async def register_webauthn(request: WebAuthNRequest):
    print(f'The request login user is {request}')
    username = request.email.lower()
    if not username:
        raise HTTPException(status_code=400, detail="No user name was sent")

    user_id = uuid.uuid4().bytes
    random_bytes = secrets.token_bytes(16)
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user_id,
        user_name=username,
        challenge=random_bytes # Generate a unique, random challenge per session
    )

    pending_registrations[username] = options.challenge
    return options_to_json(options)

@rest_api.post("/register/verify")
async def register_complete(credential_response: dict):
    username = credential_response['email'].lower()
    challenge = None

    if username in pending_registrations:
        challenge = pending_registrations.pop(username)

    if challenge is None:
        raise HTTPException(
            status_code=400,
            detail="No active session. Please start the flow again."
        )

    parsed_credential = parse_registration_credential_json(
        credential_response
    )

    print(f'The parsed credential is {parsed_credential}')
    try:
        verification = verify_registration_response(
            credential=parsed_credential,
            expected_challenge=challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
        )

        if username not in users_db:
            users_db[username] = {"credentials": []}
        users_db[username]["credentials"].append(verification)

    except Exception as e:
        print(f'Got an exception: {e}')
        raise HTTPException(status_code=400, detail=f"Invalid credential format: {e}")

    finally:
        redirect_uri = credential_response["redirect_uri"]
        state = credential_response["state"]
        chatgpt_url = f"{redirect_uri}?code={generate_code()}&state={state}"
        return {"status": "success", "redirect_uri": chatgpt_url}

@rest_api.post("/authenticate/verify")
async def authenticate_complete(credential_response: dict):
    username = credential_response["email"].lower()
    cred_type = credential_response.get("type")
    if cred_type != "public-key":
        print(f'Cred type is {cred_type}')
        raise HTTPException(
            status_code=400,
            detail=f"Expected public-key credential for authentication, got '{cred_type}'. "
                   "Are you accidentally sending registration data to the login endpoint?"
        )

    challenge = pending_authentication_challenges.pop(username, None)
    if not challenge:
        raise HTTPException(status_code=400, detail="No pending authentication")

    parsed = parse_authentication_credential_json(credential_response)

    # Get the user's stored credentials
    user_creds = users_db.get(username, {}).get("credentials", [])
    if not user_creds:
        raise HTTPException(status_code=400, detail="User not found")

    # Find the matching credential (by credential_id)
    credential_id = parsed.raw_id  # this is bytes
    stored_cred = next((c for c in user_creds if c.credential_id == credential_id), None)
    if not stored_cred:
        raise HTTPException(status_code=400, detail="Unknown credential")

    verification = verify_authentication_response(
        credential=parsed,
        expected_challenge=challenge,
        expected_origin=ORIGIN,
        expected_rp_id=RP_ID,
        credential_public_key=stored_cred.credential_public_key,
        credential_current_sign_count=stored_cred.sign_count,
        require_user_verification=False,
    )

    # Update sign count to prevent replay attacks
    stored_cred.sign_count = verification.new_sign_count
    redirect_uri = credential_response["redirect_uri"]
    state = credential_response["state"]
    chatgpt_url = f"{redirect_uri}?code={generate_code()}&state={state}"
    return {"status": "success", "redirect_uri": chatgpt_url}

@rest_api.post("/request-code")
async def request_one_time_code(request: EmailRequest, background_tasks: BackgroundTasks):
    print(f'The request data is {request}')
    email = str(request.email).strip().lower()
    user_data = users_db.get(email)
    print(f"user_data type: {type(user_data)}")
    print(f"user_data: {user_data}")
    if user_data and user_data.get('credentials'):
        # Scenario: User exists and has credentials -> Initiate Authentication ---
        print(f"User {email} exists, initiating authentication challenge.")

        allowed_credentials_list = [
            PublicKeyCredentialDescriptor(
                id=cred.credential_id,
                type=PublicKeyCredentialType.PUBLIC_KEY,
            )
            for cred in user_data['credentials']
        ]

        options = generate_authentication_options(
            rp_id=RP_ID,
            allow_credentials=allowed_credentials_list,
        )

        pending_authentication_challenges[email] = options.challenge
        if email in pending_registrations: del pending_registrations[email]
        return options_to_json(options)

    else:
        code = generate_code()
        print(f'The newly generated code is {code}')
        one_time_codes[email] = code # Store the code temporarily

    # Send the email in a background task to avoid blocking the API response
    background_tasks.add_task(send_code_email, email, code)

    return {"message": f"One-time code requested for {email}. Check your inbox."}

@rest_api.post("/verify-code")
async def verify_one_time_code(request: CodeVerification):
    print(f'Verifying otc with following request {request}')
    email = str(request.email).strip().lower()
    code = request.code
    redirect_uri = request.redirect_uri
    state = request.state

    if email in one_time_codes and one_time_codes[email] == code:
        # Code is valid, remove it after use
        del one_time_codes[email]

        temp_token = secrets.token_urlsafe(32)
        chatgpt_url = f"{redirect_uri}?state={state}"
        temp_token_store[temp_token] = chatgpt_url
        return {"status": "success", "token": temp_token}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

@rest_api.post("/auth/redirect")
async def final_login(request: SecurityToken):
    temp_token = request.token

    url = temp_token_store.pop(temp_token, None) # Pop ensures the token is single-use
    redirect = f'{url}&code={generate_code()}'
    print(f'Sending redirect {redirect}')

    if not redirect:
        raise HTTPException(status_code=401, detail="Invalid or expired temporary token.")

    return {"status": "success", "redirect_uri": redirect}

@rest_api.post("/oauth2/token")
async def oauth_token(request: Request):
    form_data = await request.form()
    grant_type = form_data.get("grant_type")
    code = form_data.get("code")
    client_id = form_data.get("client_id")
    code_verifier = form_data.get("code_verifier")
    refresh_token = form_data.get("refresh_token")
    scope = "token"
    if grant_type == "authorization_code":

        # Return the API key as the 'access_token'
        access_token = secrets.token_urlsafe(32)
        new_refresh_token = secrets.token_urlsafe(32)
        token_response = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 600,  # 90 days (or however long you want)
            "refresh_token": new_refresh_token,
            "scope": scope
        }
        print("response :", token_response)

        return token_response
    elif grant_type == "refresh_token":
        new_token = secrets.token_urlsafe(32)
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "refresh_token": refresh_token,  # can rotate or reuse
            "scope": scope,
        }
    else:
        raise HTTPException(400, "unsupported grant_type")

    # ----------------------------------------------------
    # TODO: YOUR CUSTOM LOGIC GOES HERE
    #
    # 1. Validate the 'code' and optionally the 'code_verifier' (PKCE).
    # 2. Find the user_id associated with this validated 'code'.
    # 3. Look up that user's permanent API key from your database.
    #
    # user_api_key = my_db.get_api_key(user_id)
    #
    # ----------------------------------------------------

    # For this example, we'll just hardcode it.
    scope = "token"
    # Return the API key as the 'access_token'
    access_token = secrets.token_urlsafe(32)
    token_response = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 7776000,  # 90 days (or however long you want)
        "scope": scope
    }
    print("response :", token_response)

    return token_response

