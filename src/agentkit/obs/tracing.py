"""OpenTelemetry tracing bootstrap.

The exporter endpoint is read from OTEL_EXPORTER_OTLP_ENDPOINT so the
same code runs against a local collector or an AWS-hosted one without
modification. Backend choice is a deployment concern, not a code concern."""

from __future__ import annotations
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes

DEFAULT_ENDPOINT = "http://localhost:4317"

_configured = False

def configure_tracing(service_name: str, *, endpoint: str | None = None, service_version: str |None = None) -> TracerProvider:
    """Install a global TracerProvider exporting OTLP over gRPC.

    Idempotent: repeated calls return the existing provider rather than
    stacking span processors, which would duplicate every span."""
    global _configured

    if _configured:
        return trace.get_trace_provider()

    resolved = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", DEFAULT_ENDPOINT)

    attributes = {ResourceAttributes.SERVICE_NAME: service_name}

    if service_version:
        attributes[ResourceAttributes.SERVICE_NAME] = service_version

    provider = TracerProvider(resource=Resource.create(attributes))
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=resolved, insecure=True))
    )

    trace.set_tracer_provider(provider)
    _configured = True
    return provider

def get_tracer(name: str) -> trace.Tracer:
    """Return a tracer. Safe before configure_tracing; spans are no-ops until then."""
    return trace.get_tracer(name)

def shutdown_tracing(timeout_millis: int = 5000) -> None:
    """ Flush pending spans and shut down the provider.

    BatchSpanProcessor exports on a background thread. Without this, a
    short-lived process exits with spans still queued and silently loses them."""

    global _configured

    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.force_flush(timeout_millis)
        provider.shutdown()

    _configured = False


