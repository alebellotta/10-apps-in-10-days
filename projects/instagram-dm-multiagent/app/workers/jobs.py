from dataclasses import dataclass


@dataclass(slots=True)
class ProcessingJob:
    event_id: int
