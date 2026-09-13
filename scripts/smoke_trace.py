"""Emit one gen_ai-attributed span through the local collector."""

import time

from agentkit.obs import configure_tracing, get_tracer, shutdown_tracing

configure_tracing("agentkit_python_smoke", service_version="0.1.0")
tracer = get_tracer(__name__)

with tracer.start_as_current_span("chat.completion") as span:
    span.set_attribute("gen_ai.system", "smoke")
    span.set_attribute("gen_ai.request.model", "smoke-model")
    span.set_attribute("get_ai.usage.input_tokens", 42)
    time.sleep(0.1)

shutdown_tracing()

