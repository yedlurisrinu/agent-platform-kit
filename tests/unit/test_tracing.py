"""The tracing contract: spans carry service identity and gen_ai attributes."""

import pytest

from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace import Tracer
from agentkit.obs import configure_tracing, get_tracer, shutdown_tracing

@pytest.fixture
def traced() -> tuple[InMemorySpanExporter, Tracer]:
    exporter = InMemorySpanExporter()
    provider = configure_tracing("test-service", service_version="0.0.0", span_processor=SimpleSpanProcessor(exporter),)
    yield exporter, provider.get_tracer("test")
    shutdown_tracing()

def test_span_is_exported(traced) -> None:
    exporter, tracer = traced #get_tracer(__name__)
    with tracer.start_as_current_span("unit-span"):
        pass

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "unit-span"

def test_gen_ai_attributes_survive_export(traced) -> None:
    exporter,tracer = traced #get_tracer(__name__)
    with tracer.start_as_current_span("chat.completion") as span:
        span.set_attribute("gen_ai.system", "test")
        span.set_attribute("gen_ai.request.model", "test-model")


    attrs = exporter.get_finished_spans()[0].attributes
    assert attrs["gen_ai.system"] == "test"
    assert attrs["gen_ai.request.model"] == "test-model"

def test_resource_carries_service_name(traced) -> None:
    exporter,tracer = traced
    with tracer.start_as_current_span("any"):
        pass

    resource = exporter.get_finished_spans()[0].resource
    assert resource.attributes["service.name"] == "test-service"

def test_child_span_links_to_parent(traced) -> None:
    exporter, tracer = traced
    with tracer.start_as_current_span("parent"):
        with tracer.start_as_current_span("child"):
            pass

    by_name = {s.name: s for s in exporter.get_finished_spans()}
    assert by_name["child"].parent.span_id == by_name["parent"].context.span_id
    assert by_name["child"].context.trace_id == by_name["parent"].context.trace_id