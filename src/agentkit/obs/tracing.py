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
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes

DEFAULT_ENDPOINT = "http://localhost:4317"

_configured = False


def build_provider(
    service_name: str,
    *,
    endpoint: str | None = None,
    service_version: str | None = None,
    span_processor: SpanProcessor | None = None,
) -> TracerProvider:
    """Construct a TracerProvider. Does not install it globally.

    Callers that want isolation — tests, embedded use — hold the provider
    and call provider.get_tracer() directly.
    """
    resolved = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", DEFAULT_ENDPOINT)

    attributes = {ResourceAttributes.SERVICE_NAME: service_name}
    if service_version:
        attributes[ResourceAttributes.SERVICE_VERSION] = service_version

    provider = TracerProvider(resource=Resource.create(attributes))
    provider.add_span_processor(
        span_processor
        or BatchSpanProcessor(OTLPSpanExporter(endpoint=resolved, insecure=True))
    )
    return provider


def configure_tracing(
    service_name: str,
    *,
    endpoint: str | None = None,
    service_version: str | None = None,
    span_processor: SpanProcessor | None = None,
) -> TracerProvider:
    """Build a provider and install it as the process-wide default.

    Idempotent: repeated calls return the existing provider rather than
    stacking span processors, which would duplicate every span.
    """
    global _configured

    if _configured:
        return trace.get_tracer_provider()  # type: ignore[return-value]

    provider = build_provider(
        service_name,
        endpoint=endpoint,
        service_version=service_version,
        span_processor=span_processor,
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


