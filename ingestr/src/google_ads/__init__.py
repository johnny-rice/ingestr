from typing import Iterator, List, Optional, Callable, Dict
from datetime import datetime

from flatten_json import flatten
import dlt
from dlt.common.exceptions import MissingDependencyException
from dlt.common.typing import TDataItem
from dlt.sources import DltResource
from googleapiclient.discovery import Resource  # type: ignore

from .helpers.data_processing import to_dict

from .predicates import date_predicate

try:
    from google.ads.googleads.client import GoogleAdsClient  # type: ignore
except ImportError:
    raise MissingDependencyException("Requests-OAuthlib", ["google-ads"])

class Report:
    resource: str
    dimensions: List[str]
    metrics: List[str]
    segments: List[str]

    def __init__(
        self,
        resource: str = "",
        dimensions: List[str] = [],
        metrics: List[str] = [],
        segments: List[str] = [],
    ):
        self.resource = resource
        self.dimensions = dimensions
        self.metrics = metrics
        self.segments = segments

    def primary_keys(self) -> List[str]:
        return [
            k.replace(".", "_") for k in self.dimensions + self.segments
        ]

    @classmethod
    def from_spec(cls, spec: str):
        """
        Parse a report specification string into a Report object.
        The expected format is:
        custom:{resource}:{dimensions}:{metrics}

        Example:
        custom:ad_group_ad_asset_view:ad_group.id,campaign.id:clicks,conversions
        """
        if spec.count(":") != 3:
            raise ValueError("Invalid report specification format. Expected custom:{resource}:{dimensions}:{metrics}")

        _, resource, dimensions, metrics = spec.split(":")

        report = cls()
        report.segments = ["segments.date"]
        report.resource = resource
        report.dimensions = [
            d for d in map(cls._parse_dimension, dimensions.split(","))
        ]
        report.metrics = [
            m for m in map(cls._parse_metric, metrics.split(","))
        ]
        return report

    @classmethod
    def _parse_dimension(self, dim: str):
        dim = dim.strip()
        if dim.count(".") == 0:
            raise ValueError("Invalid dimension format. Expected {resource}.{field}")
        if dim.startswith("segments."):
            raise ValueError("Invalid dimension format. Segments are not allowed in dimensions.")
        return dim
    
    @classmethod
    def _parse_metric(self, metric: str):
        metric = metric.strip()
        if not metric.startswith("metrics."):
            metric = f"metrics.{metric.strip()}"
        return metric

