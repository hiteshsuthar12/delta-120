import pytest
import hmac
import hashlib
from app.services.delta_exchange import DeltaExchangeClient

def test_delta_signature_format():
    client = DeltaExchangeClient(api_key="TEST_KEY", api_secret="TEST_SECRET")
    sig, ts = client._generate_signature("GET", "/v2/wallet/balances", "")

    # Reconstruct expected HMAC
    expected_msg = f"GET{ts}/v2/wallet/balances"
    expected_sig = hmac.new(b"TEST_SECRET", expected_msg.encode("utf-8"), hashlib.sha256).hexdigest()

    assert sig == expected_sig

def test_delta_signature_with_payload():
    client = DeltaExchangeClient(api_key="TEST_KEY", api_secret="TEST_SECRET")
    payload = '{"product_id":27,"size":1}'
    sig, ts = client._generate_signature("POST", "/v2/orders", payload)

    expected_msg = f"POST{ts}/v2/orders{payload}"
    expected_sig = hmac.new(b"TEST_SECRET", expected_msg.encode("utf-8"), hashlib.sha256).hexdigest()

    assert sig == expected_sig

@pytest.mark.asyncio
async def test_auth_failure_without_credentials():
    client = DeltaExchangeClient(api_key="", api_secret="")
    with pytest.raises(ValueError) as exc:
        await client._request("GET", "/v2/wallet/balances", auth_required=True)
    assert "credentials not configured" in str(exc.value)

