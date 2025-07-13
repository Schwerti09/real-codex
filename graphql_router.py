# -*- coding: utf-8 -*-
"""GraphQL router exposing async subscription endpoints."""

from __future__ import annotations

from fastapi import APIRouter

try:
    import graphene
    from starlette.graphql import GraphQLApp
except Exception:  # pragma: no cover - optional dependency
    graphene = None  # type: ignore
    GraphQLApp = None  # type: ignore

router = APIRouter()


if graphene is not None:

    class Query(graphene.ObjectType):
        hello = graphene.String(default_value="world")

    schema = graphene.Schema(query=Query)
    router.add_route("/graphql", GraphQLApp(schema=schema))