BUILTIN_REPORTS: Dict[str, Report] = {
    "account_report_daily": Report(
        resource="campaign",
        dimensions=[
            "customer.id",
        ],
        metrics=[
            "metrics.active_view_impressions",
            "metrics.active_view_measurability",
            "metrics.active_view_measurable_cost_micros",
            "metrics.active_view_measurable_impressions",
            "metrics.active_view_viewability",
            "metrics.clicks",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.cost_micros",
            "metrics.impressions",
            "metrics.interactions",
            "metrics.interaction_event_types",
            "metrics.view_through_conversions",
        ],
        segments=[
            "segments.date",
            "segments.ad_network_type",
            "segments.device",
        ],
    ),
    "campaign_report_daily": Report(
        resource="campaign",
        dimensions=[
            "campaign.id",
            "customer.id",
        ],
        metrics=[
            "metrics.active_view_impressions",
            "metrics.active_view_measurability",
            "metrics.active_view_measurable_cost_micros",
            "metrics.active_view_measurable_impressions",
            "metrics.active_view_viewability",
            "metrics.clicks",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.cost_micros",
            "metrics.impressions",
            "metrics.interactions",
            "metrics.interaction_event_types",
            "metrics.view_through_conversions",
        ],
        segments=[
            "segments.date",
            "segments.ad_network_type",
            "segments.device",
        ],
    ),
    "ad_group_report_daily": Report(
        resource="ad_group",
        dimensions=[
            "ad_group.id",
            "customer.id",
            "campaign.id",
        ],
        metrics=[
            "metrics.active_view_impressions",
            "metrics.active_view_measurability",
            "metrics.active_view_measurable_cost_micros",
            "metrics.active_view_measurable_impressions",
            "metrics.active_view_viewability",
            "metrics.clicks",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.cost_micros",
            "metrics.impressions",
            "metrics.interactions",
            "metrics.interaction_event_types",
            "metrics.view_through_conversions",
        ],
        segments=[
            "segments.date",
            "segments.ad_network_type",
            "segments.device",
        ],
    ),
    "ad_report_daily": Report(
        resource="ad_group_ad",
        dimensions=[
            "ad_group.id",
            "ad_group_ad.ad.id",
            "customer.id",
            "campaign.id",
        ],
        segments=[
            "segments.date",
            "segments.ad_network_type",
            "segments.device",
        ],
        metrics=[
            "metrics.active_view_impressions",
            "metrics.active_view_measurability",
            "metrics.active_view_measurable_cost_micros",
            "metrics.active_view_measurable_impressions",
            "metrics.active_view_viewability",
            "metrics.clicks",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.cost_micros",
            "metrics.impressions",
            "metrics.interactions",
            "metrics.interaction_event_types",
            "metrics.view_through_conversions",
        ]
    ),
    "audience_report_daily": Report(
        resource="ad_group_audience_view",
        dimensions=[
            "ad_group.id",
            "customer.id",
            "campaign.id",
            "ad_group_criterion.criterion_id"
        ],
        segments=[
            "segments.date",
            "segments.ad_network_type",
            "segments.device",
        ],
        metrics=[
            "metrics.active_view_impressions",
            "metrics.active_view_measurability",
            "metrics.active_view_measurable_cost_micros",
            "metrics.active_view_measurable_impressions",
            "metrics.active_view_viewability",
            "metrics.clicks",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.cost_micros",
            "metrics.impressions",
            "metrics.interactions",
            "metrics.interaction_event_types",
            "metrics.view_through_conversions"
        ]
    ),
    "keyword_report_daily": Report(
        resource="ad_group_audience_view",
        dimensions=[
            "ad_group.id",
            "customer.id",
            "campaign.id",
            "ad_group_criterion.criterion_id"
        ],
        segments=[
            "segments.date",
            "segments.ad_network_type",
            "segments.device",
        ],
        metrics=[
            "metrics.active_view_impressions",
            "metrics.active_view_measurability",
            "metrics.active_view_measurable_cost_micros",
            "metrics.active_view_measurable_impressions",
            "metrics.active_view_viewability",
            "metrics.clicks",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.cost_micros",
            "metrics.impressions",
            "metrics.interactions",
            "metrics.interaction_event_types",
            "metrics.view_through_conversions"
        ]
    ),
    "click_report_daily": Report(
        resource="click_view",
        dimensions=[
            "click_view.gclid",
            "customer.id",
            "ad_group.id",
            "campaign.id"
        ],
        metrics=[
            "metrics.clicks",
        ]
    ),
    "landing_page_report_daily": Report(
        resource="landing_page_view",
        dimensions=[
            "landing_page_view.expanded_final_url",
            "landing_page_view.resource_name",
            "customer.id",
            "ad_group.id",
            "campaign.id"
        ],
        metrics=[
            "metrics.average_cpc",
            "metrics.clicks",
            "metrics.cost_micros",
            "metrics.ctr",
            "metrics.impressions",
            "metrics.mobile_friendly_clicks_percentage",
            "metrics.speed_score",
            "metrics.valid_accelerated_mobile_pages_clicks_percentage"
        ],
    ),
    "search_keyword_report_daily": Report(
        resource="keyword_view",
        dimensions=[
            "customer.id",
            "ad_group.id",
            "campaign.id",
            "keyword_view.resource_name",
            "ad_group_criterion.criterion_id"
        ],
        metrics=[
            "metrics.absolute_top_impression_percentage",
            "metrics.average_cpc",
            "metrics.average_cpm",
            "metrics.clicks",
            "metrics.conversions_from_interactions_rate",
            "metrics.conversions_value",
            "metrics.cost_micros",
            "metrics.ctr",
            "metrics.impressions",
            "metrics.top_impression_percentage",
            "metrics.view_through_conversions"
        ],
    ),
    "search_term_report_daily": Report(
        resource="search_term_view",
        dimensions=[
            "customer.id",
            "ad_group.id",
            "campaign.id",
            "search_term_view.resource_name",
            "search_term_view.search_term",
            "search_term_view.status"
        ],
        segments=[
            "segments.search_term_match_type",
        ],
        metrics=[
            "metrics.absolute_top_impression_percentage",
            "metrics.average_cpc",
            "metrics.clicks",
            "metrics.conversions",
            "metrics.conversions_from_interactions_rate",
            "metrics.conversions_from_interactions_value_per_interaction",
            "metrics.cost_micros",
            "metrics.ctr",
            "metrics.impressions",
            "metrics.top_impression_percentage",
            "metrics.view_through_conversions"
        ],
    ),
    "lead_form_submission_data_report_daily": Report(
        resource="lead_form_submission_data",
        dimensions=[
            "lead_form_submission_data.gclid",
            "lead_form_submission_data.submission_date_time",
            "lead_form_submission_data.lead_form_submission_fields",
            "lead_form_submission_data.custom_lead_form_submission_fields",
            "lead_form_submission_data.resource_name",
            "customer.id",
            "ad_group_ad.ad.id",
            "ad_group.id",
            "campaign.id"
        ],
    ),
    "local_services_lead_report_daily": Report(
        resource="local_services_lead",
        dimensions=[
            "customer.id",
            "local_services_lead.creation_date_time",
            "local_services_lead.contact_details",
            "local_services_lead.credit_details.credit_state",
            "local_services_lead.credit_details.credit_state_last_update_date_time",
            "local_services_lead.lead_charged",
            "local_services_lead.lead_status",
            "local_services_lead.lead_type",
            "local_services_lead.locale",
            "local_services_lead.note.description",
            "local_services_lead.note.edit_date_time",
            "local_services_lead.service_id"
        ],
    ),
    "local_services_lead_conversations_report_daily": Report(
        resource="local_services_lead_conversation",
        dimensions=[
            "customer.id",
            "local_services_lead_conversation.event_date_time",
            "local_services_lead_conversation.conversation_channel",
            "local_services_lead_conversation.local_services_lead_id",
            "local_services_lead_conversation.message_details_attachment_urls",
            "local_services_lead_conversation.message_details_text",
            "local_services_lead_conversation.participant_type",
            "local_services_lead_conversation.phone_call_details_call_duration_millis",
            "local_services_lead_conversation.phone_call_details_call_recording_url"
        ],
    ),
}
    
