import binascii

import pytest
import responses
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

import auth
from HttpClient import HttpClientSingleton


@pytest.fixture
def rsa_keypair():
    """Generate a real RSA-1024 keypair so we can decrypt what auth.login sends."""
    key = RSA.generate(1024)
    modulus_hex = format(key.n, "x")
    exponent_hex = format(key.e, "x")
    return key, modulus_hex, exponent_hex


@pytest.fixture(autouse=True)
def reset_http_singleton():
    """Isolate each test — drop any shared singleton session."""
    HttpClientSingleton._instance = None
    yield
    HttpClientSingleton._instance = None


@responses.activate
def test_login_flow_encrypts_credentials_and_stores_jsessionid(rsa_keypair):
    key, modulus_hex, exponent_hex = rsa_keypair

    responses.add(responses.GET, "https://www.dhlottery.co.kr/", status=200, body="ok")
    responses.add(
        responses.GET,
        "https://www.dhlottery.co.kr/user.do",
        status=200,
        body="login page",
    )
    responses.add(
        responses.GET,
        "https://www.dhlottery.co.kr/login/selectRsaModulus.do",
        status=200,
        json={"rsaModulus": modulus_hex, "publicExponent": exponent_hex},
    )
    login_post = responses.add(
        responses.POST,
        "https://www.dhlottery.co.kr/login/securityLoginCheck.do",
        status=200,
        body="logged in",
        headers={"Set-Cookie": "JSESSIONID=TEST_SESSION_ID; Path=/"},
    )
    responses.add(
        responses.GET, "https://www.dhlottery.co.kr/main", status=200, body="main"
    )

    ctrl = auth.AuthController()
    ctrl.login("my_id", "my_pw")

    # Verify the POST body contained RSA-encrypted fields that decrypt back to the originals
    assert login_post.call_count == 1
    sent = login_post.calls[0].request.body
    fields = dict(pair.split("=", 1) for pair in sent.split("&"))
    assert fields["inpUserId"] == "my_id"

    cipher = PKCS1_v1_5.new(key)
    sentinel = b"__fail__"
    decrypted_id = cipher.decrypt(binascii.unhexlify(fields["userId"]), sentinel)
    decrypted_pw = cipher.decrypt(
        binascii.unhexlify(fields["userPswdEncn"]), sentinel
    )
    assert decrypted_id == b"my_id"
    assert decrypted_pw == b"my_pw"

    # Session cookie jar should now carry the JSESSIONID the server set
    jar = ctrl.http_client.session.cookies
    assert jar.get("JSESSIONID", domain=".dhlottery.co.kr") == "TEST_SESSION_ID"


@responses.activate
def test_login_retries_on_network_error(rsa_keypair, monkeypatch):
    _, modulus_hex, exponent_hex = rsa_keypair

    # Kill the sleep between retries so the test is fast
    monkeypatch.setattr(auth.time, "sleep", lambda *_args, **_kwargs: None)

    # Warm-up GETs that keep working for both attempts
    responses.add(responses.GET, "https://www.dhlottery.co.kr/", status=200, body="ok")
    responses.add(responses.GET, "https://www.dhlottery.co.kr/", status=200, body="ok")
    responses.add(
        responses.GET,
        "https://www.dhlottery.co.kr/user.do",
        status=200,
        body="login page",
    )
    responses.add(
        responses.GET,
        "https://www.dhlottery.co.kr/user.do",
        status=200,
        body="login page",
    )

    # First RSA fetch fails with 500, second succeeds
    responses.add(
        responses.GET,
        "https://www.dhlottery.co.kr/login/selectRsaModulus.do",
        status=500,
    )
    responses.add(
        responses.GET,
        "https://www.dhlottery.co.kr/login/selectRsaModulus.do",
        status=200,
        json={"rsaModulus": modulus_hex, "publicExponent": exponent_hex},
    )

    responses.add(
        responses.POST,
        "https://www.dhlottery.co.kr/login/securityLoginCheck.do",
        status=200,
        body="logged in",
        headers={"Set-Cookie": "JSESSIONID=RETRY_SESSION; Path=/"},
    )
    responses.add(
        responses.GET, "https://www.dhlottery.co.kr/main", status=200, body="main"
    )

    ctrl = auth.AuthController()
    ctrl.login("u", "p")

    jar = ctrl.http_client.session.cookies
    assert jar.get("JSESSIONID", domain=".dhlottery.co.kr") == "RETRY_SESSION"
