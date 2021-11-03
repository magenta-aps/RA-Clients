# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from graphql import Source
from graphql import SourceLocation

from raclients.graph.util import graphql_error_from_dict


def test_graphql_error_from_dict():
    query = """
        query Query {
          a {
            b {
              c
            }
          }
        }
    """
    error = {
        "message": "Cannot query field 'a' on type 'Query'.",
        "locations": [{"line": 2, "column": 3}],
        "path": None,
    }
    graphql_error = graphql_error_from_dict(error, query)
    assert graphql_error.message == "Cannot query field 'a' on type 'Query'."
    assert graphql_error.source == Source(body=query)
    assert graphql_error.locations == [SourceLocation(line=2, column=3)]
