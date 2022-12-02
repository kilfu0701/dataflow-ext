from typing import Any, Dict, List, Callable
from concurrent import futures

from google.cloud import pubsub_v1
#from google.cloud import storage
import apache_beam as beam
#from apache_beam.options.pipeline_options import PipelineOptions
#from google.cloud import bigquery
#from apache_beam.options.pipeline_options import GoogleCloudOptions
#from apache_beam.options.pipeline_options import StandardOptions
#from apache_beam.options.pipeline_options import WorkerOptions
#from apache_beam.io.gcp.pubsub import WriteStringsToPubSub
#import apache_beam.transforms.window as window


"""
@param:
    project_id: (str)
    topic_id:   (str)

@usage:
    from dataflow_ext.pub_sub import PubSubHandler

    PROJECT_ID = 'PID-12345'
    TOPIC_ID = 'topic1'
    handler = PubSubHandler(PROJECT_ID, TOPIC_ID)

    json_str = json.dumps({"fn": "filename1.txt"})

    publish_future = handler.publisher.publish(handler.topic_path, json_str.encode("utf-8"))
    publish_future.add_done_callback(PubSubHandler.get_callback(publish_future, json_str))
    handler.publish_futures.append(publish_future)

    futures.wait(handler.publish_futures, return_when=futures.ALL_COMPLETED)
"""
class PubSubHandler(object):
    def __init__(self, project_id, topic_id, timeout=5):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_id)
        self.publish_futures = []

    @staticmethod
    def get_callback(
        publish_future: pubsub_v1.publisher.futures.Future,
        data: str
    ) -> Callable[[pubsub_v1.publisher.futures.Future], None]:
        def callback(publish_future: pubsub_v1.publisher.futures.Future) -> None:
            try:
                # Wait N seconds for the publish call to succeed.
                print(publish_future.result(timeout=5))
            except futures.TimeoutError:
                print(f"Publishing {data} timed out.")

        return callback


"""
@usage:
    PROJECT_ID = 'PID-12345'
    TOPIC_ID = 'topic1'

    with beam.Pipeline(options=options) as pipeline:
        msg = (
            pipeline
            | 'Create sample data' >> beam.Create([1, 2, 3])
            | 'JSON format' >> beam.Map(json.dumps)
            | 'Send Message To Pub' >> beam.ParDo(SendMessageToPub(), PROJECT_ID, TOPIC_ID)
        )
"""
class SendMessageToPub(beam.DoFn):
    def process(self, element, porject_id, topic_id):
        handler = PubSubHandler(porject_id, topic_id)

        publish_future = handler.publisher.publish(handler.topic_path, element.encode("utf-8"))
        publish_future.add_done_callback(PubSubHandler.get_callback(publish_future, element))
        handler.publish_futures.append(publish_future)

        futures.wait(handler.publish_futures, return_when=futures.ALL_COMPLETED)

        return [element]
