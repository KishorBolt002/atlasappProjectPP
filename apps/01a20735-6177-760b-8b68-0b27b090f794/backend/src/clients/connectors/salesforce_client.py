"""
Salesforce authentication setup for simple-salesforce.
Provides a simple function to get an authenticated Salesforce client.
"""

import os

try:
    from simple_salesforce import Salesforce
except ImportError:
    raise ImportError(
        "simple-salesforce is required. Install with: pip install simple-salesforce"
    )


def get_salesforce_client() -> Salesforce:
    """
    Create and return an authenticated Salesforce client using simple-salesforce.
    Uses Client Credentials OAuth flow with credentials from environment/secrets.

    Returns:
        Salesforce: Authenticated simple-salesforce client

    Raises:
        RuntimeError: If required environment variables or secrets are missing

    Example:
        >>> from src.clients.connectors.salesforce_client import get_salesforce_client
        >>> sf = get_salesforce_client()
        >>> accounts = sf.query("SELECT Id, Name FROM Account LIMIT 5")
        >>> print(accounts['records'])
    """
    # Get credentials from environment
    client_id = os.environ.get("CONNECTORS_SALESFORCE_CLIENT_ID")
    domain = os.environ.get("CONNECTORS_SALESFORCE_DOMAIN")

    if not client_id:
        raise RuntimeError(
            "CONNECTORS_SALESFORCE_CLIENT_ID environment variable is required"
        )
    if not domain:
        raise RuntimeError(
            "CONNECTORS_SALESFORCE_DOMAIN environment variable is required"
        )

    # Read client secret from file
    # The secret will always be mounted in this exact path in all environments
    secret_path = "/workspace/secrets/salesforce/client-secret"

    if not os.path.exists(secret_path):
        raise RuntimeError(f"Salesforce client secret not found at: {secret_path}")

    with open(secret_path, "r") as f:
        client_secret = f.read().strip()

    if not client_secret:
        raise RuntimeError(f"Salesforce client secret file is empty: {secret_path}")

    # Prepare domain for simple-salesforce
    # simple-salesforce ALWAYS appends ".salesforce.com" to the domain parameter
    # Our domains are normalized to always end with ".salesforce.com"
    # Example: "orgfarm-df125980f9-dev-ed.develop.my.salesforce.com"
    #       -> "orgfarm-df125980f9-dev-ed.develop.my"
    # Then simple-salesforce adds ".salesforce.com" back to get the correct URL
    instance = domain[:-15]  # Remove the last 15 characters (".salesforce.com")

    # Create and return authenticated simple-salesforce client
    # Using Client Credentials OAuth flow
    return Salesforce(
        username="",  # Not needed for client credentials flow
        password="",  # Not needed for client credentials flow
        consumer_key=client_id,
        consumer_secret=client_secret,
        domain=instance,
    )
