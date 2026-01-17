OC_BASEURL = "https://opencollective.com"
OC_STAGING_BASEURL = "https://staging.opencollective.com"

OC_GRAPHQL_BASEURL = "https://api.opencollective.com/graphql/v2"
OC_GRAPHQL_STAGING_BASEURL = "https://staging.opencollective.com/graphql/v2"

OC_LEGACY_API_BASEURL = "https://api.opencollective.com/v1"
OC_LEGACY_API_STAGING_BASEURL = "https://staging.opencollective.com/api/v1"

CONFIRMED_ORDER_STATUSES = {"PAID", "ACTIVE"}
PENDING_ORDER_STATUSES = {
    "PROCESSING",
    "PENDING",
    "REQUIRE_CLIENT_CONFIRMATION",
    "IN_REVIEW",
}

ORDER_QUERY = """
query ($order: OrderReferenceInput!) {
  order(order: $order) {
    id
    legacyId
    status
    frequency
    totalAmount {
      value
      currency
    }
    amount {
      value
      currency
    }
    toAccount {
      slug
    }
    fromAccount {
      slug
      name
    }
  }
}
"""

TRANSACTION_QUERY = """
query ($transaction: TransactionReferenceInput!) {
  transaction(transaction: $transaction) {
    id
    legacyId
    order {
      id
      legacyId
      status
      frequency
      totalAmount {
        value
        currency
      }
      amount {
        value
        currency
      }
      toAccount {
        slug
      }
      fromAccount {
        slug
        name
      }
    }
  }
}
"""
