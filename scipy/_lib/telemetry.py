import os

from typing import Sequence

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from contextlib import wraps

ALLOWED_TYPES = [bool, str, bytes, int, float]

__all__ = ["span"]

provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)

trace.set_tracer_provider(
  TracerProvider(
    resource=Resource.create({SERVICE_NAME: "scipy-service"})
  )
)

jaeger_exporter = JaegerExporter(
  agent_host_name=os.environ.get("JAEGER_HOST", "localhost"),
  agent_port=os.environ.get("JAEGER_PORT", 6831),
)

trace.get_tracer_provider().add_span_processor(
  BatchSpanProcessor(jaeger_exporter)
)


def _get_func_name(func):
    return f"{func.__module__}.{func.__qualname__}"


def _serialize(arg):
    for _type in ALLOWED_TYPES:
        if isinstance(arg, _type):
            return arg
        if isinstance(arg, Sequence) and len(arg) > 0:
            if isinstance(arg[0], _type):
                return arg
    return str(arg)


def span(func):
    # Creates a tracer from the global tracer provider
    tracer = trace.get_tracer(__name__)
    func_name = _get_func_name(func)
    
    @wraps(func)
    def span_wrapper(*args, **kwargs):
        print(args, kwargs)
        import inspect
        stack = inspect.stack()
        print([stack[n][3] for n in range(len(stack))])
        with tracer.start_as_current_span(func_name) as span:
            for n, arg in enumerate(args):
                span.set_attribute(f"args.{n}", _serialize(arg))
            for k, v in kwargs.items():
                span.set_attribute(f"kwargs.{k}", v)
            return func(*args, **kwargs)

    return span_wrapper