@dlt.source
def google_ads(
    client: GoogleAdsClient,
    customer_id: str,
    date: dlt.sources.incremental[datetime],
    report_spec: Optional[str] = None,
) -> Iterator[DltResource]:

    if report_spec is not None:
        custom_report = Report().from_spec(report_spec)
        yield dlt.resource(
            daily_report,
            name="daily_report",
            write_disposition="merge",
            primary_key=custom_report.primary_keys(),
        )(client, customer_id, report, date)

    for report_name, report in BUILTIN_REPORTS.items():
        yield dlt.resource(
            daily_report,
            name=report_name,
            write_disposition="merge",
            primary_key=report.primary_keys(),
        )(client, customer_id, report, date)

def daily_report(
    client: Resource,
    customer_id: str,
    report: Report,
    date: dlt.sources.incremental[datetime],
) -> Iterator[TDataItem]:
    ga_service = client.get_service("GoogleAdsService")
    fields = report.dimensions + report.metrics + report.segments
    query = f"""
        SELECT
            {", ".join(fields)}
        FROM
            {report.resource}
        WHERE
            {date_predicate("segments.date", date.last_value, date.end_value)}
    """
    allowed_keys = set([
        k.replace(".", "_") 
        for k in fields
    ])
    stream = ga_service.search_stream(customer_id=customer_id, query=query)
    for batch in stream:
        for row in batch.results:
            data = flatten(to_dict(row))
            if "segments_date" in data:
                data["segments_date"] = datetime.strptime(data["segments_date"], "%Y-%m-%d")
            yield {
                k:v for k,v in data.items() if k in allowed_keys
            }