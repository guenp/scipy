import os

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from contextlib import wraps

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

def span(func):
    # Creates a tracer from the global tracer provider
    tracer = trace.get_tracer(__name__)
    
    @wraps(func)
    def inner(*args, **kwargs):
        print(args, kwargs)
        with tracer.start_as_current_span(func.__name__) as span:
            for n, arg in enumerate(args):
                span.set_attribute(f"arg{n}", arg)
            for k, v in kwargs.items():
                span.set_attribute(k, v)
            return func(*args, **kwargs)

    return inner
