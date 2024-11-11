import pytest

from lm_api.security import IdentityPayload


def test_identity_payload__extracts_organization_id_successfully():
    token_payload = {
        "exp": 1689105153,
        "sub": "dummy-sub",
        "azp": "dummy-client-id",
        "organization": {
            "dummy-organization-id": {
                "name": "Dummy Organization",
                "attributes": {"logo": [""], "created_at": ["1689105153.0"]},
            }
        },
    }
    identity = IdentityPayload(**token_payload)
    assert identity.organization_id == "dummy-organization-id"


def test_identity_payload__fails_validation_with_wrong_number_of_organization_values():
    token_payload = {
        "exp": 1689105153,
        "sub": "dummy-sub",
        "azp": "dummy-client-id",
        "organization": {
            "dummy-organization-id": {
                "name": "Dummy Organization",
                "attributes": {"logo": [""], "created_at": ["1689105153.0"]},
            },
            "stupid-organization-id": {
                "name": "Stupid Organization",
                "attributes": {"logo": [""], "created_at": ["1689105153.0"]},
            },
        },
    }
    with pytest.raises(ValueError, match="Organization payload did not include exactly one value"):
        IdentityPayload(**token_payload)

    token_payload = {
        "exp": 1689105153,
        "sub": "dummy-sub",
        "azp": "dummy-client-id",
        "organization": {},
    }
    with pytest.raises(ValueError, match="Organization payload did not include exactly one value"):
        IdentityPayload(**token_payload)


def test_identity_payload__null_organization_id_with_no_organization_claim():
    token_payload = {
        "exp": 1689105153,
        "sub": "dummy-sub",
        "azp": "dummy-client-id",
    }
    identity = IdentityPayload(**token_payload)
    assert identity.organization_id is None
